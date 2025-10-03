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

from .main import run_server, main
from .core import FastMCP, get_mcp_instance, mcp
from .transport import detect_transport_mode
from .registry import register_all_tools
from .tools.text_analysis import demo_analyze_text
from .tools.system import server_status, get_telemetry_summary
from .tools.integration_decisions import check_integration_alternatives
from .tools.mentor.core import vibe_check_mentor
from vibe_check.tools.vibe_mentor import get_mentor_engine

analyze_text_demo = demo_analyze_text
"""Backward compatible alias used throughout the test-suite."""

app = mcp
"""Expose the FastMCP instance under the historical ``app`` name."""

__all__ = [
    "run_server",
    "main",
    "app",
    "FastMCP",
    "get_mcp_instance",
    "mcp",
    "register_all_tools",
    "detect_transport_mode",
    "analyze_text_demo",
    "demo_analyze_text",
    "server_status",
    "get_telemetry_summary",
    "check_integration_alternatives",
    "vibe_check_mentor",
    "get_mentor_engine",
]
