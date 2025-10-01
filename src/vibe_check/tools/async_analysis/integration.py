"""
Async Analysis Integration

High-level integration functions that tie together queue management,
worker processing, and status tracking for seamless async analysis.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .config import AsyncAnalysisConfig, DEFAULT_ASYNC_CONFIG
from .queue_manager import get_global_queue, shutdown_global_queue
from .worker import get_global_worker_manager, shutdown_global_workers
from .status_tracker import StatusTracker

logger = logging.getLogger(__name__)

# Global components
_status_tracker: Optional[StatusTracker] = None
_system_initialized = False


async def initialize_async_system(config: AsyncAnalysisConfig = None) -> bool:
    """
    Initialize the async analysis system.

    Args:
        config: Optional configuration (uses default if None)

    Returns:
        True if initialization successful
    """
    global _status_tracker, _system_initialized

    if _system_initialized:
        return True

    try:
        config = config or DEFAULT_ASYNC_CONFIG

        # Initialize status tracker
        _status_tracker = StatusTracker(config)

        # Initialize queue
        queue = await get_global_queue()

        # Initialize workers
        await get_global_worker_manager(queue)

        _system_initialized = True
        logger.info("Async analysis system initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize async analysis system: {e}")
        return False


async def shutdown_async_system():
    """Shutdown the async analysis system gracefully."""
    global _status_tracker, _system_initialized

    if not _system_initialized:
        return

    try:
        # Shutdown workers first (to finish current jobs)
        await shutdown_global_workers()

        # Shutdown queue
        await shutdown_global_queue()

        _status_tracker = None
        _system_initialized = False

        logger.info("Async analysis system shutdown completed")

    except Exception as e:
        logger.error(f"Error during async system shutdown: {e}")


async def start_async_analysis(
    pr_number: int, repository: str, pr_data: Dict[str, Any], priority: int = 1
) -> Dict[str, Any]:
    """
    Start async analysis for a massive PR.

    Args:
        pr_number: GitHub PR number
        repository: Repository in format "owner/repo"
        pr_data: PR metadata from GitHub API
        priority: Job priority (lower = higher priority)

    Returns:
        Response with job_id and status information
    """
    # Validate input first
    from .validation import validate_async_analysis_request

    is_valid, validation_result = validate_async_analysis_request(
        pr_number, repository, pr_data
    )
    if not is_valid:
        return {
            "status": "error",
            "error": f"Validation failed for {validation_result['field']}: {validation_result['error']}",
            "validation_error": validation_result,
            "recommendation": "Fix the invalid input and try again",
        }

    # Use sanitized values from validation
    pr_number = validation_result["pr_number"]
    repository = validation_result["repository"]
    pr_data = validation_result["pr_data"]

    # Ensure system is initialized
    if not await initialize_async_system():
        return {
            "status": "error",
            "error": "Failed to initialize async analysis system",
            "recommendation": "Try again later or use manual review",
        }

    try:
        # Get queue
        queue = await get_global_queue()

        # Check if PR is suitable for async processing
        config = DEFAULT_ASYNC_CONFIG
        if not config.should_use_async_processing(pr_data):
            return {
                "status": "not_suitable",
                "message": "PR is not large enough for async processing",
                "recommendation": "Use standard or chunked analysis instead",
                "pr_size_info": {
                    "total_changes": pr_data.get("additions", 0)
                    + pr_data.get("deletions", 0),
                    "changed_files": pr_data.get("changed_files", 0),
                    "async_threshold_lines": config.async_threshold_lines,
                    "async_threshold_files": config.async_threshold_files,
                },
            }

        # Start resource monitoring if not already running
        from .resource_monitor import get_global_resource_monitor

        resource_monitor = get_global_resource_monitor()
        await resource_monitor.start_monitoring()

        # Queue the analysis
        job_id = await queue.queue_analysis(pr_number, repository, pr_data, priority)

        # Get initial status
        status_info = _status_tracker.get_comprehensive_status(job_id, queue)

        # Generate immediate response with basic analysis
        immediate_analysis = _generate_immediate_analysis(pr_data)

        return {
            "status": "queued_for_async_analysis",
            "job_id": job_id,
            "message": f"Large PR ({pr_data.get('changed_files', 0)} files, {pr_data.get('additions', 0) + pr_data.get('deletions', 0)} lines) queued for comprehensive background analysis.",
            # Status information
            "queue_status": status_info,
            # Immediate basic analysis
            "immediate_analysis": immediate_analysis,
            # Instructions for user
            "instructions": {
                "check_status": f"Check analysis progress with job ID: {job_id}",
                "estimated_completion": status_info.get("timing", {}).get(
                    "estimated_completion_timestamp"
                ),
                "how_to_check": "Use the check_analysis_status tool with this job_id",
            },
        }

    except asyncio.QueueFull:
        return {
            "status": "queue_full",
            "error": "Analysis queue is currently at capacity",
            "recommendation": "Try again in a few minutes or use manual review",
            "queue_info": (await get_global_queue()).get_queue_status(),
        }
    except Exception as e:
        # Handle ResourceError from queue_manager
        from .queue_manager import ResourceError

        if isinstance(e, ResourceError):
            return {
                "status": "resource_limit_exceeded",
                "error": str(e),
                "recommendation": "System is at capacity. Try again later or use manual review",
                "resource_info": "Resource monitoring detected system limits exceeded",
            }
        logger.error(f"Error starting async analysis: {e}")
        return {
            "status": "error",
            "error": f"Failed to queue analysis: {str(e)}",
            "recommendation": "Use manual review for this PR",
        }


async def check_analysis_status(job_id: str) -> Dict[str, Any]:
    """
    Check the status of an async analysis job.

    Args:
        job_id: Job identifier from start_async_analysis

    Returns:
        Comprehensive status information
    """
    # Validate job ID first
    from .validation import validate_status_check_request

    is_valid, validation_result = validate_status_check_request(job_id)
    if not is_valid:
        return {
            "status": "error",
            "error": f"Invalid job ID: {validation_result['error']}",
            "job_id": job_id,
        }

    # Use sanitized job ID
    job_id = validation_result["job_id"]

    # Ensure system is initialized
    if not await initialize_async_system():
        return {"status": "error", "error": "Async analysis system not available"}

    try:
        queue = await get_global_queue()

        # Get comprehensive status
        status_info = _status_tracker.get_comprehensive_status(job_id, queue)

        if not status_info:
            return {
                "status": "not_found",
                "job_id": job_id,
                "error": "Job not found - it may have expired or never existed",
                "suggestion": "Check the job_id or start a new analysis",
            }

        # Add result if completed
        if status_info["status"] == "completed":
            result = queue.get_result(job_id)
            if result:
                status_info["analysis_result"] = result

        return {"status": "status_retrieved", "job_status": status_info}

    except Exception as e:
        logger.error(f"Error checking analysis status: {e}")
        return {
            "status": "error",
            "error": f"Failed to check status: {str(e)}",
            "job_id": job_id,
        }


async def get_system_status() -> Dict[str, Any]:
    """
    Get overall async analysis system status.

    Returns:
        System status and metrics
    """
    if not _system_initialized:
        return {
            "system_status": "not_initialized",
            "message": "Async analysis system is not running",
        }

    # Use graceful degradation for system status
    from .graceful_degradation import system_status_with_fallback

    return await system_status_with_fallback()


def _generate_immediate_analysis(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate immediate basic analysis while detailed analysis is queued.

    Args:
        pr_data: PR metadata

    Returns:
        Basic analysis with immediate insights
    """
    total_changes = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)

    # Basic categorization
    if total_changes > 5000:
        size_category = "massive"
        complexity_note = "Major architectural changes likely"
    elif total_changes > 2000:
        size_category = "very_large"
        complexity_note = "Significant refactoring or feature addition"
    else:
        size_category = "large"
        complexity_note = "Substantial changes requiring detailed review"

    # File distribution analysis
    avg_changes_per_file = total_changes / max(changed_files, 1)
    if avg_changes_per_file > 200:
        distribution = "concentrated_changes"
        distribution_note = "Large changes in few files - possibly new features"
    elif avg_changes_per_file < 50:
        distribution = "distributed_changes"
        distribution_note = "Small changes across many files - possibly refactoring"
    else:
        distribution = "balanced_changes"
        distribution_note = "Moderate changes spread across files"

    return {
        "size_analysis": {
            "category": size_category,
            "total_changes": total_changes,
            "changed_files": changed_files,
            "avg_changes_per_file": avg_changes_per_file,
            "complexity_note": complexity_note,
        },
        "distribution_analysis": {"pattern": distribution, "note": distribution_note},
        "immediate_recommendations": [
            "Plan for extended review time due to PR size",
            "Consider breaking into smaller PRs for future changes",
            "Focus on architectural and security implications first",
            "Ensure comprehensive testing before deployment",
        ],
        "review_strategy": {
            "approach": "architectural_first",
            "focus_areas": [
                "breaking_changes",
                "security_implications",
                "performance_impact",
            ],
            "estimated_review_time": f"{(total_changes // 500) * 15}-{(total_changes // 500) * 30} minutes",
        },
    }


# Convenience function for external use
async def stop_async_workers():
    """Stop async workers (for testing or shutdown)."""
    await shutdown_global_workers()
