import logging
from typing import Dict, Any, Optional, List
from ...core import mcp
from .context import load_workspace_context
from .analysis import analyze_query_and_context
from .reasoning import get_reasoning_engine, generate_response

logger = logging.getLogger(__name__)

def register_mentor_tools(mcp_instance):
    """Registers mentor tools with the MCP server."""
    mcp_instance.add_tool(vibe_check_mentor)

@mcp.tool()
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
    working_directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    🧠 Senior engineer collaborative reasoning - Get multi-perspective feedback on technical decisions.

    Interactive senior engineer mentor combining vibe-check pattern detection with collaborative reasoning.
    Multiple engineering personas analyze your technical decisions and provide structured feedback.

    Features:
    - 🧠 Multi-persona collaborative reasoning (Senior, Product, AI/ML Engineer perspectives)
    - 🎯 Automatic anti-pattern detection drives persona responses
    - 💬 Session continuity for multi-turn conversations  
    - 📊 Structured insights with consensus and disagreements
    - 🎓 Educational coaching recommendations
    - ⚡ NEW: Interrupt mode for quick focused interventions

    Modes:
    - interrupt: Quick focused intervention (<3 seconds) - single question/approval
    - standard: Normal collaborative reasoning with selected personas
    - comprehensive: Full analysis (legacy, same as reasoning_depth="comprehensive")

    Reasoning Depths (when mode="standard"):
    - quick: Senior engineer perspective only
    - standard: Senior + Product engineer perspectives  
    - comprehensive: All personas with full collaborative reasoning

    Use this tool for: "Should I build a custom auth system?", "Planning microservices architecture", 
    "What's the best approach for API integration?", "Continue previous discussion about caching"

    Args:
        query: Technical question or decision to discuss
        context: Additional context (code, architecture, requirements)
        session_id: Session ID to continue previous conversation
        reasoning_depth: Analysis depth - quick/standard/comprehensive (default: standard)
        continue_session: Whether to continue existing session (default: false)
        mode: Interaction mode - interrupt/standard (default: standard)
        phase: Development phase - planning/implementation/review (default: planning)
        confidence_threshold: Minimum confidence to trigger interrupt (default: 0.7)
        file_paths: Optional list of file paths to analyze (max 10 files, 1MB each)
        working_directory: Optional working directory for resolving relative paths
        
    Returns:
        Collaborative reasoning analysis with multi-perspective insights or quick interrupt
    """
    logger.info(f"Vibe mentor activated: mode={mode}, depth={reasoning_depth}, phase={phase} for query: {query[:100]}...")
    
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
