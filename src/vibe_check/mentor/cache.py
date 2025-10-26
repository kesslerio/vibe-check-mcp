"""
Context caching with session management and project registry.

Provides in-memory caching with TTL, session management, and project discovery.
"""

import os
import time
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .context_models import FileContext, SessionContext
from .constants import MAX_FILES, MAX_TOTAL_SIZE, PROJECT_REGISTRY_PATH
from .file_reader import FileReader
from .code_parser import CodeParser

logger = logging.getLogger(__name__)


class ContextCache:
    """Manages session-based context caching"""

    def __init__(self):
        self._cache: Dict[str, SessionContext] = {}
        self._file_reader = FileReader()
        self._code_parser = CodeParser()

    def get_or_create_session(
        self, session_id: str, working_directory: str | None = None
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
        working_directory: str | None = None,
        query: str | None = None,
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
        self, file_names: List[str], search_dirs: List[str] | None = None
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
