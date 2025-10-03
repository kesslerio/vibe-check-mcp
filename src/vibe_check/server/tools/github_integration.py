import logging
import logging
from typing import Any, Dict
from vibe_check.server.core import mcp
from vibe_check.tools.analyze_issue_nollm import (
    analyze_issue as analyze_github_issue_tool,
)
from vibe_check.tools.analyze_pr_nollm import (
    analyze_pr_nollm as analyze_pr_nollm_function,
)
from vibe_check.tools.pr_review import review_pull_request

logger = logging.getLogger(__name__)


def register_github_tools(mcp_instance):
    """Registers GitHub tools with the MCP server."""
    _register_tool(mcp_instance, analyze_issue_nollm)
    _register_tool(mcp_instance, analyze_pr_nollm)
    _register_tool(mcp_instance, review_pr_comprehensive)


def _register_tool(mcp_instance, tool) -> None:
    manager = getattr(mcp_instance, "_tool_manager", None)
    tool_name = getattr(tool, "__name__", getattr(tool, "name", None))

    if manager and hasattr(manager, "_tools"):
        if tool_name in manager._tools:
            return

    mcp_instance.add_tool(tool)


@mcp.tool(name="analyze_issue_nollm")
def analyze_issue_nollm(
    issue_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = None,
) -> Dict[str, Any]:
    """
    🚀 Fast GitHub issue analysis using direct pattern detection (no LLM calls).

    Direct GitHub issue analysis with pattern detection and GitHub API data.
    Perfect for "quick vibe check issue", "fast issue analysis", and development workflow.
    For comprehensive LLM-powered analysis, use analyze_issue_llm instead.

    Features:
    - 🚀 Fast pattern detection on GitHub issues
    - 🎯 Direct GitHub API integration
    - 🔍 Basic anti-pattern detection
    - 📊 Issue metrics and validation

    Use this tool for: "quick vibe check issue 23", "fast analysis issue 42", "basic issue check"

    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        analysis_mode: "quick" for fast pattern detection
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
        post_comment: Post analysis as GitHub comment (disabled by default for fast mode)

    Returns:
        Fast GitHub issue analysis with basic recommendations
    """
    # Auto-enable comment posting for comprehensive mode unless explicitly disabled
    if post_comment is None:
        post_comment = analysis_mode == "comprehensive"

    logger.info(
        f"GitHub issue analysis ({analysis_mode}): #{issue_number} in {repository}"
    )
    return analyze_github_issue_tool(
        issue_number=issue_number,
        repository=repository,
        analysis_mode=analysis_mode,
        detail_level=detail_level,
        post_comment=post_comment,
    )


@mcp.tool(name="analyze_pr_nollm")
def analyze_pr_nollm(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    analysis_mode: str = "quick",
    detail_level: str = "standard",
) -> Dict[str, Any]:
    """
    🚀 Fast PR analysis using direct pattern detection (no LLM calls).

    Direct PR analysis with metrics, pattern detection, and GitHub API data.
    Perfect for "quick PR check", "fast PR analysis", and development workflow.
    For comprehensive LLM-powered analysis, use analyze_pr_llm instead.

    Features:
    - 🚀 Fast PR metrics and pattern detection
    - 🎯 Direct GitHub API integration
    - 📊 PR size classification and file analysis
    - 🔍 Basic anti-pattern detection
    - 📋 Issue linkage validation

    Use this tool for: "quick PR check 44", "fast analysis PR 42", "basic PR review"

    Args:
        pr_number: PR number to analyze
        repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
        analysis_mode: "quick" for fast analysis
        detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")

    Returns:
        Fast PR analysis with basic recommendations
    """
    logger.info(
        f"Fast PR analysis requested: #{pr_number} in {repository} (mode: {analysis_mode})"
    )
    return analyze_pr_nollm_function(
        pr_number=pr_number,
        repository=repository,
        analysis_mode=analysis_mode,
        detail_level=detail_level,
    )


@mcp.tool(name="review_pr_comprehensive")
async def review_pr_comprehensive(
    pr_number: int,
    repository: str = "kesslerio/vibe-check-mcp",
    force_re_review: bool = False,
    analysis_mode: str = "comprehensive",
    detail_level: str = "standard",
    model: str = "sonnet",
) -> Dict[str, Any]:
    """
    🧠 Advanced PR review with file type analysis and model selection.

    Enhanced PR review tool with:
    - 📁 File type-specific analysis (TypeScript, Python, API endpoints, tests)
    - ⭐ First-time contributor awareness for encouraging feedback
    - 🔍 Security-focused review sections
    - 🧪 Test coverage analysis
    - 🎯 Model selection (sonnet/opus/haiku) for performance vs capability

    This is the enhanced modular PR review replacing the monolithic tool.

    Args:
        pr_number: PR number to review
        repository: Repository in format "owner/repo"
        force_re_review: Force re-review mode even if not auto-detected
        analysis_mode: "comprehensive" or "quick" analysis
        detail_level: "brief", "standard", or "comprehensive"
        model: Claude model - "sonnet" (default), "opus" (best), or "haiku" (fast)

    Returns:
        Comprehensive PR analysis with file type breakdown and recommendations
    """
    logger.info(
        f"🔍 Starting enhanced PR review for PR #{pr_number} with model: {model}"
    )

    return await review_pull_request(
        pr_number=pr_number,
        repository=repository,
        force_re_review=force_re_review,
        analysis_mode=analysis_mode,
        detail_level=detail_level,
        model=model,
    )
