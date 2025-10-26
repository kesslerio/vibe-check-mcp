"""
Context data models for context management.

Provides core dataclasses for representing file and session context.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .constants import (
    MAX_FILE_SIZE,
    MAX_TOTAL_SIZE,
    MAX_FILES,
    CACHE_TTL_SECONDS,
    MAX_LINE_LENGTH,
    ALLOWED_EXTENSIONS,
    PROJECT_REGISTRY_PATH,
)


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
