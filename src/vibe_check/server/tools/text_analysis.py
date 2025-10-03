import logging
from typing import Dict, Any
from vibe_check.server.core import mcp
from vibe_check.tools.analyze_text_nollm import (
    analyze_text_demo as analyze_text_core,
    demo_analyze_text as legacy_demo_analyze_text,
)
from vibe_check.tools.large_prompt_demo import demo_large_prompt_analysis

logger = logging.getLogger(__name__)


def register_text_analysis_tools(
    mcp_instance, dev_mode: bool = False, skip_production: bool = False
):
    """Registers text analysis tools with the MCP server.

    Args:
        mcp_instance: The MCP server instance
        dev_mode: If True, registers development/demo tools
        skip_production: If True, skips production tools (useful when they're already registered)
    """
    # Register production tools unless explicitly skipped
    if not skip_production:
        _register_tool(mcp_instance, demo_analyze_text)
        _register_tool(mcp_instance, analyze_text_nollm)

    # Only register dev/demo tools when dev_mode=True
    if dev_mode:
        logger.info("Registering demo_large_prompt_handling (dev mode)")
        _register_tool(mcp_instance, demo_large_prompt_handling)


def _register_tool(mcp_instance, tool) -> None:
    manager = getattr(mcp_instance, "_tool_manager", None)
    tool_name = getattr(tool, "__name__", getattr(tool, "name", None))

    if manager and hasattr(manager, "_tools"):
        if tool_name in manager._tools:
            return

    mcp_instance.add_tool(tool)


@mcp.tool(name="analyze_text_nollm")
def analyze_text_nollm(
    text: str,
    detail_level: str = "standard",
    use_project_context: bool = True,
    project_root: str = ".",
) -> Dict[str, Any]:
    """
    Fast text analysis using direct pattern detection with contextual awareness.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
    """
    logger.info(
        f"Fast text analysis requested for {len(text)} characters with context={use_project_context}"
    )
    return analyze_text_core(
        text,
        detail_level,
        use_project_context=use_project_context,
        project_root=project_root,
    )


@mcp.tool(name="demo_analyze_text")
def demo_analyze_text(
    text: str,
    detail_level: str = "standard",
    use_project_context: bool = True,
    project_root: str = ".",
) -> Dict[str, Any]:
    """Demo-friendly wrapper that mirrors the legacy response contract."""

    logger.info(
        "Demo text analysis requested for %d characters (context=%s)",
        len(text),
        use_project_context,
    )
    return legacy_demo_analyze_text(
        text=text,
        detail_level=detail_level,
        use_project_context=use_project_context,
        project_root=project_root,
    )


@mcp.tool(name="demo_large_prompt_handling")
def demo_large_prompt_handling(
    content: str, files: list = None, detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    [DEV] Demo: Zen-style Large Prompt Handling for MCP's 25K token limit.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
    """
    logger.info(f"Large prompt demo requested for {len(content)} characters")
    return demo_large_prompt_analysis(content, files, detail_level)
