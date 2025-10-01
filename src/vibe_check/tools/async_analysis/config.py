"""
Configuration for Async Analysis System

Centralized configuration for background processing of massive PRs.
All timeouts, thresholds, and performance parameters are defined here.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AsyncAnalysisConfig:
    """Configuration for async PR analysis system."""

    # Queue Configuration
    max_queue_size: int = 50  # Maximum jobs in queue
    max_concurrent_workers: int = 2  # Max parallel analysis workers
    worker_idle_timeout: int = 30  # Seconds to wait for new jobs

    # Analysis Timeouts (longer for background processing)
    chunk_timeout_seconds: int = 300  # 5 minutes per chunk for background
    max_analysis_duration: int = 1200  # 20 minutes maximum per PR
    status_update_interval: int = 10  # Status update frequency

    # Chunking Strategy for Large PRs
    large_pr_chunk_size: int = 1000  # Larger chunks for background processing
    max_chunks_per_pr: int = 20  # Safety limit on chunk count

    # Storage and Retention
    result_retention_hours: int = 24  # Keep results for 24 hours
    status_retention_hours: int = 48  # Keep status longer for debugging
    cleanup_interval_minutes: int = 60  # How often to clean old results

    # Thresholds for Async Processing
    async_threshold_lines: int = 1500  # Lines to trigger async processing
    async_threshold_files: int = 30  # Files to trigger async processing

    # Progress Tracking
    progress_checkpoints: Dict[str, int] = None

    def __post_init__(self):
        """Set default progress checkpoints."""
        if self.progress_checkpoints is None:
            self.progress_checkpoints = {
                "queued": 0,
                "started": 10,
                "chunking_complete": 20,
                "analysis_in_progress": 30,  # Will increment during chunk processing
                "merging_results": 90,
                "completed": 100,
            }

    def estimate_duration(self, pr_data: Dict[str, Any]) -> int:
        """
        Estimate analysis duration based on PR complexity.

        Args:
            pr_data: PR metadata with additions, deletions, changed_files

        Returns:
            Estimated duration in seconds
        """
        base_time = 180  # 3 minutes base

        # Add time based on size
        total_changes = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
        file_time = (total_changes // 1000) * 60  # 1 minute per 1000 lines

        # Add time based on files
        files_time = pr_data.get("changed_files", 0) * 5  # 5 seconds per file

        # Cap at maximum duration
        estimated = min(base_time + file_time + files_time, self.max_analysis_duration)

        return estimated

    def should_use_async_processing(self, pr_data: Dict[str, Any]) -> bool:
        """
        Determine if PR should use async processing.

        Args:
            pr_data: PR metadata

        Returns:
            True if PR should be processed asynchronously
        """
        total_changes = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
        changed_files = pr_data.get("changed_files", 0)

        return (
            total_changes > self.async_threshold_lines
            or changed_files > self.async_threshold_files
        )


# Default configuration instance
DEFAULT_ASYNC_CONFIG = AsyncAnalysisConfig()


class AsyncAnalysisMetrics:
    """Metrics tracking for async analysis system."""

    def __init__(self):
        self.jobs_queued = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.total_analysis_time = 0.0
        self.average_chunk_time = 0.0
        self.queue_length_history = []

    def record_job_queued(self):
        """Record a new job being queued."""
        self.jobs_queued += 1

    def record_job_completed(self, duration: float):
        """Record a job completion."""
        self.jobs_completed += 1
        self.total_analysis_time += duration

    def record_job_failed(self):
        """Record a job failure."""
        self.jobs_failed += 1

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        total = self.jobs_completed + self.jobs_failed
        if total == 0:
            return 100.0
        return (self.jobs_completed / total) * 100.0

    def get_average_duration(self) -> float:
        """Calculate average analysis duration."""
        if self.jobs_completed == 0:
            return 0.0
        return self.total_analysis_time / self.jobs_completed

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "jobs_queued": self.jobs_queued,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "success_rate_percent": self.get_success_rate(),
            "average_duration_seconds": self.get_average_duration(),
            "total_analysis_time": self.total_analysis_time,
        }


# Global metrics instance
ASYNC_METRICS = AsyncAnalysisMetrics()
