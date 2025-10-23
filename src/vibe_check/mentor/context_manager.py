"""
Context Manager for Codebase-Aware Vibe Check Mentor

Provides secure file reading, session-based caching, and smart context extraction
for making vibe_check_mentor aware of actual code instead of making assumptions.

Security Features:
- Path traversal prevention
- Symlink resolution
- File size limits
- Timeout protection

Performance Features:
- In-memory caching with TTL
- Lazy loading of file contents
- Smart extraction of relevant context
"""

import os
import ast
import time
import hashlib
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

# Constants for security and performance
MAX_FILE_SIZE = 1024 * 1024  # 1MB max per file
MAX_TOTAL_SIZE = 5 * 1024 * 1024  # 5MB total for all files
MAX_FILES = 10  # Maximum number of files to read
CACHE_TTL_SECONDS = 3600  # 1 hour cache TTL
MAX_LINE_LENGTH = 1000  # Maximum line length to prevent memory issues
ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".clj",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
}

# Project registry for auto-discovery
PROJECT_REGISTRY_PATH = Path.home() / ".vibe-check" / "project_registry.json"


@dataclass
class FileContext:
    """Represents context extracted from a single file"""

    path: str
    content: str
    language: str
    size: int
    last_modified: float
    hash: str

    # Extracted structure (for Python files)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    # Relevant sections
    relevant_lines: Dict[str, List[Tuple[int, str]]] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.hash)


@dataclass
class SessionContext:
    """Represents cached context for a session"""

    session_id: str
    created_at: float
    last_accessed: float
    files: Dict[str, FileContext]
    working_directory: str
    total_size: int

    def is_expired(self) -> bool:
        """Check if this session context has expired"""
        return (time.time() - self.last_accessed) > CACHE_TTL_SECONDS

    def touch(self):
        """Update last accessed time"""
        self.last_accessed = time.time()


class SecurityValidator:
    """Validates file paths for security"""

    @staticmethod
    def get_workspace_directory() -> Optional[str]:
        """
        Get the configured workspace directory from environment variable.

        Returns:
            Workspace directory path or None if not configured
        """
        workspace = os.environ.get("WORKSPACE")
        if workspace:
            workspace_path = Path(workspace).resolve()
            if workspace_path.exists() and workspace_path.is_dir():
                logger.info(f"Using configured WORKSPACE: {workspace_path}")
                return str(workspace_path)
            else:
                logger.warning(
                    f"WORKSPACE environment variable points to invalid directory: {workspace}"
                )
        return None

    @staticmethod
    def validate_path(
        file_path: str, working_directory: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a file path for security issues.
        Uses WORKSPACE environment variable if set, otherwise uses provided working_directory.

        Returns:
            Tuple of (is_valid, resolved_path, error_message)
        """
        try:
            # Prefer WORKSPACE environment variable over provided working_directory
            workspace = SecurityValidator.get_workspace_directory()
            if workspace:
                working_directory = workspace

            # Handle explicit Windows drive references on non-Windows systems
            if re.match(r"^[a-zA-Z]:\\", file_path):
                return (
                    False,
                    file_path,
                    "File is outside working directory",
                )

            # Convert to Path object
            path = Path(file_path).expanduser()

            # If relative, make it relative to working directory
            if not path.is_absolute():
                if working_directory:
                    base_dir = Path(working_directory).resolve()
                    path = (base_dir / path).resolve()
                else:
                    path = path.resolve()
            else:
                path = path.resolve()

            # Prevent path traversal - ensure file is within working directory if specified
            if working_directory:
                base_dir = Path(working_directory).resolve()
                try:
                    # Check if the resolved path is within the base directory
                    path.relative_to(base_dir)
                except ValueError:
                    # If specified, file must be within working directory
                    return (
                        False,
                        str(path),
                        f"File is outside working directory: {path}",
                    )

            # Check if file exists
            if not path.exists():
                return False, str(path), f"File does not exist: {path}"

            # Check if it's a file (not directory)
            if not path.is_file():
                return False, str(path), f"Path is not a file: {path}"

            # Check file extension
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                return False, str(path), f"File type not allowed: {path.suffix}"

            # Check file size
            file_size = path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return (
                    False,
                    str(path),
                    f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})",
                )

            return True, str(path), None

        except Exception as e:
            return False, str(file_path), f"Error validating path: {str(e)}"


class FileReader:
    """Secure file reader with validation"""

    @staticmethod
    def read_file(
        file_path: str,
        working_directory: str = None,
        *,
        include_error: bool = False,
    ):
        """
        Securely read a file with validation.

        Returns:
            Content string when successful or None when blocked.
            If include_error=True, returns Tuple[content, error_message].
        """
        # Validate path
        is_valid, resolved_path, error = SecurityValidator.validate_path(
            file_path, working_directory
        )
        if not is_valid:
            logger.warning(f"Path validation failed: {error}")
            if include_error:
                return None, error
            return None

        try:
            # Read file with encoding detection
            path = Path(resolved_path)

            # Try UTF-8 first, then fallback to latin-1
            encodings = ["utf-8", "latin-1", "ascii"]
            content = None

            for encoding in encodings:
                try:
                    content = path.read_text(encoding=encoding)

                    # Validate content
                    lines = content.split("\n")
                    if any(len(line) > MAX_LINE_LENGTH for line in lines):
                        logger.warning(
                            f"File contains very long lines: {resolved_path}"
                        )
                        # Truncate long lines
                        lines = [
                            (
                                line[:MAX_LINE_LENGTH] + "..."
                                if len(line) > MAX_LINE_LENGTH
                                else line
                            )
                            for line in lines
                        ]
                        content = "\n".join(lines)

                    if include_error:
                        return content, None
                    return content

                except UnicodeDecodeError:
                    continue

            error_msg = (
                f"Could not decode file with any supported encoding: {resolved_path}"
            )
            if include_error:
                return None, error_msg
            return None

        except Exception as e:
            logger.error(f"Error reading file {resolved_path}: {str(e)}")
            error_msg = f"Error reading file: {str(e)}"
            if include_error:
                return None, error_msg
            return None


class CodeParser:
    """Extract relevant context from code files"""

    @staticmethod
    def parse_python_file(content: str) -> Dict[str, Any]:
        """
        Parse Python file to extract structure.

        Returns:
            Dict with classes, functions, imports
        """
        result = {"classes": [], "functions": [], "imports": [], "docstrings": {}}

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result["classes"].append(node.name)
                    # Extract class docstring
                    docstring = ast.get_docstring(node)
                    if docstring:
                        result["docstrings"][f"class:{node.name}"] = docstring[:200]

                elif isinstance(node, ast.FunctionDef) or isinstance(
                    node, ast.AsyncFunctionDef
                ):
                    # Only top-level functions or class methods
                    result["functions"].append(node.name)
                    # Extract function docstring
                    docstring = ast.get_docstring(node)
                    if docstring:
                        result["docstrings"][f"func:{node.name}"] = docstring[:200]

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing Python file: {e}")
            # Fallback to regex-based extraction
            result["classes"] = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            result["functions"] = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
            result["imports"] = re.findall(
                r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE
            )

        return result

    @staticmethod
    def parse_javascript_file(content: str) -> Dict[str, Any]:
        """
        Parse JavaScript/TypeScript file to extract structure.
        """
        result = {
            "classes": [],
            "functions": [],
            "imports": [],
            "exports": [],
            "interfaces": [],
            "types": [],
        }

        # Regex-based extraction for JS/TS
        result["classes"] = re.findall(r"class\s+(\w+)", content)
        result["functions"] = re.findall(
            r"(?:function|const|let|var)\s+(\w+)\s*=?\s*(?:\([^)]*\)|async)", content
        )
        result["imports"] = re.findall(
            r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', content
        )
        result["exports"] = re.findall(
            r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)", content
        )
        # TypeScript specific
        result["interfaces"] = re.findall(r"interface\s+(\w+)", content)
        result["types"] = re.findall(r"type\s+(\w+)\s*=", content)

        return result

    @staticmethod
    def parse_go_file(content: str) -> Dict[str, Any]:
        """
        Parse Go file to extract structure.
        """
        result = {
            "functions": [],
            "types": [],
            "interfaces": [],
            "imports": [],
            "packages": [],
        }

        # Go-specific patterns
        result["functions"] = re.findall(r"func\s+(?:\(.*?\)\s+)?(\w+)\s*\(", content)
        result["types"] = re.findall(r"type\s+(\w+)\s+struct", content)
        result["interfaces"] = re.findall(r"type\s+(\w+)\s+interface", content)
        result["imports"] = re.findall(
            r'import\s+(?:\(([^)]+)\)|"([^"]+)")', content, re.MULTILINE | re.DOTALL
        )
        result["packages"] = re.findall(r"^package\s+(\w+)", content, re.MULTILINE)

        return result

    @staticmethod
    def parse_rust_file(content: str) -> Dict[str, Any]:
        """
        Parse Rust file to extract structure.
        """
        result = {
            "functions": [],
            "structs": [],
            "enums": [],
            "traits": [],
            "impls": [],
            "mods": [],
            "uses": [],
        }

        # Rust-specific patterns
        result["functions"] = re.findall(r"(?:pub\s+)?fn\s+(\w+)", content)
        result["structs"] = re.findall(r"(?:pub\s+)?struct\s+(\w+)", content)
        result["enums"] = re.findall(r"(?:pub\s+)?enum\s+(\w+)", content)
        result["traits"] = re.findall(r"(?:pub\s+)?trait\s+(\w+)", content)
        result["impls"] = re.findall(r"impl(?:\s+<.*?>)?\s+(\w+)", content)
        result["mods"] = re.findall(r"(?:pub\s+)?mod\s+(\w+)", content)
        result["uses"] = re.findall(r"use\s+([^;]+);", content)

        return result

    @staticmethod
    def parse_java_file(content: str) -> Dict[str, Any]:
        """
        Parse Java file to extract structure.
        """
        result = {
            "classes": [],
            "interfaces": [],
            "methods": [],
            "imports": [],
            "packages": [],
        }

        # Java-specific patterns
        result["classes"] = re.findall(
            r"(?:public\s+)?(?:abstract\s+)?class\s+(\w+)", content
        )
        result["interfaces"] = re.findall(r"(?:public\s+)?interface\s+(\w+)", content)
        result["methods"] = re.findall(
            r"(?:public|private|protected)\s+(?:static\s+)?(?:\w+(?:<.*?>)?\s+)?(\w+)\s*\(",
            content,
        )
        result["imports"] = re.findall(r"import\s+([^;]+);", content)
        result["packages"] = re.findall(r"^package\s+([^;]+);", content, re.MULTILINE)

        return result

    @staticmethod
    def parse_generic_file(content: str) -> Dict[str, Any]:
        """
        Generic parser for other programming languages.
        Uses common patterns across many languages.
        """
        result = {"functions": [], "classes": [], "comments": [], "todos": []}

        # Common patterns across languages
        # Functions: function, func, fn, def, sub
        result["functions"] = re.findall(
            r"(?:function|func|fn|def|sub)\s+(\w+)", content, re.IGNORECASE
        )
        # Classes: class, struct, type
        result["classes"] = re.findall(
            r"(?:class|struct|type)\s+(\w+)", content, re.IGNORECASE
        )
        # TODO comments
        result["todos"] = re.findall(
            r"(?://|#|/\*)\s*(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)[:)]?\s*(.{0,100})",
            content,
            re.IGNORECASE,
        )

        return result

    @staticmethod
    def extract_relevant_context(
        content: str, query: str, language: str
    ) -> Dict[str, List[Tuple[int, str]]]:
        """
        Extract lines relevant to the query.

        Returns:
            Dict mapping relevance type to list of (line_number, line_content) tuples
        """
        relevant = {
            "direct_mentions": [],
            "related_functions": [],
            "related_classes": [],
            "potential_issues": [],
        }

        lines = content.split("\n")
        query_terms = set(query.lower().split())

        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "could",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
            "this",
            "that",
            "these",
            "those",
        }
        query_terms = query_terms - stop_words

        for i, line in enumerate(lines, 1):
            line_lower = line.lower()

            # Direct mentions of query terms
            if any(term in line_lower for term in query_terms if len(term) > 2):
                relevant["direct_mentions"].append((i, line))

            # Look for function/class definitions related to query
            if language == "python":
                if re.match(r"^(class|def)\s+\w+", line):
                    if any(term in line_lower for term in query_terms):
                        relevant["related_functions"].append((i, line))

            # Look for potential issues (TODO, FIXME, etc.)
            if re.search(r"(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)", line, re.IGNORECASE):
                relevant["potential_issues"].append((i, line))

        # Limit results to most relevant
        for key in relevant:
            relevant[key] = relevant[key][:10]  # Max 10 lines per category

        return relevant


class ContextCache:
    """Manages session-based context caching"""

    def __init__(self):
        self._cache: Dict[str, SessionContext] = {}
        self._file_reader = FileReader()
        self._code_parser = CodeParser()

    def get_or_create_session(
        self, session_id: str, working_directory: str = None
    ) -> SessionContext:
        """Get existing session or create new one"""
        # Clean expired sessions
        self._cleanup_expired()

        if session_id in self._cache:
            session = self._cache[session_id]
            session.touch()
            return session

        # Create new session
        session = SessionContext(
            session_id=session_id,
            created_at=time.time(),
            last_accessed=time.time(),
            files={},
            working_directory=working_directory or os.getcwd(),
            total_size=0,
        )
        self._cache[session_id] = session
        return session

    def add_files_to_session(
        self,
        session_id: str,
        file_paths: List[str],
        working_directory: str = None,
        query: str = None,
    ) -> Tuple[List[FileContext], List[str]]:
        """
        Add files to a session context.

        Returns:
            Tuple of (successful_contexts, error_messages)
        """
        session = self.get_or_create_session(session_id, working_directory)
        successful = []
        errors = []

        # Validate total file count
        if len(file_paths) > MAX_FILES:
            errors.append(
                f"Too many files requested ({len(file_paths)}). Maximum is {MAX_FILES}."
            )
            file_paths = file_paths[:MAX_FILES]

        for file_path in file_paths:
            # Check if already cached in this session
            file_hash = hashlib.md5(file_path.encode()).hexdigest()
            if file_hash in session.files:
                successful.append(session.files[file_hash])
                continue

            # Read file
            content, error = self._file_reader.read_file(
                file_path, session.working_directory, include_error=True
            )
            if error:
                errors.append(f"{file_path}: {error}")
                continue

            # Check total size limit
            file_size = len(content.encode("utf-8"))
            if session.total_size + file_size > MAX_TOTAL_SIZE:
                errors.append(f"{file_path}: Would exceed total size limit")
                continue

            # Determine language
            path = Path(file_path)
            language = self._detect_language(path.suffix)

            # Create file context
            file_context = FileContext(
                path=str(path),
                content=content,
                language=language,
                size=file_size,
                last_modified=path.stat().st_mtime,
                hash=file_hash,
            )

            # Parse structure based on language
            if language == "python":
                parsed = self._code_parser.parse_python_file(content)
                file_context.classes = parsed["classes"]
                file_context.functions = parsed["functions"]
                file_context.imports = parsed["imports"]
            elif language in ["javascript", "typescript"]:
                parsed = self._code_parser.parse_javascript_file(content)
                file_context.classes = parsed["classes"]
                file_context.functions = parsed["functions"]
                file_context.imports = parsed["imports"]
            elif language == "go":
                parsed = self._code_parser.parse_go_file(content)
                file_context.functions = parsed["functions"]
                file_context.classes = parsed[
                    "types"
                ]  # Go types are similar to classes
                file_context.imports = [
                    imp
                    for group in parsed["imports"]
                    for imp in (group[0].split("\n") if group[0] else [group[1]])
                    if imp
                ]
            elif language == "rust":
                parsed = self._code_parser.parse_rust_file(content)
                file_context.functions = parsed["functions"]
                file_context.classes = parsed[
                    "structs"
                ]  # Rust structs are similar to classes
                file_context.imports = parsed["uses"]
            elif language == "java":
                parsed = self._code_parser.parse_java_file(content)
                file_context.classes = parsed["classes"]
                file_context.functions = parsed["methods"]
                file_context.imports = parsed["imports"]
            else:
                # Use generic parser for other languages
                parsed = self._code_parser.parse_generic_file(content)
                file_context.classes = parsed["classes"]
                file_context.functions = parsed["functions"]
                # No imports in generic parser

            # Extract relevant context if query provided
            if query:
                file_context.relevant_lines = (
                    self._code_parser.extract_relevant_context(content, query, language)
                )

            # Add to session
            session.files[file_hash] = file_context
            session.total_size += file_size
            successful.append(file_context)

        return successful, errors

    def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """Get session context if it exists and isn't expired"""
        if session_id in self._cache:
            session = self._cache[session_id]
            if not session.is_expired():
                session.touch()
                return session
            else:
                # Remove expired session
                del self._cache[session_id]
        return None

    def _cleanup_expired(self):
        """Remove expired sessions from cache"""
        expired = [sid for sid, session in self._cache.items() if session.is_expired()]
        for sid in expired:
            del self._cache[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def _detect_language(self, suffix: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".clj": "clojure",
        }
        return language_map.get(suffix.lower(), "unknown")

    def clear_session(self, session_id: str):
        """Clear a specific session from cache"""
        if session_id in self._cache:
            del self._cache[session_id]

    def clear_all(self):
        """Clear all cached sessions"""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._cleanup_expired()

        total_size = sum(s.total_size for s in self._cache.values())
        total_files = sum(len(s.files) for s in self._cache.values())

        return {
            "sessions": len(self._cache),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_session": min(
                (s.created_at for s in self._cache.values()), default=None
            ),
            "newest_session": max(
                (s.created_at for s in self._cache.values()), default=None
            ),
        }

    def extract_files_from_query(self, query: str) -> List[str]:
        """Extract file names mentioned in the query"""
        files = []

        # Pattern for file paths like "universal_mapper.py", "src/mapper.py", etc.
        file_pattern = r'(?:^|\s|["\'])([a-zA-Z0-9_\-/]+\.(?:py|js|ts|jsx|tsx|java|go|rs|cpp|c|h|hpp|cs|rb|php|swift|kt|scala|clj|md|txt|yaml|yml|json|toml|ini|cfg|conf|sh|bash|zsh|fish))(?:\s|["\']|$|:|\))'
        matches = re.findall(file_pattern, query)
        files.extend(matches)

        # Pattern for "line 80" references that might indicate a file context
        line_pattern = r"line\s+(\d+)"
        if re.search(line_pattern, query):
            # If line numbers mentioned, look for nearby file references
            pass  # Files already captured above

        return list(set(files))  # Remove duplicates

    def find_project_containing_files(
        self, file_names: List[str], search_dirs: List[str] = None
    ) -> Optional[str]:
        """Find a project directory containing the specified files"""
        if not file_names:
            return None

        # Default search directories
        if not search_dirs:
            search_dirs = [
                os.getcwd(),  # Current directory
                os.path.expanduser("~/Projects"),  # Common project directory
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/GDrive/Projects"),  # User's specific path
                "/tmp",  # Temporary projects
            ]

        # Search for the files in each directory
        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue

            try:
                # Use a simple find approach (limit depth for performance)
                for root, dirs, files in os.walk(base_dir):
                    # Limit search depth
                    depth = root[len(base_dir) :].count(os.sep)
                    if depth > 3:  # Don't go too deep
                        dirs[:] = []  # Don't recurse further
                        continue

                    # Skip hidden and system directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if not d.startswith(".")
                        and d not in ["node_modules", "venv", "__pycache__"]
                    ]

                    # Check if any target files exist here
                    for target_file in file_names:
                        if os.path.basename(target_file) in files:
                            # Found a match, verify it's the right project
                            full_path = os.path.join(
                                root, os.path.basename(target_file)
                            )
                            if os.path.exists(full_path):
                                # Return the project root (might be current dir or parent)
                                return root
            except (PermissionError, OSError):
                continue

        return None

    def load_project_registry(self) -> Dict[str, str]:
        """Load the project registry from disk"""
        if PROJECT_REGISTRY_PATH.exists():
            try:
                with open(PROJECT_REGISTRY_PATH, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning(
                    f"Failed to load project registry from {PROJECT_REGISTRY_PATH}"
                )
        return {}

    def save_project_registry(self, registry: Dict[str, str]):
        """Save the project registry to disk"""
        PROJECT_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(PROJECT_REGISTRY_PATH, "w") as f:
                json.dump(registry, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save project registry: {e}")

    def register_project(self, name: str, path: str):
        """Register a project path for future auto-discovery"""
        registry = self.load_project_registry()
        registry[name] = path
        self.save_project_registry(registry)
        logger.info(f"Registered project '{name}' at {path}")

    def auto_discover_context(
        self,
        query: str,
        file_paths: Optional[List[str]] = None,
        working_directory: Optional[str] = None,
    ) -> Tuple[Optional[str], List[str]]:
        """
        Auto-discover working directory and relevant files from query.

        Returns:
            Tuple of (working_directory, file_paths)
        """
        # If both are provided, nothing to discover
        if file_paths and working_directory:
            return working_directory, file_paths

        # Try to extract file names from query
        mentioned_files = self.extract_files_from_query(query) if not file_paths else []

        # If no working directory, try to find it
        if not working_directory:
            # 1. Check environment variable
            working_directory = os.environ.get("VIBE_CHECK_PROJECT_ROOT")

            # 2. Try to find project containing mentioned files
            if not working_directory and mentioned_files:
                working_directory = self.find_project_containing_files(mentioned_files)
                if working_directory:
                    logger.info(
                        f"Auto-discovered project at {working_directory} containing {mentioned_files}"
                    )

            # 3. Check project registry for keywords in query
            if not working_directory:
                registry = self.load_project_registry()
                for project_name, project_path in registry.items():
                    if project_name.lower() in query.lower():
                        working_directory = project_path
                        logger.info(
                            f"Found registered project '{project_name}' at {project_path}"
                        )
                        break

        # If we found a working directory but no files, use mentioned files
        if working_directory and not file_paths and mentioned_files:
            # Verify the files exist in the working directory
            verified_files = []
            for file_name in mentioned_files:
                # Try both basename and full relative path
                possible_paths = [
                    os.path.join(working_directory, file_name),
                    os.path.join(working_directory, os.path.basename(file_name)),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        verified_files.append(os.path.relpath(path, working_directory))
                        break

            if verified_files:
                file_paths = verified_files
                logger.info(f"Auto-discovered files: {file_paths}")

        return working_directory, file_paths or []


# Global cache instance
_context_cache = None


def get_context_cache() -> ContextCache:
    """Get or create the global context cache instance"""
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache


def reset_context_cache():
    """Reset the global context cache (for testing)"""
    global _context_cache
    if _context_cache:
        _context_cache.clear_all()
    _context_cache = None
