"""Public API functions for issue analysis."""

import asyncio
import copy
import logging
from datetime import UTC, datetime
from typing import Dict, Any, Optional

from vibe_check.core.educational_content import DetailLevel
from ..legacy.vibe_check_framework import (
    VibeCheckMode,
    VibeCheckResult,
    get_vibe_check_framework,
)

from .analyzer import EnhancedGitHubIssueAnalyzer, EXTERNAL_CLAUDE_AVAILABLE

logger = logging.getLogger(__name__)

# Initialize global analyzer instance
_enhanced_github_analyzer = None


def get_enhanced_github_analyzer(
    github_token: Optional[str] = None, enable_claude_cli: bool = True
) -> EnhancedGitHubIssueAnalyzer:
    """Get or create enhanced GitHub analyzer instance."""
    global _enhanced_github_analyzer
    if _enhanced_github_analyzer is None:
        _enhanced_github_analyzer = EnhancedGitHubIssueAnalyzer(
            github_token, enable_claude_cli
        )
    return _enhanced_github_analyzer


def get_github_analyzer(
    github_token: Optional[str] = None,
) -> EnhancedGitHubIssueAnalyzer:
    """Get or create GitHub analyzer instance (backward compatibility)."""
    return get_enhanced_github_analyzer(github_token, enable_claude_cli=False)


async def _analyze_issue_async(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "hybrid",
    detail_level: str = "standard",
    post_comment: bool = False,
) -> Dict[str, Any]:
    """
    Enhanced GitHub issue analysis with optional ExternalClaudeCli integration.

    This enhanced version provides multiple analysis modes:
    - "basic": Fast pattern detection only (backward compatible)
    - "comprehensive": Claude CLI powered sophisticated reasoning
    - "hybrid": Combined pattern detection + Claude CLI insights (recommended)

    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo" (optional, defaults to current repo)
        analysis_mode: Analysis mode - "basic", "comprehensive", or "hybrid" (default: "hybrid")
        detail_level: Educational detail level - "brief"/"standard"/"comprehensive" (default: "standard")
        post_comment: Whether to post analysis as GitHub comment (future enhancement)

    Returns:
        Comprehensive issue analysis with optional Claude CLI enhancement

    Example:
        # Fast pattern detection only (backward compatible)
        result = await analyze_issue_async(22, analysis_mode="basic")

        # Comprehensive Claude CLI analysis
        result = await analyze_issue_async(123, "owner/repo", "comprehensive")

        # Hybrid analysis (recommended) - combines both approaches
        result = await analyze_issue_async(456, analysis_mode="hybrid")
    """
    try:
        # Get enhanced analyzer
        analyzer = get_enhanced_github_analyzer()

        # Normalize analysis mode to support legacy aliases
        requested_mode = analysis_mode.lower() if analysis_mode else "hybrid"
        mode_aliases = {
            "quick": "basic",
            "fast": "basic",
            "legacy": "basic",
            "detailed": "comprehensive",
        }
        mode = mode_aliases.get(requested_mode, requested_mode)
        if mode not in ["basic", "comprehensive", "hybrid"]:
            logger.warning(
                f"Invalid analysis mode '{analysis_mode}', using 'hybrid'"
            )
            mode = "hybrid"

        # Normalize detail level so downstream code always receives a string
        if isinstance(detail_level, DetailLevel):
            normalized_detail_level: Optional[str] = detail_level.value
        elif detail_level is None:
            normalized_detail_level = None
        else:
            normalized_detail_level = str(detail_level)

        # Execute analysis based on mode
        if mode == "basic":
            logger.info(
                f"Running basic pattern detection analysis for issue #{issue_number}"
            )
            result = await analyzer.analyze_issue_basic(
                issue_number=issue_number,
                repository=repository,
                detail_level=normalized_detail_level or "standard",
            )
        elif mode == "comprehensive":
            logger.info(
                f"Running comprehensive Claude CLI analysis for issue #{issue_number}"
            )
            result = await analyzer.analyze_issue_comprehensive(
                issue_number=issue_number,
                repository=repository,
                detail_level=normalized_detail_level or "standard",
            )
        else:  # hybrid
            logger.info(f"Running hybrid analysis for issue #{issue_number}")
            result = await analyzer.analyze_issue_hybrid(
                issue_number=issue_number,
                repository=repository,
                detail_level=normalized_detail_level or "standard",
            )

        # Add enhancement metadata
        result["enhanced_analysis"] = {
            "analysis_mode": mode,
            "external_claude_available": EXTERNAL_CLAUDE_AVAILABLE,
            "claude_cli_enabled": analyzer.claude_cli_enabled,
            "enhancement_version": "1.0 - Issue #65 implementation",
            "backward_compatible": True,
        }

        # Future enhancement: post_comment functionality
        if post_comment:
            logger.info("Comment posting not yet implemented - future enhancement")
            result["comment_posting"] = {
                "requested": True,
                "status": "not_implemented",
                "note": "Future enhancement - will integrate with vibe check framework",
            }

        return result

    except Exception as e:
        error_msg = f"Enhanced issue analysis failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "status": "enhanced_analysis_error",
            "issue_number": issue_number,
            "repository": repository,
            "analysis_mode": analysis_mode,
            "external_claude_available": EXTERNAL_CLAUDE_AVAILABLE,
            "fallback_recommendation": "Try basic analysis mode",
        }


def _normalize_async_mode(mode: Optional[str]) -> str:
    """Normalize user-facing modes to async-compatible values."""
    normalized = (mode or "hybrid").lower()
    if normalized == "quick":
        return "basic"
    if normalized not in {"basic", "comprehensive", "hybrid"}:
        return "hybrid"
    return normalized


def _build_vibe_check_payload(
    vibe_result: VibeCheckResult, detail_level: str, mode: str
) -> Dict[str, Any]:
    """Convert VibeCheckResult into API-friendly response."""
    timestamp = datetime.now(UTC).isoformat()
    technical_analysis = copy.deepcopy(vibe_result.technical_analysis)

    response: Dict[str, Any] = {
        "status": "vibe_check_complete",
        "analysis_timestamp": timestamp,
        "vibe_check": {
            "overall_vibe": vibe_result.overall_vibe,
            "vibe_level": vibe_result.vibe_level.value,
            "friendly_summary": vibe_result.friendly_summary,
            "coaching_recommendations": list(vibe_result.coaching_recommendations),
        },
        "technical_analysis": technical_analysis,
        "enhanced_features": {
            "claude_reasoning": vibe_result.claude_reasoning is not None,
            "clear_thought_analysis": vibe_result.clear_thought_analysis is not None,
            "educational_coaching": True,
            "friendly_language": True,
            "comprehensive_validation": mode == "comprehensive",
        },
    }

    if vibe_result.claude_reasoning:
        response["vibe_check"]["claude_reasoning"] = vibe_result.claude_reasoning
        response["claude_reasoning"] = vibe_result.claude_reasoning
    if vibe_result.clear_thought_analysis:
        response["vibe_check"]["clear_thought_analysis"] = vibe_result.clear_thought_analysis
        response["clear_thought_analysis"] = vibe_result.clear_thought_analysis

    metadata = technical_analysis.setdefault("analysis_metadata", {})
    metadata.setdefault("detail_level", detail_level)
    return response


def _run_vibe_check_sync(
    issue_number: int,
    repository: Optional[str],
    detail_level: str,
    mode: str,
    post_comment: bool,
) -> Dict[str, Any]:
    """Execute legacy vibe check synchronously."""
    try:
        framework = get_vibe_check_framework()
    except Exception as exc:
        return {
            "status": "vibe_check_error",
            "error": str(exc),
            "friendly_error": "🚨 Oops! Something went wrong with the vibe check. Try again once the framework is available.",
            "issue_number": issue_number,
        }

    try:
        detail_enum = DetailLevel(detail_level.lower())
    except ValueError:
        detail_enum = DetailLevel.STANDARD

    vibe_mode = (
        VibeCheckMode.COMPREHENSIVE
        if mode == "comprehensive"
        else VibeCheckMode.QUICK
    )

    vibe_result = framework.check_issue_vibes(
        issue_number=issue_number,
        repository=repository,
        mode=vibe_mode,
        detail_level=detail_enum,
        post_comment=post_comment,
    )
    response = _build_vibe_check_payload(vibe_result, detail_level, mode)
    response["issue_info"] = {
        "number": issue_number,
        "repository": repository,
        "analysis_mode": mode,
        "detail_level": detail_level,
        "comment_posted": post_comment,
    }
    return response


async def analyze_issue_async(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "hybrid",
    detail_level: str = "standard",
    post_comment: bool = False,
) -> Dict[str, Any]:
    """Public coroutine wrapper for async workflows."""
    requested_mode = (analysis_mode or "hybrid").lower()
    if requested_mode in {"quick", "comprehensive", "hybrid"}:
        return await asyncio.to_thread(
            _run_vibe_check_sync,
            issue_number,
            repository,
            detail_level,
            requested_mode,
            post_comment,
        )

    return await _analyze_issue_async(
        issue_number=issue_number,
        repository=repository,
        analysis_mode=_normalize_async_mode(analysis_mode),
        detail_level=detail_level,
        post_comment=post_comment,
    )


def analyze_issue(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "hybrid",
    detail_level: str = "standard",
    post_comment: bool = False,
) -> Dict[str, Any]:
    """
    Run issue analysis synchronously.

    For async usage, call analyze_issue_async() directly.

    Note:
        Nested event loops are not supported (Python limitation).
        If you need async, use analyze_issue_async() instead.
    """
    requested_mode = (analysis_mode or "hybrid").lower()

    # Vibe check modes use synchronous execution
    if requested_mode in {"quick", "comprehensive", "hybrid"}:
        return _run_vibe_check_sync(
            issue_number=issue_number,
            repository=repository,
            detail_level=detail_level,
            mode=requested_mode,
            post_comment=post_comment,
        )

    # Basic/enhanced modes use async execution
    normalized_mode = _normalize_async_mode(analysis_mode)
    return asyncio.run(
        _analyze_issue_async(
            issue_number=issue_number,
            repository=repository,
            analysis_mode=normalized_mode,
            detail_level=detail_level,
            post_comment=post_comment,
        )
    )


def analyze_issue_legacy(
    issue_number: int,
    repository: Optional[str] = None,
    analysis_mode: str = "quick",
    detail_level: str = "standard",
    post_comment: bool = False,
) -> Dict[str, Any]:
    """
    Legacy analyze_issue function for backward compatibility.

    Args:
        issue_number: GitHub issue number to analyze
        repository: Repository in format "owner/repo"
        analysis_mode: Analysis mode - "quick" or "comprehensive"
        detail_level: Educational detail level
        post_comment: Whether to post analysis as GitHub comment

    Returns:
        Issue analysis results
    """
    return analyze_issue(
        issue_number=issue_number,
        repository=repository,
        analysis_mode=analysis_mode,
        detail_level=detail_level,
        post_comment=post_comment,
    )
