"""
Constants for context management and security.

Centralized location for all configuration constants used across modules.
"""

from pathlib import Path

# Security constraints
MAX_FILE_SIZE = 1024 * 1024  # 1MB max per file
MAX_TOTAL_SIZE = 5 * 1024 * 1024  # 5MB total for all files
MAX_FILES = 10  # Maximum number of files to read
MAX_LINE_LENGTH = 1000  # Maximum line length to prevent memory issues

# Cache configuration
CACHE_TTL_SECONDS = 3600  # 1 hour cache TTL

# File type support
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

# Project registry location
PROJECT_REGISTRY_PATH = Path.home() / ".vibe-check" / "project_registry.json"
