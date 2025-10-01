"""
Async Analysis System for Massive PRs

Phase 4 of the vibe check reliability overhaul. Provides background processing
queue for PRs too large for chunked analysis, ensuring 100% PR coverage.

This module implements:
- AsyncAnalysisQueue: Job management and status tracking
- AsyncAnalysisWorker: Background processing with controlled concurrency
- StatusTracker: Real-time progress monitoring
- Integration with existing PR analysis flow

Usage:
    from vibe_check.tools.async_analysis import start_async_analysis

    analysis_id = await start_async_analysis(pr_number, repository, pr_data)
    status = await check_analysis_status(analysis_id)
"""

# Import only what's needed to avoid circular dependencies
from .config import AsyncAnalysisConfig, DEFAULT_ASYNC_CONFIG

__all__ = ["AsyncAnalysisConfig", "DEFAULT_ASYNC_CONFIG"]
