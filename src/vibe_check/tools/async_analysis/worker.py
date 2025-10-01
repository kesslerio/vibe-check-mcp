"""
Async Analysis Worker System

Background workers that process queued massive PRs using extended chunked 
analysis with longer timeouts and larger chunks optimized for background processing.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .config import AsyncAnalysisConfig, DEFAULT_ASYNC_CONFIG
from .queue_manager import AsyncAnalysisQueue, AnalysisJob, JobStatus
from vibe_check.tools.shared.claude_integration import analyze_content_async_with_circuit_breaker
from vibe_check.tools.pr_review.chunked_analyzer import analyze_pr_with_chunking, ChunkedAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class WorkerResult:
    """Result of worker processing."""
    success: bool
    job_id: str
    duration: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AsyncAnalysisWorker:
    """
    Background worker for processing massive PRs.
    
    Uses extended chunked analysis with larger chunks and longer timeouts
    optimized for background processing where user experience is not critical.
    """
    
    def __init__(
        self, 
        queue: AsyncAnalysisQueue,
        worker_id: str = None,
        config: AsyncAnalysisConfig = None
    ):
        self.queue = queue
        self.config = config or DEFAULT_ASYNC_CONFIG
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.running = False
        self.current_job: Optional[AnalysisJob] = None
        
        # Configure chunked analysis for background processing
        self.chunked_analyzer = ChunkedAnalyzer(
            chunk_timeout=self.config.chunk_timeout_seconds,
            max_concurrent_chunks=1,  # Sequential for background to avoid resource conflicts
            max_lines_per_chunk=self.config.large_pr_chunk_size
        )
        
        logger.info(
            f"AsyncAnalysisWorker {self.worker_id} initialized",
            extra={
                "chunk_size": self.config.large_pr_chunk_size,
                "chunk_timeout": self.config.chunk_timeout_seconds
            }
        )
    
    async def start(self):
        """Start the worker processing loop."""
        self.running = True
        logger.info(f"Worker {self.worker_id} started")
        
        while self.running:
            try:
                # Get next job from queue
                job = await self.queue.get_next_job(timeout=self.config.worker_idle_timeout)
                
                if job is None:
                    # No jobs available, continue waiting
                    continue
                
                # Process the job
                result = await self._process_job(job)
                
                # Update queue with result
                if result.success:
                    self.queue.complete_job(result.job_id, result.result)
                else:
                    self.queue.fail_job(result.job_id, result.error)
                    
            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                
                # If we have a current job, mark it as failed
                if self.current_job:
                    self.queue.fail_job(self.current_job.job_id, f"Worker error: {str(e)}")
                    self.current_job = None
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info(f"Worker {self.worker_id} stop requested")
    
    async def _process_job(self, job: AnalysisJob) -> WorkerResult:
        """
        Process a single analysis job.
        
        Args:
            job: The analysis job to process
            
        Returns:
            WorkerResult with success status and result/error
        """
        import os
        self.current_job = job
        start_time = time.time()
        
        # Register process ID for resource monitoring
        from .resource_monitor import get_global_resource_monitor
        resource_monitor = get_global_resource_monitor()
        process_id = os.getpid()
        
        # Update resource monitor with process ID
        tracker = resource_monitor.job_trackers.get(job.job_id)
        if tracker:
            tracker.process_id = process_id
        
        logger.info(
            f"Worker {self.worker_id} processing job {job.job_id}",
            extra={
                "pr": f"{job.repository}#{job.pr_number}",
                "pr_size": job.pr_data.get('additions', 0) + job.pr_data.get('deletions', 0),
                "process_id": process_id
            }
        )
        
        try:
            # Update progress - started
            self.queue.update_job_progress(
                job.job_id, 
                self.config.progress_checkpoints["started"],
                self.worker_id
            )
            
            # Fetch PR files for analysis
            from ..shared.github_abstraction import get_default_github_operations
            github_ops = get_default_github_operations()
            
            # Get PR files with diff content
            files_result = github_ops.get_pull_request_files(job.repository, job.pr_number)
            if not files_result.success:
                raise Exception(f"Failed to fetch PR files: {files_result.error}")
            
            pr_files = files_result.data
            
            # Update progress - files fetched
            self.queue.update_job_progress(job.job_id, 25)
            
            # Perform extended chunked analysis
            analysis_result = await self._analyze_large_pr(job, pr_files)
            
            # Update progress - analysis complete
            self.queue.update_job_progress(job.job_id, 95)
            
            # Prepare final result
            final_result = self._prepare_final_result(job, analysis_result)
            
            duration = time.time() - start_time
            self.current_job = None
            
            # Unregister from resource monitoring
            resource_monitor.unregister_job(job.job_id)
            
            logger.info(
                f"Worker {self.worker_id} completed job {job.job_id}",
                extra={"duration": duration}
            )
            
            return WorkerResult(
                success=True,
                job_id=job.job_id,
                duration=duration,
                result=final_result
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            
            # Unregister from resource monitoring
            resource_monitor.unregister_job(job.job_id)
            
            logger.error(
                f"Worker {self.worker_id} failed job {job.job_id}: {error_message}",
                extra={"duration": duration}
            )
            
            self.current_job = None
            
            return WorkerResult(
                success=False,
                job_id=job.job_id,
                duration=duration,
                error=error_message
            )
    
    async def _analyze_large_pr(
        self, 
        job: AnalysisJob, 
        pr_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform extended chunked analysis for large PRs.
        
        Args:
            job: Analysis job with PR metadata
            pr_files: List of changed files with content
            
        Returns:
            Comprehensive analysis result
        """
        # Perform chunked analysis with background-optimized settings
        chunked_result = await self.chunked_analyzer.analyze_pr_chunked(
            pr_data=job.pr_data,
            pr_files=pr_files
        )
        
        # Update progress based on chunked analysis completion
        if chunked_result.total_chunks > 0:
            chunk_progress = int(
                (chunked_result.successful_chunks / chunked_result.total_chunks) * total_progress_range
            )
            self.queue.update_job_progress(job.job_id, base_progress + chunk_progress)
        
        return {
            "analysis_mode": "async_detailed_analysis",
            "chunked_result": chunked_result,
            "background_processing": True,
            "worker_id": self.worker_id,
            "analysis_timestamp": time.time()
        }
    
    def _prepare_final_result(
        self, 
        job: AnalysisJob, 
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare final result for storage and retrieval.
        
        Args:
            job: Original analysis job
            analysis_result: Raw analysis result
            
        Returns:
            Formatted final result
        """
        chunked_result = analysis_result.get("chunked_result")
        
        return {
            "status": "async_analysis_complete",
            "job_id": job.job_id,
            "pr_number": job.pr_number,
            "repository": job.repository,
            "analysis_mode": "async_detailed_analysis",
            "completed_at": time.time(),
            "worker_id": self.worker_id,
            
            # Analysis summary
            "overview": chunked_result.overall_assessment if chunked_result else "Analysis completed",
            "patterns_detected": chunked_result.patterns_detected if chunked_result else [],
            "recommendations": chunked_result.recommendations if chunked_result else [],
            
            # Detailed results
            "chunk_analysis": {
                "total_chunks": chunked_result.total_chunks if chunked_result else 0,
                "successful_chunks": chunked_result.successful_chunks if chunked_result else 0,
                "failed_chunks": chunked_result.failed_chunks if chunked_result else 0,
                "total_duration": chunked_result.total_duration if chunked_result else 0,
                "chunk_summaries": chunked_result.chunk_summaries if chunked_result else []
            },
            
            # PR metadata
            "pr_info": {
                "title": job.pr_data.get("title", "Unknown"),
                "additions": job.pr_data.get("additions", 0),
                "deletions": job.pr_data.get("deletions", 0),
                "changed_files": job.pr_data.get("changed_files", 0),
                "total_changes": job.pr_data.get("additions", 0) + job.pr_data.get("deletions", 0)
            },
            
            # Processing metadata
            "processing_info": {
                "queued_at": job.queued_at,
                "started_at": job.started_at,
                "processing_duration": time.time() - (job.started_at or job.queued_at),
                "chunk_size_used": self.chunked_config.chunk_size_lines,
                "chunk_timeout_used": self.chunked_config.chunk_timeout_seconds
            }
        }


class AsyncWorkerManager:
    """
    Manages multiple async analysis workers.
    
    Provides controlled scaling of background processing capacity
    and graceful shutdown of worker pool.
    """
    
    def __init__(
        self, 
        queue: AsyncAnalysisQueue,
        config: AsyncAnalysisConfig = None
    ):
        self.queue = queue
        self.config = config or DEFAULT_ASYNC_CONFIG
        self.workers: List[AsyncAnalysisWorker] = []
        self.worker_tasks: List[asyncio.Task] = []
        
        logger.info(
            f"AsyncWorkerManager initialized for {self.config.max_concurrent_workers} workers"
        )
    
    async def start_workers(self):
        """Start the worker pool."""
        for i in range(self.config.max_concurrent_workers):
            worker = AsyncAnalysisWorker(
                queue=self.queue,
                worker_id=f"worker-{i+1}",
                config=self.config
            )
            
            self.workers.append(worker)
            
            # Start worker in background
            task = asyncio.create_task(worker.start())
            self.worker_tasks.append(task)
        
        logger.info(f"Started {len(self.workers)} async analysis workers")
    
    async def stop_workers(self):
        """Stop all workers gracefully."""
        logger.info("Stopping async analysis workers...")
        
        # Request all workers to stop
        for worker in self.workers:
            worker.stop()
        
        # Wait for all worker tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Clear worker references
        self.workers.clear()
        self.worker_tasks.clear()
        
        logger.info("All async analysis workers stopped")
    
    def get_worker_status(self) -> List[Dict[str, Any]]:
        """Get status of all workers."""
        return [
            {
                "worker_id": worker.worker_id,
                "running": worker.running,
                "current_job": worker.current_job.job_id if worker.current_job else None,
                "current_pr": f"{worker.current_job.repository}#{worker.current_job.pr_number}" 
                              if worker.current_job else None
            }
            for worker in self.workers
        ]


# Global worker manager
_global_worker_manager: Optional[AsyncWorkerManager] = None


async def get_global_worker_manager(queue: AsyncAnalysisQueue) -> AsyncWorkerManager:
    """Get or create the global worker manager."""
    global _global_worker_manager
    if _global_worker_manager is None:
        _global_worker_manager = AsyncWorkerManager(queue)
        await _global_worker_manager.start_workers()
    return _global_worker_manager


async def shutdown_global_workers():
    """Shutdown the global worker manager."""
    global _global_worker_manager
    if _global_worker_manager:
        await _global_worker_manager.stop_workers()
        _global_worker_manager = None