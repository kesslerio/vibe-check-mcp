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

This module is now a thin re-export layer for backward compatibility.
The actual implementation is split into focused submodules:
- models: FileContext and SessionContext dataclasses
- validators: SecurityValidator for path validation
- file_reader: FileReader for secure file access
- code_parser: CodeParser for language-specific parsing
- cache: ContextCache and session management
"""

# Re-export constants
from .constants import (
    MAX_FILE_SIZE,
    MAX_TOTAL_SIZE,
    MAX_FILES,
    CACHE_TTL_SECONDS,
    MAX_LINE_LENGTH,
    ALLOWED_EXTENSIONS,
    PROJECT_REGISTRY_PATH,
)

# Re-export core models
from .context_models import (
    FileContext,
    SessionContext,
)

# Re-export security validator
from .validators import SecurityValidator

# Re-export file reader
from .file_reader import FileReader

# Re-export code parser
from .code_parser import CodeParser

# Re-export cache management
from .cache import (
    ContextCache,
    get_context_cache,
    reset_context_cache,
)

__all__ = [
    # Models
    "FileContext",
    "SessionContext",
    # Constants
    "MAX_FILE_SIZE",
    "MAX_TOTAL_SIZE",
    "MAX_FILES",
    "CACHE_TTL_SECONDS",
    "MAX_LINE_LENGTH",
    "ALLOWED_EXTENSIONS",
    "PROJECT_REGISTRY_PATH",
    # Security
    "SecurityValidator",
    # File operations
    "FileReader",
    # Code parsing
    "CodeParser",
    # Caching
    "ContextCache",
    "get_context_cache",
    "reset_context_cache",
]
