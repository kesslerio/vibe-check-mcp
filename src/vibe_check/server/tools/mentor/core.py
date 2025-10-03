import logging
from typing import Dict, Any, Optional, List
from vibe_check.server.core import mcp
from .context import load_workspace_context
from .analysis import analyze_query_and_context
from .reasoning import get_reasoning_engine, generate_response

logger = logging.getLogger(__name__)


def register_mentor_tools(mcp_instance):
    """Registers mentor tools with the MCP server."""
    _register_tool(mcp_instance, vibe_check_mentor)


def _register_tool(mcp_instance, tool) -> None:
    manager = getattr(mcp_instance, "_tool_manager", None)
    tool_name = getattr(tool, "__name__", getattr(tool, "name", None))

    if manager and hasattr(manager, "_tools"):
        if tool_name in manager._tools:
            return

    mcp_instance.add_tool(tool)


@mcp.tool(name="vibe_check_mentor")
async def vibe_check_mentor(
    ctx,  # FastMCP Context for MCP sampling
    query: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    reasoning_depth: str = "standard",
    continue_session: bool = False,
    mode: str = "standard",
    phase: str = "planning",
    confidence_threshold: float = 0.7,
    file_paths: Optional[List[str]] = None,
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Multi-persona technical decision analysis with anti-pattern detection.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
    """
    logger.info(
        f"Vibe mentor activated: mode={mode}, depth={reasoning_depth}, phase={phase} for query: {query[:100]}..."
    )

    # 1. Load context
    full_context, session_id, workspace_warning = await load_workspace_context(
        query, context, session_id, file_paths, working_directory
    )

    # 2. Analyze query and context
    analysis_result = await analyze_query_and_context(
        query, full_context, phase, mode, confidence_threshold
    )

    if "clarifying_questions" in analysis_result:
        return analysis_result

    # 3. Get reasoning engine and generate response
    engine = get_reasoning_engine()
    response = await generate_response(
        engine=engine,
        query=query,
        context=full_context,
        session_id=session_id,
        reasoning_depth=reasoning_depth,
        continue_session=continue_session,
        mode=mode,
        phase=phase,
        analysis_result=analysis_result,
        workspace_warning=workspace_warning,
    )

    return response
