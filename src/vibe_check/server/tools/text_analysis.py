import logging
from typing import Dict, Any
from ..core import mcp
from ...tools.analyze_text_nollm import analyze_text_demo
from ...tools.large_prompt_demo import demo_large_prompt_analysis

logger = logging.getLogger(__name__)

def register_text_analysis_tools(mcp_instance):
    """Registers text analysis tools with the MCP server."""
    mcp_instance.add_tool(analyze_text_nollm)
    mcp_instance.add_tool(demo_large_prompt_handling)

@mcp.tool()
def analyze_text_nollm(
    text: str, 
    detail_level: str = "standard",
    use_project_context: bool = True,
    project_root: str = "."
) -> Dict[str, Any]:
    """
    🚀 Fast text analysis using direct pattern detection with contextual awareness.

    Direct pattern detection and anti-pattern analysis without LLM reasoning,
    enhanced with project-specific context and library awareness.
    Perfect for "quick vibe check", "fast pattern analysis", and development workflow.
    For comprehensive LLM-powered analysis, use analyze_text_llm instead.

    Features:
    - 🚀 Fast pattern detection on any content
    - 🎯 Direct analysis without LLM dependencies  
    - 🤝 Basic coaching recommendations
    - 📊 Pattern detection with confidence scoring
    - 🔍 Project-aware analysis with library context (Issue #168)
    - 📚 Pattern exceptions and contextual recommendations

    Use this tool for: "quick vibe check this text", "fast pattern analysis", "basic text check"

    Args:
        text: Text content to analyze for anti-patterns
        detail_level: Educational detail level (brief/standard/comprehensive)
        use_project_context: Whether to automatically load project context (default: true)
        project_root: Root directory for project context loading (default: current directory)
        
    Returns:
        Fast pattern detection analysis results with contextual recommendations
    """
    logger.info(f"Fast text analysis requested for {len(text)} characters with context={use_project_context}")
    return analyze_text_demo(text, detail_level, use_project_context=use_project_context, project_root=project_root)

@mcp.tool()
def demo_large_prompt_handling(
    content: str,
    files: list = None,
    detail_level: str = "standard"
) -> Dict[str, Any]:
    """
    🚀 Demo: Zen-style Large Prompt Handling (Issue #164)
    
    Demonstrates the simple approach inspired by Zen MCP server for handling
    prompts that exceed MCP's 25K token limit. No complex infrastructure needed!
    
    How it works:
    1. Check if content >50K characters
    2. Ask Claude to save to file and resubmit
    3. Claude handles the file operations automatically
    4. Process the content normally
    
    This is a proof of concept for the minimal solution that replaces the
    overengineered 473-line approach from PR #157.
    
    Args:
        content: The content to analyze (if >50K chars, will request file mode)
        files: Optional list of file paths (when Claude resubmits with files)
        detail_level: Analysis detail level
        
    Returns:
        Either analysis results or instructions to use file mode
    """
    logger.info(f"Large prompt demo requested for {len(content)} characters")
    return demo_large_prompt_analysis(content, files, detail_level)
