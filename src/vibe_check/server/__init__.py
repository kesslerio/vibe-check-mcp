"""Public exports for the :mod:`vibe_check.server` package.

This module centralises the objects that external callers rely on so that
historical import paths such as ``from vibe_check.server import app`` continue
to function after the refactor that split the server into submodules.  Tests in
``tests/unit/test_mcp_server_tools.py`` patch ``FastMCP`` and ``app`` directly
from this package, while integrations expect to reach the mentor engine helper
via ``vibe_check.server`` as well.  Exposing these symbols here avoids
``AttributeError`` surprises when the package is imported in isolation (for
example during ``python -c"from vibe_check.server import *"``).
"""

from __future__ import annotations

import logging
import asyncio
from typing import Any

from .main import run_server, main
from .core import FastMCP, get_mcp_instance, mcp
from .transport import detect_transport_mode
from .registry import ensure_tools_registered, register_all_tools
from .tools import get_local_tool_names
from .tools.text_analysis import demo_analyze_text, analyze_text_nollm
from .tools.system import (
    server_status,
    get_telemetry_summary,
    list_registered_tools,
)
from .tools.integration_decisions import check_integration_alternatives
from .tools.mentor.core import vibe_check_mentor
from vibe_check.tools.vibe_mentor import get_mentor_engine

analyze_text_demo = demo_analyze_text
"""Backward compatible alias used throughout the test-suite."""

logger = logging.getLogger(__name__)

try:
    from vibe_check.mentor.mcp_sampling_patch import (
        auto_apply as _auto_apply_security_patches,
    )
except Exception as exc:  # pragma: no cover - defensive guard
    logger.warning("Security patches unavailable: %s", exc)
else:
    try:
        _PATCHED = _auto_apply_security_patches()
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Failed to apply security patches: %s", exc)
    else:
        if not _PATCHED:
            logger.warning(
                "Security patches did not verify; security regression tests may fail."
            )

ensure_tools_registered(mcp)


class MCPServerHandle:
    """Synchronous-friendly wrapper around the FastMCP server instance."""

    def __init__(self, instance: FastMCP):
        self._instance = instance

    def list_tools(self) -> Any:
        """Return registered tools, ensuring registration has occurred."""

        ensure_tools_registered(self._instance)
        return asyncio.run(self._instance.list_tools())

    def get_registered_tool_names(self) -> list[str]:
        """Return sorted list of locally defined MCP tool names."""

        return get_local_tool_names()

    def __getattr__(self, item: str) -> Any:
        return getattr(self._instance, item)


server = MCPServerHandle(mcp)
app = server
"""Expose the FastMCP instance under the historical ``app`` name."""

__all__ = [
    "run_server",
    "main",
    "app",
    "FastMCP",
    "get_mcp_instance",
    "mcp",
    "server",
    "register_all_tools",
    "ensure_tools_registered",
    "detect_transport_mode",
    "analyze_text_demo",
    "demo_analyze_text",
    "analyze_text_nollm",
    "server_status",
    "get_telemetry_summary",
    "list_registered_tools",
    "check_integration_alternatives",
    "vibe_check_mentor",
    "get_mentor_engine",
]
