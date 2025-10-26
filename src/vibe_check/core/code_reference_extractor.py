"""
Code Reference Extractor - Enhanced Implementation for Issue #152

Extracts code references from GitHub issue text including file paths,
function names, and stack traces. Follows mentor guidance to start
with working API calls first, then extract patterns.

Includes improvements from PR #154 code review:
- Binary file filtering
- Path validation for security
- Performance optimizations
- Configurable extraction limits
"""

import re
import logging
from typing import Dict, List, Optional, NamedTuple, Set, Any, Union
from dataclasses import dataclass
import os.path

logger = logging.getLogger(__name__)


@dataclass
class CodeReference:
    """Represents a code reference extracted from issue text."""

    type: str  # 'file_path', 'function_name', 'line_reference', 'stack_trace'
    value: str
    line_number: Optional[int] = None
    confidence: float = 0.0
    context: str = ""


@dataclass
class ExtractionConfig:
    """Configuration for code reference extraction."""

    max_context_lines: int = 5
    max_files_per_issue: int = 3
    max_line_refs_per_file: int = 2
    max_file_path_length: int = 200
    enable_metrics_logging: bool = True


class CodeReferenceExtractor:
    """Enhanced code reference extraction for GitHub issues."""

    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".svg",
        ".ico",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wav",
        ".flac",
    }

    # Text file extensions that are safe to analyze
    TEXT_EXTENSIONS = {
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".py",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".cs",
        ".php",
        ".rb",
        ".go",
        ".rs",
        ".kt",
        ".swift",
        ".scala",
        ".html",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".txt",
        ".md",
        ".rst",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
    }

    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()

        # Compile regex patterns for better performance (from code review)
        self.compiled_file_patterns = [
            re.compile(r"`([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})`"),  # `src/file.js`
            re.compile(
                r"(?:file|in|at)\s+([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})"
            ),  # file src/file.js
            re.compile(r"([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4}):(\d+)"),  # file.js:42
            re.compile(r'"([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})"'),  # "src/file.js"
        ]

        self.compiled_function_patterns = [
            re.compile(
                r"function\s+([a-zA-Z_][a-zA-Z0-9_]*)"
            ),  # function processPayment
            re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\(\)"),  # processPayment()
            re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*)\(`"),  # `processPayment(`
        ]

        self.compiled_stack_trace_patterns = [
            re.compile(
                r"at\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+\(([^)]+):(\d+):(\d+)\)"
            ),  # Node.js
            re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+)'),  # Python
        ]

    def _is_valid_file_path(self, file_path: str) -> bool:
        """
        Validate file path for security and reasonableness.

        Args:
            file_path: File path to validate

        Returns:
            True if file path is valid and safe
        """
        # Basic sanity checks
        if not file_path or len(file_path) < 3:
            if self.config.enable_metrics_logging:
                logger.debug(f"File path too short: '{file_path}'")
            return False

        # Length check
        if len(file_path) > self.config.max_file_path_length:
            if self.config.enable_metrics_logging:
                logger.debug(
                    f"File path too long ({len(file_path)} chars): '{file_path[:50]}...'"
                )
            return False

        # Path traversal check (security critical)
        if ".." in file_path:
            if self.config.enable_metrics_logging:
                logger.warning(f"Path traversal attempt detected: '{file_path}'")
            return False

        # System/sensitive file protection
        sensitive_patterns = ["/etc/", "/proc/", "/sys/", "/dev/", "/tmp/", "/var/log/"]
        if any(pattern in file_path.lower() for pattern in sensitive_patterns):
            if self.config.enable_metrics_logging:
                logger.warning(f"Sensitive system path blocked: '{file_path}'")
            return False

        # Allow absolute paths for stack traces but be more restrictive for user input
        if file_path.startswith("/") and not file_path.startswith(
            ("/app/", "/src/", "/lib/", "/opt/", "/home/", "/usr/local/")
        ):
            if self.config.enable_metrics_logging:
                logger.debug(
                    f"Absolute path outside allowed directories: '{file_path}'"
                )
            return False

        # Must have extension for most cases (allow some exceptions like Dockerfile, Makefile)
        if "." not in file_path and not any(
            name in file_path
            for name in ["Dockerfile", "Makefile", "README", "LICENSE"]
        ):
            if self.config.enable_metrics_logging:
                logger.debug(f"File path missing extension: '{file_path}'")
            return False

        # Check for reasonable file structure (prevent deep nesting attacks)
        if file_path.count("/") > 15:  # More generous limit but still reasonable
            if self.config.enable_metrics_logging:
                logger.debug(
                    f"File path too deeply nested ({file_path.count('/')} levels): '{file_path}'"
                )
            return False

        # Check for invalid characters that could indicate injection attempts
        invalid_chars = ["<", ">", "|", "&", ";", "`", "$"]
        if any(char in file_path for char in invalid_chars):
            if self.config.enable_metrics_logging:
                logger.warning(f"Invalid characters in file path: '{file_path}'")
            return False

        return True

    def _is_text_file(self, file_path: str) -> bool:
        """
        Check if file is likely a text file that can be analyzed.

        Args:
            file_path: File path to check

        Returns:
            True if file is safe to analyze as text
        """
        ext = os.path.splitext(file_path)[1].lower()

        # Skip known binary extensions
        if ext in self.BINARY_EXTENSIONS:
            return False

        # Allow known text extensions
        if ext in self.TEXT_EXTENSIONS:
            return True

        # Files without extension or unknown extensions - be cautious
        return len(ext) == 0  # Allow files without extensions

    def extract_references(self, text: str) -> List[CodeReference]:
        """
        Extract code references from issue text with enhanced validation.

        Args:
            text: Issue body or title text

        Returns:
            List of extracted and validated code references
        """
        references = []
        extraction_stats = {
            "files": 0,
            "functions": 0,
            "stack_traces": 0,
            "filtered": 0,
        }

        # Extract file paths
        file_refs = self._extract_file_paths(text)
        # Filter and validate file references
        validated_file_refs = []
        for ref in file_refs:
            if self._is_valid_file_path(ref.value) and self._is_text_file(ref.value):
                validated_file_refs.append(ref)
                extraction_stats["files"] += 1
            else:
                extraction_stats["filtered"] += 1
                if self.config.enable_metrics_logging:
                    logger.debug(f"Filtered invalid/binary file reference: {ref.value}")

        references.extend(validated_file_refs)

        # Extract function references
        func_refs = self._extract_functions(text)
        references.extend(func_refs)
        extraction_stats["functions"] = len(func_refs)

        # Extract stack traces
        stack_refs = self._extract_stack_traces(text)
        references.extend(stack_refs)
        extraction_stats["stack_traces"] = len(stack_refs)

        # Log extraction metrics
        if self.config.enable_metrics_logging and any(extraction_stats.values()):
            logger.info(f"Code reference extraction: {extraction_stats}")

        return references

    def _extract_file_paths(self, text: str) -> List[CodeReference]:
        """Extract file path references using compiled patterns."""
        references = []

        for pattern in self.compiled_file_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        # File path with line number
                        file_path = match.group(1)
                        line_num = int(match.group(2))
                        confidence = 0.9  # High confidence for explicit line refs
                    else:
                        file_path = match.group(1)
                        line_num = None
                        confidence = 0.7  # Medium confidence for file refs

                    # Basic validation - must have valid extension
                    if "." in file_path and len(file_path) > 3:
                        references.append(
                            CodeReference(
                                type="file_path",
                                value=file_path,
                                line_number=line_num,
                                confidence=confidence,
                                context=match.group(0),
                            )
                        )
                except ValueError as e:
                    if self.config.enable_metrics_logging:
                        logger.debug(
                            f"Invalid line number in file reference '{match.group(0)}': {e}"
                        )
                except IndexError as e:
                    if self.config.enable_metrics_logging:
                        logger.debug(
                            f"Malformed file reference pattern '{match.group(0)}': {e}"
                        )
                except Exception as e:
                    if self.config.enable_metrics_logging:
                        logger.warning(
                            f"Unexpected error parsing file reference '{match.group(0)}': {e}"
                        )

        return references

    def _extract_functions(self, text: str) -> List[CodeReference]:
        """Extract function name references using compiled patterns."""
        references = []

        for pattern in self.compiled_function_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    func_name = match.group(1)

                    # Enhanced validation
                    if (
                        len(func_name) >= 3
                        and func_name.isidentifier()
                        and not func_name.isupper()
                    ):  # Exclude constants like 'ERROR'
                        confidence = 0.6  # Medium confidence for function refs
                        references.append(
                            CodeReference(
                                type="function_name",
                                value=func_name,
                                confidence=confidence,
                                context=match.group(0),
                            )
                        )
                except ValueError as e:
                    if self.config.enable_metrics_logging:
                        logger.debug(
                            f"Invalid function name in reference '{match.group(0)}': {e}"
                        )
                except IndexError as e:
                    if self.config.enable_metrics_logging:
                        logger.debug(
                            f"Malformed function reference pattern '{match.group(0)}': {e}"
                        )
                except Exception as e:
                    if self.config.enable_metrics_logging:
                        logger.warning(
                            f"Unexpected error parsing function reference '{match.group(0)}': {e}"
                        )

        return references

    def _extract_stack_traces(self, text: str) -> List[CodeReference]:
        """Extract stack trace information using compiled patterns."""
        references = []

        for pattern in self.compiled_stack_trace_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        file_path = (
                            match.group(2)
                            if len(match.groups()) > 2
                            else match.group(1)
                        )
                        line_num = (
                            int(match.group(3))
                            if len(match.groups()) > 3
                            else int(match.group(2))
                        )

                        # Validate stack trace file path
                        if self._is_valid_file_path(file_path):
                            references.append(
                                CodeReference(
                                    type="stack_trace",
                                    value=file_path,
                                    line_number=line_num,
                                    confidence=0.95,  # Very high confidence for stack traces
                                    context=match.group(0),
                                )
                            )
                except ValueError as e:
                    if self.config.enable_metrics_logging:
                        logger.debug(
                            f"Invalid line number in stack trace '{match.group(0)}': {e}"
                        )
                except IndexError as e:
                    if self.config.enable_metrics_logging:
                        logger.debug(
                            f"Malformed stack trace pattern '{match.group(0)}': {e}"
                        )
                except Exception as e:
                    if self.config.enable_metrics_logging:
                        logger.warning(
                            f"Unexpected error parsing stack trace '{match.group(0)}': {e}"
                        )

        return references

    def get_unique_files(self, references: List[CodeReference]) -> List[str]:
        """Get unique file paths from references."""
        files = set()
        for ref in references:
            if ref.type in ["file_path", "stack_trace"]:
                files.add(ref.value)
        return list(files)

    def get_file_with_lines(
        self, references: List[CodeReference]
    ) -> Dict[str, List[int]]:
        """Get files mapped to their referenced line numbers."""
        file_lines: Dict[str, List[int]] = {}
        for ref in references:
            if ref.type in ["file_path", "stack_trace"] and ref.line_number:
                if ref.value not in file_lines:
                    file_lines[ref.value] = []
                file_lines[ref.value].append(ref.line_number)
        return file_lines


def extract_code_references_from_issue(issue_text: str) -> Dict[str, Any]:
    """
    Simple function for extracting code references - minimal POC.

    Args:
        issue_text: GitHub issue body text

    Returns:
        Dictionary with extracted references
    """
    extractor = CodeReferenceExtractor()
    references = extractor.extract_references(issue_text)

    return {
        "file_paths": extractor.get_unique_files(references),
        "function_names": [
            ref.value for ref in references if ref.type == "function_name"
        ],
        "file_lines": extractor.get_file_with_lines(references),
        "confidence_scores": [ref.confidence for ref in references],
    }
