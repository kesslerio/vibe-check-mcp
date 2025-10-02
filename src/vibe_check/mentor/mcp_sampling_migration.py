"""Compatibility shim for secure MCP sampling migration helpers.

The comprehensive migration layer lives in
``vibe_check.mentor.deprecated.mcp_sampling_migration`` while the refactor is
finalised.  The original public module path –
``vibe_check.mentor.mcp_sampling_migration`` – disappeared during the cleanup,
which broke the security regression suite.  This module restores that public
API by re-exporting the secure migration helpers from the deprecated package.
"""

from __future__ import annotations

from .deprecated.mcp_sampling_migration import (
    EnhancedSecretsScanner,
    FileAccessController,
    QueryInput,
    RateLimiter,
    SafeTemplateRenderer,
    SecureMCPSamplingClient,
    SecurePromptBuilder,
    SecurePromptTemplate,
    WorkspaceDataInput,
    migrate_to_secure_client,
)

__all__ = [
    "EnhancedSecretsScanner",
    "FileAccessController",
    "QueryInput",
    "RateLimiter",
    "SafeTemplateRenderer",
    "SecureMCPSamplingClient",
    "SecurePromptBuilder",
    "SecurePromptTemplate",
    "WorkspaceDataInput",
    "migrate_to_secure_client",
]
