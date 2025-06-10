"""
Status Tracking System

Real-time progress monitoring and status reporting for async analysis jobs.
Provides user-friendly status updates and detailed progress information.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .config import AsyncAnalysisConfig, DEFAULT_ASYNC_CONFIG
from .queue_manager import AsyncAnalysisQueue, JobStatus


class AnalysisPhase(Enum):
    """Phases of analysis processing."""
    QUEUED = "queued"
    FETCHING_DATA = "fetching_data"
    CHUNKING = "chunking"
    ANALYZING = "analyzing"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AnalysisStatus:
    """Comprehensive status information for an analysis job."""
    job_id: str
    phase: AnalysisPhase
    progress_percent: int
    message: str
    estimated_completion: Optional[float] = None
    time_remaining_seconds: Optional[int] = None
    current_activity: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "phase": self.phase.value,
            "progress_percent": self.progress_percent,
            "message": self.message,
            "estimated_completion": self.estimated_completion,
            "time_remaining_seconds": self.time_remaining_seconds,
            "current_activity": self.current_activity
        }


class StatusTracker:
    """
    Tracks and reports analysis job status with user-friendly messaging.
    
    Provides real-time progress updates, time estimates, and detailed
    status information for background analysis jobs.
    """
    
    def __init__(self, config: AsyncAnalysisConfig = None):
        self.config = config or DEFAULT_ASYNC_CONFIG
        self.status_cache: Dict[str, AnalysisStatus] = {}
    
    def get_comprehensive_status(
        self, 
        job_id: str, 
        queue: AsyncAnalysisQueue
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive status for a job including progress, timing, and context.
        
        Args:
            job_id: Job identifier
            queue: Queue to get job information from
            
        Returns:
            Comprehensive status dictionary or None if job not found
        """
        job_status = queue.get_job_status(job_id)
        if not job_status:
            return None
        
        # Extract basic information
        progress = job_status.get("progress", 0)
        status_enum = JobStatus(job_status.get("status", "queued"))
        
        # Calculate timing information
        timing_info = self._calculate_timing_info(job_status)
        
        # Generate user-friendly status
        user_status = self._generate_user_friendly_status(job_status, timing_info)
        
        # Build comprehensive response
        return {
            "job_id": job_id,
            "status": status_enum.value,
            "progress_percent": progress,
            "phase": self._determine_phase(job_status).value,
            
            # User-friendly information
            "message": user_status["message"],
            "user_friendly_status": user_status["friendly_description"],
            "current_activity": user_status["current_activity"],
            
            # Timing information
            "timing": timing_info,
            
            # PR information
            "pr_info": job_status.get("pr_info", {}),
            
            # Technical details
            "technical_details": {
                "worker_id": job_status.get("worker_id"),
                "queued_at": job_status.get("queued_at"),
                "started_at": job_status.get("started_at"),
                "completed_at": job_status.get("completed_at"),
                "error_message": job_status.get("error_message")
            },
            
            # Actions available
            "available_actions": self._get_available_actions(status_enum, progress)
        }
    
    def _calculate_timing_info(self, job_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate timing information for a job."""
        now = time.time()
        queued_at = job_status.get("queued_at", now)
        started_at = job_status.get("started_at")
        completed_at = job_status.get("completed_at")
        estimated_completion = job_status.get("estimated_completion")
        
        timing_info = {
            "queued_duration_seconds": int(now - queued_at),
            "total_duration_seconds": None,
            "processing_duration_seconds": None,
            "estimated_completion_timestamp": estimated_completion,
            "time_remaining_seconds": None
        }
        
        if started_at:
            timing_info["processing_duration_seconds"] = int(
                (completed_at or now) - started_at
            )
        
        if completed_at:
            timing_info["total_duration_seconds"] = int(completed_at - queued_at)
        
        # Calculate time remaining for active jobs
        if estimated_completion and not completed_at:
            remaining = max(0, int(estimated_completion - now))
            timing_info["time_remaining_seconds"] = remaining
        
        return timing_info
    
    def _determine_phase(self, job_status: Dict[str, Any]) -> AnalysisPhase:
        """Determine the current analysis phase."""
        status = JobStatus(job_status.get("status", "queued"))
        progress = job_status.get("progress", 0)
        
        if status == JobStatus.FAILED:
            return AnalysisPhase.FAILED
        elif status == JobStatus.COMPLETED:
            return AnalysisPhase.COMPLETED
        elif status == JobStatus.QUEUED:
            return AnalysisPhase.QUEUED
        elif status == JobStatus.PROCESSING:
            if progress < 20:
                return AnalysisPhase.FETCHING_DATA
            elif progress < 30:
                return AnalysisPhase.CHUNKING
            elif progress < 90:
                return AnalysisPhase.ANALYZING
            else:
                return AnalysisPhase.MERGING
        
        return AnalysisPhase.QUEUED
    
    def _generate_user_friendly_status(
        self, 
        job_status: Dict[str, Any], 
        timing_info: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate user-friendly status messages."""
        phase = self._determine_phase(job_status)
        progress = job_status.get("progress", 0)
        pr_info = job_status.get("pr_info", {})
        
        # Get PR context
        pr_title = pr_info.get("title", "Unknown PR")
        pr_size = pr_info.get("additions", 0) + pr_info.get("deletions", 0)
        pr_files = pr_info.get("changed_files", 0)
        
        if phase == AnalysisPhase.QUEUED:
            queue_time = timing_info.get("queued_duration_seconds", 0)
            return {
                "message": f"PR analysis queued ({self._format_duration(queue_time)} ago)",
                "friendly_description": f"Your large PR ({pr_files} files, {pr_size} lines) is waiting in queue for detailed analysis.",
                "current_activity": "Waiting for available worker"
            }
        
        elif phase == AnalysisPhase.FETCHING_DATA:
            return {
                "message": f"Fetching PR data and files ({progress}%)",
                "friendly_description": f"Downloading all changes from '{pr_title}' for analysis.",
                "current_activity": "Retrieving file contents and diffs"
            }
        
        elif phase == AnalysisPhase.CHUNKING:
            return {
                "message": f"Organizing files for analysis ({progress}%)",
                "friendly_description": f"Grouping {pr_files} files into optimal chunks for deep analysis.",
                "current_activity": "Creating intelligent file groups"
            }
        
        elif phase == AnalysisPhase.ANALYZING:
            time_remaining = timing_info.get("time_remaining_seconds")
            time_str = f" (~{self._format_duration(time_remaining)} remaining)" if time_remaining else ""
            return {
                "message": f"Analyzing code changes ({progress}%){time_str}",
                "friendly_description": f"Running comprehensive LLM analysis on code chunks from '{pr_title}'.",
                "current_activity": "Deep analysis with pattern detection"
            }
        
        elif phase == AnalysisPhase.MERGING:
            return {
                "message": f"Finalizing analysis results ({progress}%)",
                "friendly_description": "Merging chunk analysis results and generating final recommendations.",
                "current_activity": "Combining insights and prioritizing findings"
            }
        
        elif phase == AnalysisPhase.COMPLETED:
            duration = timing_info.get("total_duration_seconds", 0)
            return {
                "message": f"Analysis completed in {self._format_duration(duration)}",
                "friendly_description": f"Comprehensive analysis of '{pr_title}' is ready with detailed insights.",
                "current_activity": "Results available for review"
            }
        
        elif phase == AnalysisPhase.FAILED:
            error = job_status.get("error_message", "Unknown error")
            return {
                "message": f"Analysis failed: {error}",
                "friendly_description": f"Could not complete analysis of '{pr_title}' due to processing error.",
                "current_activity": "Manual review recommended"
            }
        
        return {
            "message": "Processing...",
            "friendly_description": "Analysis in progress.",
            "current_activity": "Working on your request"
        }
    
    def _format_duration(self, seconds: Optional[int]) -> str:
        """Format duration in human-readable format."""
        if seconds is None or seconds < 0:
            return "unknown"
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _get_available_actions(
        self, 
        status: JobStatus, 
        progress: int
    ) -> List[str]:
        """Get list of actions available for the current status."""
        actions = []
        
        if status == JobStatus.QUEUED:
            actions.append("cancel")
        elif status == JobStatus.PROCESSING:
            actions.append("check_progress")
            if progress > 50:
                actions.append("cancel_with_partial_results")
        elif status == JobStatus.COMPLETED:
            actions.extend(["view_results", "download_report"])
        elif status == JobStatus.FAILED:
            actions.extend(["retry", "manual_review"])
        
        return actions
    
    def get_queue_overview(self, queue: AsyncAnalysisQueue) -> Dict[str, Any]:
        """Get overview of entire queue status."""
        queue_status = queue.get_queue_status()
        active_jobs = queue.list_active_jobs()
        
        # Calculate statistics
        total_queued = sum(1 for job in active_jobs if job["status"] == "queued")
        total_processing = sum(1 for job in active_jobs if job["status"] == "processing")
        
        # Estimate queue processing time
        avg_duration = queue_status["metrics"].get("average_duration_seconds", 600)
        estimated_queue_time = total_queued * avg_duration
        
        return {
            "queue_summary": {
                "total_jobs": len(active_jobs),
                "queued": total_queued,
                "processing": total_processing,
                "estimated_queue_time_seconds": estimated_queue_time
            },
            "system_status": {
                "queue_capacity": queue_status["max_queue_size"],
                "queue_utilization_percent": int(
                    (queue_status["queue_size"] / queue_status["max_queue_size"]) * 100
                ),
                "active_workers": queue_status["max_concurrent_workers"],
                "system_load": "normal" if total_processing < queue_status["max_concurrent_workers"] else "high"
            },
            "metrics": queue_status["metrics"],
            "recent_jobs": [
                {
                    "job_id": job["job_id"],
                    "pr": f"{job['repository']}#{job['pr_number']}",
                    "status": job["status"],
                    "progress": job["progress"]
                }
                for job in active_jobs[-5:]  # Last 5 jobs
            ]
        }