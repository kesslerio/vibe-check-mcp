from __future__ import annotations

import asyncio
from typing import Any

from .main import run_server, main
from .core import mcp, FastMCP
from .transport import detect_transport_mode
from .registry import ensure_tools_registered
from .tools import get_local_tool_names
from .tools.text_analysis import demo_analyze_text, analyze_text_nollm
from .tools.system import (
    server_status,
    get_telemetry_summary,
    list_registered_tools,
)
from .tools.integration_decisions import check_integration_alternatives
from .tools.mentor.core import vibe_check_mentor

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

__all__ = [
    "run_server",
    "main",
    "mcp",
    "server",
    "app",
    "FastMCP",
    "detect_transport_mode",
    "analyze_text_demo",
    "demo_analyze_text",
    "server_status",
    "get_telemetry_summary",
    "list_registered_tools",
    "check_integration_alternatives",
    "vibe_check_mentor",
]

# Backward compatibility: preserve legacy import name
analyze_text_demo = demo_analyze_text
