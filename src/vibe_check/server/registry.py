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
from .tools.context7_integration import register_context7_tools
from vibe_check.tools.analyze_llm.tool_registry import (
    register_llm_production_tools,
    register_llm_diagnostic_tools
)
from vibe_check.tools.diagnostics_claude_cli import register_diagnostic_tools
from vibe_check.tools.config_validation import register_config_validation_tools

logger = logging.getLogger(__name__)


def _count_registered_tools(mcp: FastMCP) -> int:
    """Count registered tools for validation."""
    try:
        if hasattr(mcp, 'list_tools'):
            tools = mcp.list_tools()
            return len(tools)
        elif hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, 'tools'):
            return len(mcp._tool_manager.tools)
        else:
            return 0
    except Exception:
        return 0


def register_all_tools(mcp: FastMCP):
    """Register tools based on environment configuration.

    Default (Production Mode) - 22 tools:
    - Essential tools for anti-pattern detection and analysis
    - Core productivity and analysis capabilities
    - Professional, production-ready toolset

    VIBE_CHECK_DIAGNOSTICS=true - Adds 13 diagnostic tools:
    - Claude CLI diagnostics and status checking
    - Async system monitoring and health checks
    - Configuration validation tools

    VIBE_CHECK_DEV_MODE=true - Adds 6 development tools:
    - Demo and experimental tools
    - Session tracking reset
    - Comprehensive test suite (with OVERRIDE)

    Environment Variables:
    - VIBE_CHECK_DIAGNOSTICS: Enable diagnostic tools
    - VIBE_CHECK_DEV_MODE: Enable development tools
    - VIBE_CHECK_DEV_MODE_OVERRIDE: Enable comprehensive test suite
    """
    logger.info("=" * 60)
    logger.info("Registering tools based on environment configuration...")
    logger.info("=" * 60)

    # ========== PRODUCTION TOOLS (Always enabled) ==========
    logger.info("📦 Registering PRODUCTION tools...")

    register_system_tools(mcp)  # 1: server_status
    register_text_analysis_tools(mcp, dev_mode=False)  # 1: analyze_text_nollm
    register_project_context_tools(mcp)  # 3: detect_libraries, load_context, create_structure
    register_github_tools(mcp)  # 3: analyze_issue/pr_nollm, review_pr_comprehensive
    register_integration_decision_tools(mcp)  # 7: integration decision tools
    register_productivity_tools(mcp, dev_mode=False)  # 3: doom_loops, session_health, intervention
    register_mentor_tools(mcp)  # 1: vibe_check_mentor
    register_context7_tools(mcp)  # 3: resolve_lib, get_docs, get_hybrid_context
    register_llm_production_tools(mcp)  # 6: analyze_text/pr/code/issue/github_issue/github_pr_llm

    production_count = _count_registered_tools(mcp)
    logger.info(f"✅ Registered {production_count} production tools")

    # ========== DIAGNOSTIC TOOLS (Optional) ==========
    diagnostics_enabled = os.getenv("VIBE_CHECK_DIAGNOSTICS") == "true"
    if diagnostics_enabled:
        logger.info("🔍 DIAGNOSTICS mode enabled...")
        register_diagnostic_tools(mcp)  # 2: claude_cli_status, claude_cli_diagnostics
        register_config_validation_tools(mcp)  # 3: validate_mcp, check_integration, register_project
        register_llm_diagnostic_tools(mcp)  # 7: async monitoring + analyze_llm_status + test_with_env

        diag_count = _count_registered_tools(mcp) - production_count
        logger.info(f"🔍 +{diag_count} diagnostic tools registered")

    # ========== DEVELOPMENT TOOLS (Optional) ==========
    dev_mode = os.getenv("VIBE_CHECK_DEV_MODE") == "true"
    dev_mode_override = os.getenv("VIBE_CHECK_DEV_MODE_OVERRIDE") == "true"
    dev_count = 0

    if dev_mode or dev_mode_override:
        logger.info("🔧 DEV mode enabled...")
        before_dev = _count_registered_tools(mcp)

        # Register dev-only tools from main codebase
        register_text_analysis_tools(mcp, dev_mode=True)  # +1: demo_large_prompt_handling
        register_productivity_tools(mcp, dev_mode=True)  # +1: reset_session_tracking

        # Register comprehensive test suite (if OVERRIDE is set)
        if dev_mode_override:
            try:
                import sys
                from pathlib import Path

                tests_dir = Path(__file__).parent.parent.parent.parent / "tests"
                if str(tests_dir) not in sys.path:
                    sys.path.insert(0, str(tests_dir))

                from integration.claude_cli_tests import register_dev_tools
                if register_dev_tools:
                    register_dev_tools(mcp)  # +4: test_claude_cli_* tools
                    logger.info("🔧 Comprehensive test tools available")
            except ImportError as e:
                logger.warning(f"⚠️ Comprehensive test tools not available: {e}")

        dev_count = _count_registered_tools(mcp) - before_dev
        logger.info(f"🔧 +{dev_count} development tools registered")

    # ========== SUMMARY ==========
    total_tools = _count_registered_tools(mcp)
    logger.info("=" * 60)
    logger.info(f"📊 Total tools registered: {total_tools}")
    logger.info(f"📦 Production: {production_count}")
    if diagnostics_enabled:
        logger.info(f"🔍 Diagnostics: {_count_registered_tools(mcp) - production_count - (dev_count if (dev_mode or dev_mode_override) else 0)}")
    if dev_mode or dev_mode_override:
        logger.info(f"🔧 Development: {dev_count}")
    logger.info("=" * 60)
