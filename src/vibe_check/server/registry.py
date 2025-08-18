import logging
import os
from mcp.server.fastmcp import FastMCP
from .tools.system import register_system_tools
from .tools.text_analysis import register_text_analysis_tools
from .tools.project_context import register_project_context_tools
from .tools.github_integration import register_github_tools
from .tools.integration_decisions import register_integration_decision_tools
from .tools.productivity import register_productivity_tools
from .tools.mentor.core import register_mentor_tools
from vibe_check.tools.analyze_llm.tool_registry import register_llm_analysis_tools
from vibe_check.tools.diagnostics_claude_cli import register_diagnostic_tools
from vibe_check.tools.config_validation import register_config_validation_tools

logger = logging.getLogger(__name__)

def register_all_tools(mcp: FastMCP):
    """Registers all available tools with the MCP server."""
    logger.info("Registering all tools...")
    
    register_system_tools(mcp)
    register_text_analysis_tools(mcp)
    register_project_context_tools(mcp)
    register_github_tools(mcp)
    register_integration_decision_tools(mcp)
    register_productivity_tools(mcp)
    register_mentor_tools(mcp)
    register_llm_analysis_tools(mcp)
    register_diagnostic_tools(mcp)
    register_config_validation_tools(mcp)

    dev_mode_override = os.getenv("VIBE_CHECK_DEV_MODE_OVERRIDE") == "true"
    if dev_mode_override:
        try:
            import sys
            from pathlib import Path
            
            tests_dir = Path(__file__).parent.parent.parent.parent / "tests"
            if str(tests_dir) not in sys.path:
                sys.path.insert(0, str(tests_dir))
            
            from integration.claude_cli_tests import register_dev_tools
            if register_dev_tools:
                register_dev_tools(mcp)
                logger.info("🔧 Dev mode enabled: Comprehensive testing tools available")
        except ImportError as e:
            logger.warning(f"⚠️ Dev tools not available: {e}")
