from .main import run_server, main
from .core import mcp
from .transport import detect_transport_mode
from .tools.text_analysis import demo_analyze_text, analyze_text_nollm
from .tools.system import server_status, get_telemetry_summary
from .tools.integration_decisions import check_integration_alternatives
from .tools.mentor.core import vibe_check_mentor

__all__ = [
    "run_server",
    "main",
    "mcp",
    "detect_transport_mode",
    "analyze_text_demo",
    "demo_analyze_text",
    "server_status",
    "get_telemetry_summary",
    "check_integration_alternatives",
    "vibe_check_mentor",
]

# Backward compatibility: preserve legacy import name
analyze_text_demo = demo_analyze_text
