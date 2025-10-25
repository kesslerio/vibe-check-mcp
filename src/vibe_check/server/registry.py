import asyncio
import inspect
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
    register_llm_diagnostic_tools,
)
from vibe_check.tools.diagnostics_claude_cli import register_diagnostic_tools
from vibe_check.tools.config_validation import register_config_validation_tools

logger = logging.getLogger(__name__)


_TOOLS_INITIALIZED = False


def _count_registered_tools(mcp: FastMCP) -> int:
    """Count registered tools for validation."""
    try:
        if hasattr(mcp, "list_tools"):
            tools = mcp.list_tools()
            if inspect.isawaitable(tools):
                try:
                    tools = asyncio.run(tools)
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        logger.debug(
                            "Active event loop detected - deferring tool count"
                        )
                        return 0
                    tools = loop.run_until_complete(tools)
            return len(tools)
        elif hasattr(mcp, "_tool_manager") and hasattr(mcp._tool_manager, "tools"):
            return len(mcp._tool_manager.tools)
        else:
            return 0
    except Exception:
        return 0


def get_registered_tool_count(mcp: FastMCP) -> int:
    """Public helper for retrieving the registered tool count."""

    return _count_registered_tools(mcp)


def ensure_tools_registered(mcp: FastMCP) -> int:
    """Ensure tools are registered once and return the resulting count."""

    global _TOOLS_INITIALIZED

    registered = _count_registered_tools(mcp)
    if not _TOOLS_INITIALIZED or registered == 0:
        logger.debug("Tool registry not initialized - registering tools now")
        register_all_tools(mcp)
        _TOOLS_INITIALIZED = True
        registered = _count_registered_tools(mcp)

    return registered


def register_all_tools(mcp: FastMCP):
    """Register tools based on environment configuration.

    Default (Production Mode) - 22 tools:
    - Essential tools for anti-pattern detection and analysis
    - Core productivity and analysis capabilities
    - Professional, production-ready toolset

    VIBE_CHECK_DIAGNOSTICS=true - Adds 11 diagnostic tools:
    - Claude CLI diagnostics (2 tools: status, diagnostics)
    - Configuration validation (2 tools: validate_mcp, check_integration)
    - Async LLM monitoring (7 tools: async analysis, health, metrics, status)

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

    dev_mode = os.getenv("VIBE_CHECK_DEV_MODE") == "true"
    dev_mode_override = os.getenv("VIBE_CHECK_DEV_MODE_OVERRIDE") == "true"
    diagnostics_enabled = os.getenv("VIBE_CHECK_DIAGNOSTICS") == "true"

    # ========== PRODUCTION TOOLS (Always enabled) ==========
    logger.info("📦 Registering PRODUCTION tools...")

    register_system_tools(
        mcp,
        include_introspection=(diagnostics_enabled or dev_mode or dev_mode_override),
    )  # server status + telemetry (+ introspection in diagnostics/dev)
    register_text_analysis_tools(mcp, dev_mode=False)  # 1: analyze_text_nollm
    register_project_context_tools(
        mcp, dev_mode=(dev_mode or dev_mode_override)
    )  # 3 production tools + optional dev-only registration helper
    register_github_tools(mcp)  # 3: analyze_issue/pr_nollm, review_pr_comprehensive
    register_integration_decision_tools(mcp)  # 7: integration decision tools
    register_productivity_tools(
        mcp, dev_mode=False
    )  # 3: doom_loops, session_health, intervention
    register_mentor_tools(mcp)  # 1: vibe_check_mentor
    register_context7_tools(mcp)  # 3: resolve_lib, get_docs, get_hybrid_context
    register_llm_production_tools(
        mcp
    )  # 6: analyze_text/pr/code/issue/github_issue/github_pr_llm

    # Total: 2 + 1 + 4 + 3 + 7 + 3 + 1 + 3 + 6 = 30 production tools

    production_count = _count_registered_tools(mcp)
    logger.info(f"✅ Registered {production_count} production tools")

    # ========== DIAGNOSTIC TOOLS (Optional) ==========
    if diagnostics_enabled:
        logger.info("🔍 DIAGNOSTICS mode enabled...")
        register_diagnostic_tools(mcp)  # 2: claude_cli_status, claude_cli_diagnostics
        register_config_validation_tools(mcp)  # 2: validate_mcp, check_integration
        register_llm_diagnostic_tools(
            mcp
        )  # 7: async monitoring + analyze_llm_status + test_with_env

        # Total: 2 + 2 + 7 = 11 diagnostic tools

        diag_count = _count_registered_tools(mcp) - production_count
        logger.info(f"🔍 +{diag_count} diagnostic tools registered")

    # ========== DEVELOPMENT TOOLS (Optional) ==========
    dev_count = 0

    if dev_mode or dev_mode_override:
        logger.info("🔧 DEV mode enabled...")
        before_dev = _count_registered_tools(mcp)

        # Register dev-only tools (skip production since they're already registered above)
        register_text_analysis_tools(
            mcp, dev_mode=True, skip_production=True
        )  # +1: demo_large_prompt_handling
        register_productivity_tools(
            mcp, dev_mode=True, skip_production=True
        )  # +1: reset_session_tracking

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
        logger.info(
            f"🔍 Diagnostics: {_count_registered_tools(mcp) - production_count - (dev_count if (dev_mode or dev_mode_override) else 0)}"
        )
    if dev_mode or dev_mode_override:
        logger.info(f"🔧 Development: {dev_count}")
    logger.info("=" * 60)

    global _TOOLS_INITIALIZED
    _TOOLS_INITIALIZED = True
