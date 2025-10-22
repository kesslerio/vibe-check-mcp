"""
Backward compatibility layer for external Claude CLI tooling.

Historically, tests and integration scripts imported
``vibe_check.tools.external_claude_cli`` directly. The refactor that introduced
modular Claude integration moved the primary implementation into
``vibe_check.tools.shared.claude_integration`` and legacy fallbacks into the
backup analyzer module.  This shim keeps the original import path working so
older tests that haven't been updated (or third-party scripts) continue to
collect without raising ``ModuleNotFoundError``.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from 'vibe_check.tools.external_claude_cli' is deprecated; "
    "use 'vibe_check.tools.shared.claude_integration' or "
    "'vibe_check.tools.analyze_llm_backup' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .analyze_llm_backup import ExternalClaudeCli  # Legacy compatibility
from .shared.claude_integration import (
    ClaudeCliExecutor,
    ClaudeCliResult,
    analyze_content_async,
)

__all__ = [
    "ExternalClaudeCli",
    "ClaudeCliExecutor",
    "ClaudeCliResult",
    "analyze_content_async",
]


def get_default_executor(timeout_seconds: int = 60) -> ClaudeCliExecutor:
    """
    Convenience helper returning the modern Claude CLI executor.

    Legacy tests frequently instantiated ``ExternalClaudeCli`` directly.  New
    integrations should prefer ``ClaudeCliExecutor``; this helper offers a clear
    upgrade path without breaking existing imports.
    """

    return ClaudeCliExecutor(timeout_seconds=timeout_seconds)
