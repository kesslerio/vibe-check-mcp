"""
Async Analysis Queue Manager

Manages background processing queue for massive PRs, providing job tracking,
status monitoring, and result storage with configurable retention.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .config import AsyncAnalysisConfig, DEFAULT_ASYNC_CONFIG, ASYNC_METRICS

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of an analysis job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class AnalysisJob:
    """Represents an async analysis job."""
    job_id: str
    pr_number: int
    repository: str
    pr_data: Dict[str, Any]
    
    # Status tracking
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    worker_id: Optional[str] = None
    
    # Timing
    queued_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    estimated_completion: Optional[float] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Metadata
    created_by: str = "async_analysis_system"
    priority: int = 1  # Lower numbers = higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "pr_number": self.pr_number,
            "repository": self.repository,
            "status": self.status.value,
            "progress": self.progress,
            "worker_id": self.worker_id,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "estimated_completion": self.estimated_completion,
            "error_message": self.error_message,
            "created_by": self.created_by,
            "priority": self.priority,
            "pr_info": {
                "title": self.pr_data.get("title", "Unknown"),
                "additions": self.pr_data.get("additions", 0),
                "deletions": self.pr_data.get("deletions", 0),
                "changed_files": self.pr_data.get("changed_files", 0)
            }
        }


class AsyncAnalysisQueue:
    """
    Manages async analysis jobs with status tracking and result storage.
    
    Provides a complete job lifecycle management system for background
    processing of massive PRs that exceed chunked analysis thresholds.
    """
    
    def __init__(self, config: AsyncAnalysisConfig = None):
        self.config = config or DEFAULT_ASYNC_CONFIG
        
        # Core queue and storage
        self.job_queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.active_jobs: Dict[str, AnalysisJob] = {}  # job_id -> job
        self.job_results: Dict[str, Dict[str, Any]] = {}  # job_id -> result
        self.job_history: List[AnalysisJob] = []  # For metrics and debugging
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_requested = False
        
        logger.info(
            f"AsyncAnalysisQueue initialized",
            extra={
                "max_queue_size": self.config.max_queue_size,
                "max_concurrent_workers": self.config.max_concurrent_workers,
                "result_retention_hours": self.config.result_retention_hours
            }
        )
    
    async def start(self):
        """Start the queue manager and background cleanup."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Async analysis queue started")
    
    async def stop(self):
        """Stop the queue manager and cleanup background tasks."""
        self._shutdown_requested = True
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
        logger.info("Async analysis queue stopped")
    
    async def queue_analysis(
        self,
        pr_number: int,
        repository: str,
        pr_data: Dict[str, Any],
        priority: int = 1
    ) -> str:
        """
        Queue a PR for async analysis.
        
        Args:
            pr_number: GitHub PR number
            repository: Repository in format "owner/repo"
            pr_data: PR metadata from GitHub API
            priority: Job priority (lower = higher priority)
            
        Returns:
            job_id for tracking the analysis
            
        Raises:
            asyncio.QueueFull: If queue is at capacity
        """
        # Generate unique job ID
        job_id = f"{repository}#{pr_number}#{uuid.uuid4().hex[:8]}"
        
        # Create job with estimated completion
        estimated_duration = self.config.estimate_duration(pr_data)
        job = AnalysisJob(
            job_id=job_id,
            pr_number=pr_number,
            repository=repository,
            pr_data=pr_data,
            priority=priority,
            estimated_completion=time.time() + estimated_duration
        )
        
        # Add to queue
        try:
            await self.job_queue.put(job)
            self.active_jobs[job_id] = job
            ASYNC_METRICS.record_job_queued()
            
            logger.info(
                f"Queued async analysis for {repository}#{pr_number}",
                extra={
                    "job_id": job_id,
                    "queue_size": self.job_queue.qsize(),
                    "estimated_duration": estimated_duration,
                    "pr_size": pr_data.get('additions', 0) + pr_data.get('deletions', 0)
                }
            )
            
            return job_id
            
        except asyncio.QueueFull:
            logger.error(f"Queue full, cannot queue analysis for {repository}#{pr_number}")
            raise
    
    async def get_next_job(self, timeout: int = None) -> Optional[AnalysisJob]:
        """
        Get the next job from the queue.
        
        Args:
            timeout: Maximum seconds to wait for a job
            
        Returns:
            Next job to process or None if timeout
        """
        try:
            timeout = timeout or self.config.worker_idle_timeout
            job = await asyncio.wait_for(self.job_queue.get(), timeout=timeout)
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.started_at = time.time()
            job.progress = self.config.progress_checkpoints["started"]
            
            logger.debug(f"Dispatched job {job.job_id} for processing")
            return job
            
        except asyncio.TimeoutError:
            return None
    
    def update_job_progress(self, job_id: str, progress: int, worker_id: str = None):
        """Update job progress."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.progress = min(progress, 100)
            if worker_id:
                job.worker_id = worker_id
                
            logger.debug(f"Job {job_id} progress: {progress}%")
    
    def complete_job(self, job_id: str, result: Dict[str, Any]):
        """Mark job as completed with result."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = JobStatus.COMPLETED
            job.completed_at = time.time()
            job.progress = 100
            job.result = result
            
            # Store result
            self.job_results[job_id] = result
            
            # Move to history
            self.job_history.append(job)
            
            # Calculate duration and record metrics
            duration = job.completed_at - (job.started_at or job.queued_at)
            ASYNC_METRICS.record_job_completed(duration)
            
            logger.info(
                f"Job {job_id} completed successfully",
                extra={
                    "duration": duration,
                    "pr": f"{job.repository}#{job.pr_number}"
                }
            )
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed with error message."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = JobStatus.FAILED
            job.completed_at = time.time()
            job.error_message = error_message
            
            # Move to history
            self.job_history.append(job)
            ASYNC_METRICS.record_job_failed()
            
            logger.error(
                f"Job {job_id} failed: {error_message}",
                extra={"pr": f"{job.repository}#{job.pr_number}"}
            )
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job."""
        # Check active jobs first
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()
        
        # Check completed results
        if job_id in self.job_results:
            # Find in history
            for job in self.job_history:
                if job.job_id == job_id:
                    status = job.to_dict()
                    if job.status == JobStatus.COMPLETED:
                        status["result"] = self.job_results[job_id]
                    return status
        
        # Check history for failed/expired jobs
        for job in self.job_history:
            if job.job_id == job_id:
                return job.to_dict()
        
        return None
    
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get result of completed analysis."""
        return self.job_results.get(job_id)
    
    def list_active_jobs(self) -> List[Dict[str, Any]]:
        """List all active jobs."""
        return [job.to_dict() for job in self.active_jobs.values()]
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        return {
            "queue_size": self.job_queue.qsize(),
            "active_jobs": len(self.active_jobs),
            "max_queue_size": self.config.max_queue_size,
            "max_concurrent_workers": self.config.max_concurrent_workers,
            "metrics": ASYNC_METRICS.to_dict(),
            "config": {
                "result_retention_hours": self.config.result_retention_hours,
                "async_threshold_lines": self.config.async_threshold_lines,
                "async_threshold_files": self.config.async_threshold_files
            }
        }
    
    async def _cleanup_loop(self):
        """Background cleanup of expired results."""
        while not self._shutdown_requested:
            try:
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
                await self._cleanup_expired_results()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired_results(self):
        """Remove expired results and update metrics."""
        now = time.time()
        retention_seconds = self.config.result_retention_hours * 3600
        
        # Clean up results
        expired_results = []
        for job_id, _ in list(self.job_results.items()):
            # Find corresponding job in history
            job = next((j for j in self.job_history if j.job_id == job_id), None)
            if job and job.completed_at and (now - job.completed_at) > retention_seconds:
                expired_results.append(job_id)
        
        for job_id in expired_results:
            del self.job_results[job_id]
        
        # Clean up old history entries
        status_retention_seconds = self.config.status_retention_hours * 3600
        self.job_history = [
            job for job in self.job_history
            if not job.completed_at or (now - job.completed_at) <= status_retention_seconds
        ]
        
        if expired_results:
            logger.info(f"Cleaned up {len(expired_results)} expired analysis results")


# Global queue instance
_global_queue: Optional[AsyncAnalysisQueue] = None


async def get_global_queue() -> AsyncAnalysisQueue:
    """Get or create the global async analysis queue."""
    global _global_queue
    if _global_queue is None:
        _global_queue = AsyncAnalysisQueue()
        await _global_queue.start()
    return _global_queue


async def shutdown_global_queue():
    """Shutdown the global queue."""
    global _global_queue
    if _global_queue:
        await _global_queue.stop()
        _global_queue = None