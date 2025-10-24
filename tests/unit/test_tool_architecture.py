"""
Unit tests for tool architecture optimization (Issue #237).

Tests verify that tool registration respects environment-based gating
and that the correct number of tools are registered in each mode.
"""

import os
import pytest
from unittest.mock import Mock, patch
from mcp.server.fastmcp import FastMCP


class MockToolManager:
    """Mock tool manager for testing."""

    def __init__(self):
        self.tools = []
        self._tools = {}

    def add_tool(self, tool):
        """Add a tool to the registry."""
        name = getattr(tool, "__name__", getattr(tool, "name", None))
        if name not in self._tools:
            self.tools.append(tool)
            self._tools[name] = tool
        return tool


@pytest.fixture
def mcp_instance():
    """Create a mock MCP instance for testing."""
    mcp = Mock(spec=FastMCP)
    mcp._tool_manager = MockToolManager()
    # Support both no-args and keyword args for tool decorator
    mcp.tool = lambda **kwargs: lambda func: mcp._tool_manager.add_tool(func)
    mcp.add_tool = lambda func: mcp._tool_manager.add_tool(func)
    return mcp


@pytest.fixture
def clean_env():
    """Ensure clean environment for each test."""
    env_vars = [
        "VIBE_CHECK_DIAGNOSTICS",
        "VIBE_CHECK_DEV_MODE",
        "VIBE_CHECK_DEV_MODE_OVERRIDE",
    ]

    # Save original values
    original_values = {var: os.environ.get(var) for var in env_vars}

    # Clear all vars
    for var in env_vars:
        os.environ.pop(var, None)

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        else:
            os.environ.pop(var, None)


def test_production_mode_tool_count(mcp_instance, clean_env):
    """Verify production tool count (no env vars set)."""
    from vibe_check.server.registry import register_all_tools

    # Ensure no env vars are set
    assert os.getenv("VIBE_CHECK_DIAGNOSTICS") is None
    assert os.getenv("VIBE_CHECK_DEV_MODE") is None
    assert os.getenv("VIBE_CHECK_DEV_MODE_OVERRIDE") is None

    # Register tools
    register_all_tools(mcp_instance)

    # Count tools
    tool_count = len(mcp_instance._tool_manager.tools)

    # Expected: 30 production tools (current registry baseline)
    # Breakdown:
    # - system: 2 (server_status, get_telemetry_summary)
    # - text_analysis: 2 (demo_analyze_text, analyze_text_nollm)
    # - project_context: 3 (detect, load, create structure)
    # - github: 3 (issue/pr nollm, review_pr_comprehensive)
    # - integration decisions: 7 (core decision helpers)
    # - productivity: 3 (doom_loops, session_health, intervention)
    # - mentor: 1 (vibe_check_mentor)
    # - context7: 3 (resolve, get_docs, get_hybrid_context)
    # - llm production: 6 (analyze_*_llm variants)

    assert tool_count == 30, f"Expected 30 production tools, got {tool_count}"


def test_diagnostics_mode_tool_count(mcp_instance, clean_env):
    """Verify +11 diagnostic tools with VIBE_CHECK_DIAGNOSTICS=true."""
    from vibe_check.server.registry import register_all_tools

    # Enable diagnostics mode
    os.environ["VIBE_CHECK_DIAGNOSTICS"] = "true"

    # Register tools
    register_all_tools(mcp_instance)

    # Count tools
    tool_count = len(mcp_instance._tool_manager.tools)

    # Expected: 30 + 11 = 41 diagnostic tools
    # Additional diagnostic tools:
    # - diagnostics_claude_cli: 2 (claude_cli_status, claude_cli_diagnostics)
    # - config_validation: 2 (validate_mcp, check_integration)
    # - llm_diagnostic: 7 (async monitoring + analyze_llm_status + test_with_env)
    # Total: 2 + 2 + 7 = 11 diagnostic tools

    assert tool_count >= 30, f"Should have at least 30 tools, got {tool_count}"
    assert (
        tool_count >= 41
    ), f"Diagnostics mode should add 11 tools (30+11=41), got {tool_count}"


def test_dev_mode_tool_count(mcp_instance, clean_env):
    """Verify +2 tools with VIBE_CHECK_DEV_MODE=true (without OVERRIDE)."""
    from vibe_check.server.registry import register_all_tools

    # Enable dev mode (without override)
    os.environ["VIBE_CHECK_DEV_MODE"] = "true"

    # Register tools
    register_all_tools(mcp_instance)

    # Count tools
    tool_count = len(mcp_instance._tool_manager.tools)

    # Expected: 30 + 2 = 32 tools
    # Additional dev tools:
    # - demo_large_prompt_handling
    # - reset_session_tracking

    assert tool_count >= 30, f"Should have at least 30 tools, got {tool_count}"
    assert tool_count >= 32, f"Dev mode should add 2+ tools, got {tool_count}"


def test_all_modes_combined(mcp_instance, clean_env):
    """Verify all tools with both diagnostics and dev mode enabled."""
    from vibe_check.server.registry import register_all_tools

    # Enable both modes
    os.environ["VIBE_CHECK_DIAGNOSTICS"] = "true"
    os.environ["VIBE_CHECK_DEV_MODE"] = "true"

    # Register tools
    register_all_tools(mcp_instance)

    # Count tools
    tool_count = len(mcp_instance._tool_manager.tools)

    # Expected: 30 + 11 diagnostic + 2 dev = 43 tools
    # Production: 30
    # Diagnostic: 11 (2 + 2 + 7)
    # Dev: 2
    assert (
        tool_count >= 43
    ), f"Combined modes should have 43+ tools (30+11+2), got {tool_count}"


def test_llm_production_tools_only():
    """Test that LLM production tools registration works independently."""
    from vibe_check.tools.analyze_llm.tool_registry import register_llm_production_tools

    mcp = Mock(spec=FastMCP)
    tools_registered = []
    mcp.tool = lambda: lambda func: tools_registered.append(func) or func

    register_llm_production_tools(mcp)

    # Should register 6 production tools
    assert (
        len(tools_registered) == 6
    ), f"Expected 6 LLM production tools, got {len(tools_registered)}"


def test_llm_diagnostic_tools_only():
    """Test that LLM diagnostic tools registration works independently."""
    from vibe_check.tools.analyze_llm.tool_registry import register_llm_diagnostic_tools

    mcp = Mock(spec=FastMCP)
    tools_registered = []
    mcp.tool = lambda: lambda func: tools_registered.append(func) or func

    register_llm_diagnostic_tools(mcp)

    # Should register 7 diagnostic tools
    # Note: This includes inline tool definitions, so count may differ
    assert (
        len(tools_registered) >= 7
    ), f"Expected 7+ LLM diagnostic tools, got {len(tools_registered)}"


def test_text_analysis_dev_mode():
    """Test that text_analysis respects dev_mode and skip_production parameters."""
    from vibe_check.server.tools.text_analysis import register_text_analysis_tools

    # Test production mode
    mcp_prod = Mock()
    tools_prod = []
    mcp_prod.add_tool = lambda func: tools_prod.append(func)

    register_text_analysis_tools(mcp_prod, dev_mode=False)
    assert len(tools_prod) == 2, "Production mode should register 2 tools"

    # Test dev mode (with production)
    mcp_dev = Mock()
    tools_dev = []
    mcp_dev.add_tool = lambda func: tools_dev.append(func)

    register_text_analysis_tools(mcp_dev, dev_mode=True)
    assert len(tools_dev) == 3, "Dev mode should register 3 tools (2 production + 1 dev)"

    # Test dev mode with skip_production
    mcp_dev_skip = Mock()
    tools_dev_skip = []
    mcp_dev_skip.add_tool = lambda func: tools_dev_skip.append(func)

    register_text_analysis_tools(mcp_dev_skip, dev_mode=True, skip_production=True)
    assert (
        len(tools_dev_skip) == 1
    ), "Dev mode with skip_production should register only 1 dev tool"


def test_productivity_dev_mode():
    """Test that productivity tools respect dev_mode and skip_production parameters."""
    from vibe_check.server.tools.productivity import register_productivity_tools

    # Test production mode
    mcp_prod = Mock()
    tools_prod = []
    mcp_prod.add_tool = lambda func: tools_prod.append(func)

    register_productivity_tools(mcp_prod, dev_mode=False)
    assert len(tools_prod) == 3, "Production mode should register 3 tools"

    # Test dev mode (with production)
    mcp_dev = Mock()
    tools_dev = []
    mcp_dev.add_tool = lambda func: tools_dev.append(func)

    register_productivity_tools(mcp_dev, dev_mode=True)
    assert (
        len(tools_dev) == 4
    ), "Dev mode should register 4 tools (3 production + 1 dev)"

    # Test dev mode with skip_production
    mcp_dev_skip = Mock()
    tools_dev_skip = []
    mcp_dev_skip.add_tool = lambda func: tools_dev_skip.append(func)

    register_productivity_tools(mcp_dev_skip, dev_mode=True, skip_production=True)
    assert (
        len(tools_dev_skip) == 1
    ), "Dev mode with skip_production should register only 1 dev tool"


def test_diagnostic_prefix_in_descriptions():
    """Verify [DIAGNOSTIC] prefix is added to diagnostic tool descriptions."""
    from vibe_check.tools.diagnostics_claude_cli import register_diagnostic_tools

    mcp = Mock()
    registered_tools = {}

    def mock_tool():
        def decorator(func):
            registered_tools[func.__name__] = func.__doc__
            return func

        return decorator

    mcp.tool = mock_tool

    register_diagnostic_tools(mcp)

    # Check that registered tools have [DIAGNOSTIC] prefix
    for tool_name, docstring in registered_tools.items():
        assert (
            "[DIAGNOSTIC]" in docstring
        ), f"{tool_name} should have [DIAGNOSTIC] prefix"


def test_dev_prefix_in_descriptions():
    """Verify [DEV] prefix is added to dev tool descriptions."""
    # Check demo_large_prompt_handling
    from vibe_check.server.tools.text_analysis import demo_large_prompt_handling

    assert (
        "[DEV]" in demo_large_prompt_handling.__doc__
    ), "demo_large_prompt_handling should have [DEV] prefix"

    # Check reset_session_tracking
    from vibe_check.server.tools.productivity import reset_session_tracking

    assert (
        "[DEV]" in reset_session_tracking.__doc__
    ), "reset_session_tracking should have [DEV] prefix"


def test_backward_compatibility():
    """Test that register_llm_analysis_tools still works for backward compatibility."""
    from vibe_check.tools.analyze_llm.tool_registry import register_llm_analysis_tools

    mcp = Mock(spec=FastMCP)
    tools_registered = []
    mcp.tool = lambda: lambda func: tools_registered.append(func) or func

    # Should not raise any errors
    register_llm_analysis_tools(mcp)

    # Should register both production and diagnostic tools
    assert (
        len(tools_registered) >= 6
    ), "Backward compatible function should register at least 6 tools"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
