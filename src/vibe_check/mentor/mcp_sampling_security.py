"""Compatibility layer exposing secure MCP sampling components.

This module re-exports the hardened implementations that previously lived in
``vibe_check.mentor.deprecated.mcp_sampling_secure`` so that the rest of the
codebase (and third-party extensions) can continue to import from
``vibe_check.mentor.mcp_sampling_security``.  The secure components provide
input validation, sandboxed template rendering, file access controls, rate
limiting, and secrets scanning that are required for the security regression
suite.

The actual implementations continue to live in the deprecated namespace while
we finish the migration.  Keeping this lightweight compatibility shim avoids
code duplication while restoring the public API that the tests – and downstream
callers – expect.
"""

from __future__ import annotations

from .deprecated.mcp_sampling_secure import (
    EnhancedSecretsScanner,
    FileAccessController,
    FilePathInput,
    QueryInput,
    RateLimiter,
    SafeTemplateRenderer,
    TokenBucket,
    WorkspaceDataInput,
    sanitize_code_for_llm,
)

__all__ = [
    "EnhancedSecretsScanner",
    "FileAccessController",
    "FilePathInput",
    "QueryInput",
    "RateLimiter",
    "SafeTemplateRenderer",
    "TokenBucket",
    "WorkspaceDataInput",
    "sanitize_code_for_llm",
]
