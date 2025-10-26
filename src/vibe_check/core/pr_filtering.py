"""
PR Filtering and Size Analysis

Intelligent pre-filtering logic to determine when to use LLM analysis
vs fallback to fast analysis based on PR size and complexity.
Implements Phase 1 of issue #101.
"""

import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class MetricsHooks:
    """
    Monitoring hooks for tracking fallback usage patterns.

    These hooks can be implemented to send metrics to monitoring systems
    like Prometheus, DataDog, or CloudWatch for production tracking.
    """

    @staticmethod
    def track_filtering_decision(
        pr_data: Dict[str, Any], filter_result: "PRFilterResult"
    ):
        """Track PR filtering decisions for monitoring."""
        # Example: logger.info(f"metrics.pr_filtering.decision", extra={...})
        logger.info(
            "PR filtering decision tracked",
            extra={
                "pr_size": filter_result.size_metrics.get("total_changes", 0),
                "pr_files": filter_result.size_metrics.get("changed_files", 0),
                "used_llm": filter_result.should_use_llm,
                "reason": filter_result.reason,
                "fallback_strategy": filter_result.fallback_strategy,
            },
        )

    @staticmethod
    def track_fallback_usage(
        fallback_type: str, pr_data: Dict[str, Any], error_context: Optional[str] = None
    ):
        """Track when fallback analysis is used."""
        logger.info(
            "Fallback analysis used",
            extra={
                "fallback_type": fallback_type,  # "size_filtered", "llm_failed", "complete_failure"
                "pr_number": pr_data.get("number", "unknown"),
                "error_context": error_context,
            },
        )

    @staticmethod
    def track_analysis_success(analysis_type: str, pr_data: Dict[str, Any]):
        """Track successful analysis completions."""
        logger.info(
            "Analysis completed successfully",
            extra={
                "analysis_type": analysis_type,  # "llm", "fast", "fallback"
                "pr_number": pr_data.get("number", "unknown"),
            },
        )


# Configuration constants for filtering thresholds
# These can be adjusted based on production metrics and performance data
class FilteringConfig:
    """Configuration constants for PR filtering thresholds."""

    # Maximum lines changed before skipping LLM analysis
    MAX_LINES_FOR_LLM = 1000

    # Maximum files changed before skipping LLM analysis
    MAX_FILES_FOR_LLM = 20

    # Threshold for detecting wide refactoring patterns
    # (many files with moderate changes that often timeout)
    REFACTORING_FILE_THRESHOLD = 15
    REFACTORING_LINES_THRESHOLD = 500

    # Ratio threshold for detecting mass changes (many files, few lines each)
    MASS_CHANGE_RATIO_THRESHOLD = 0.1


@dataclass
class PRFilterResult:
    """Result of PR filtering analysis."""

    should_use_llm: bool
    reason: str
    fallback_strategy: str
    size_metrics: Dict[str, Any]


def should_use_llm_analysis(
    pr_data: Dict[str, Any], track_metrics: bool = True
) -> PRFilterResult:
    """
    Determine if PR should use LLM analysis or fallback to fast analysis.

    This implements intelligent pre-filtering to prevent Claude CLI timeouts
    and ensure the system never fails completely.

    Args:
        pr_data: PR data containing additions, deletions, changed_files, etc.

    Returns:
        PRFilterResult with decision and reasoning
    """
    # Extract size metrics
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)
    total_changes = additions + deletions

    # Calculate size metrics
    size_metrics = {
        "total_changes": total_changes,
        "additions": additions,
        "deletions": deletions,
        "changed_files": changed_files,
        "files_per_change_ratio": changed_files / max(total_changes, 1),
    }

    # Decision logic based on issue #101 requirements

    # Skip LLM if too many lines changed
    if total_changes > FilteringConfig.MAX_LINES_FOR_LLM:
        result = PRFilterResult(
            should_use_llm=False,
            reason=f"Large PR: {total_changes} lines changed (threshold: {FilteringConfig.MAX_LINES_FOR_LLM})",
            fallback_strategy="fast_analysis_with_guidance",
            size_metrics=size_metrics,
        )
        if track_metrics:
            MetricsHooks.track_filtering_decision(pr_data, result)
        return result

    # Skip LLM if too many files changed
    if changed_files > FilteringConfig.MAX_FILES_FOR_LLM:
        result = PRFilterResult(
            should_use_llm=False,
            reason=f"Many files changed: {changed_files} files (threshold: {FilteringConfig.MAX_FILES_FOR_LLM})",
            fallback_strategy="fast_analysis_with_guidance",
            size_metrics=size_metrics,
        )
        if track_metrics:
            MetricsHooks.track_filtering_decision(pr_data, result)
        return result

    # Additional heuristic: Skip if very wide changes (many files, few lines each)
    # This often indicates refactoring or mass changes that timeout LLM analysis
    if (
        changed_files > FilteringConfig.REFACTORING_FILE_THRESHOLD
        and total_changes > FilteringConfig.REFACTORING_LINES_THRESHOLD
    ):
        result = PRFilterResult(
            should_use_llm=False,
            reason=f"Wide changes: {changed_files} files with {total_changes} lines (refactoring pattern)",
            fallback_strategy="fast_analysis_with_guidance",
            size_metrics=size_metrics,
        )
        if track_metrics:
            MetricsHooks.track_filtering_decision(pr_data, result)
        return result

    # Use LLM analysis for smaller PRs
    result = PRFilterResult(
        should_use_llm=True,
        reason=f"Suitable for LLM: {total_changes} lines, {changed_files} files",
        fallback_strategy="not_needed",
        size_metrics=size_metrics,
    )

    # Track metrics if enabled
    if track_metrics:
        MetricsHooks.track_filtering_decision(pr_data, result)

    return result


def create_large_pr_response(
    pr_data: Dict[str, Any], filter_result: PRFilterResult
) -> Dict[str, Any]:
    """
    Create a helpful response for PRs that are too large for LLM analysis.

    This ensures the system always provides useful feedback even when
    skipping LLM analysis due to size constraints.

    Args:
        pr_data: Original PR data
        filter_result: Result from should_use_llm_analysis

    Returns:
        Response with helpful guidance for large PRs
    """
    total_changes = filter_result.size_metrics["total_changes"]
    changed_files = filter_result.size_metrics["changed_files"]

    return {
        "status": "large_pr_detected",
        "analysis_mode": "pattern_detection_only",
        "large_pr_detected": True,
        "filter_reason": filter_result.reason,
        "message": f"Large PR detected ({changed_files} files, {total_changes} lines). Providing fast analysis instead of LLM analysis to ensure reliable response.",
        "recommendation": "Consider splitting into smaller PRs for detailed LLM review",
        "guidance": {
            "splitting_strategy": _generate_splitting_guidance(
                filter_result.size_metrics
            ),
            "review_approach": "Focus on architectural changes and high-risk areas first",
            "next_steps": [
                "Review the overall design approach",
                "Check for breaking changes",
                "Validate critical functionality",
                "Consider if changes can be broken into smaller, focused PRs",
            ],
        },
        "size_metrics": filter_result.size_metrics,
    }


def _generate_splitting_guidance(size_metrics: Dict[str, Any]) -> list:
    """Generate specific guidance for splitting large PRs."""
    guidance = []

    total_changes = size_metrics["total_changes"]
    changed_files = size_metrics["changed_files"]

    if changed_files > FilteringConfig.MAX_FILES_FOR_LLM:
        guidance.append("Split by functional area - group related files together")
        guidance.append("Separate refactoring changes from feature changes")

    if total_changes > FilteringConfig.MAX_LINES_FOR_LLM:
        guidance.append("Break into logical commits that can stand alone")
        guidance.append("Consider feature flags for incremental rollout")

    if (
        size_metrics.get("files_per_change_ratio", 0)
        > FilteringConfig.MASS_CHANGE_RATIO_THRESHOLD
    ):
        guidance.append(
            "This appears to be a mass refactoring - consider automation tools"
        )
        guidance.append("Split into preparation PRs and the main change")

    return guidance or ["Consider splitting by feature or component boundaries"]


async def analyze_with_fallback(
    pr_data: Dict[str, Any], llm_analyzer_func, fast_analyzer_func, **analyzer_kwargs
) -> Dict[str, Any]:
    """
    Orchestrate PR analysis with intelligent fallback and graceful degradation.

    This ensures the system **never** fails completely and always returns
    useful analysis, implementing the core requirement of issue #101.

    Args:
        pr_data: PR data for size analysis
        llm_analyzer_func: Function to call for LLM analysis
        fast_analyzer_func: Function to call for fast analysis
        **analyzer_kwargs: Additional arguments for analyzer functions

    Returns:
        Analysis result with graceful degradation on any failure
    """
    filter_result = should_use_llm_analysis(pr_data)

    try:
        if filter_result.should_use_llm:
            # Try LLM analysis for smaller PRs
            logger.info(f"Using LLM analysis: {filter_result.reason}")

            try:
                result = await llm_analyzer_func(**analyzer_kwargs)

                # Track successful LLM analysis
                MetricsHooks.track_analysis_success("llm", pr_data)

                # Add filtering context to successful LLM result
                if isinstance(result, dict):
                    result.update(
                        {
                            "analysis_method": "llm_analysis",
                            "filter_result": {
                                "reason": filter_result.reason,
                                "size_metrics": filter_result.size_metrics,
                            },
                        }
                    )

                return result

            except Exception as llm_error:
                logger.warning(
                    f"LLM analysis failed, falling back to fast analysis: {llm_error}"
                )

                # Track LLM failure fallback
                MetricsHooks.track_fallback_usage("llm_failed", pr_data, str(llm_error))

                # Fall back to fast analysis with error context
                fast_result = fast_analyzer_func(**analyzer_kwargs)
                MetricsHooks.track_analysis_success("fast", pr_data)

                if isinstance(fast_result, dict):
                    fast_result.update(
                        {
                            "status": "partial_analysis",
                            "analysis_mode": "pattern_detection_only",
                            "llm_analysis_error": str(llm_error),
                            "fallback_reason": "LLM analysis failed, using fast analysis",
                        }
                    )
                return fast_result
        else:
            # Skip LLM analysis for large PRs
            logger.info(f"Skipping LLM analysis: {filter_result.reason}")

            # Track size-based filtering
            MetricsHooks.track_fallback_usage(
                "size_filtered", pr_data, filter_result.reason
            )

            # Use fast analysis with large PR guidance
            fast_result = fast_analyzer_func(**analyzer_kwargs)
            MetricsHooks.track_analysis_success("fast", pr_data)

            if isinstance(fast_result, dict):
                # Enhance fast result with large PR context
                large_pr_context = create_large_pr_response(pr_data, filter_result)
                fast_result.update(large_pr_context)

            return fast_result

    except Exception as e:
        # Ultimate fallback - always return something useful
        logger.error(f"Complete analysis failure, using minimal fallback: {e}")

        # Track complete failure
        MetricsHooks.track_fallback_usage("complete_failure", pr_data, str(e))

        return {
            "status": "error_fallback",
            "analysis_mode": "minimal_fallback",
            "error": str(e),
            "message": "Analysis encountered errors but providing basic information",
            "fallback_data": {
                "pr_number": pr_data.get("number", "unknown"),
                "title": pr_data.get("title", "Unknown"),
                "size_metrics": (
                    filter_result.size_metrics if "filter_result" in locals() else {}
                ),
                "recommendation": "Manual review recommended due to analysis errors",
            },
            "note": "System ensured response despite errors - this implements graceful degradation",
        }
