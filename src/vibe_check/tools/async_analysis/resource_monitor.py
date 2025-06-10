"""
Resource Monitoring for Async Analysis System

Provides real-time monitoring of system resources, job-level resource limits,
and automatic protection against resource exhaustion.
"""

import asyncio
import psutil
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from threading import Lock
import warnings

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits configuration for jobs."""
    
    # Memory limits
    max_memory_mb: int = 512  # Maximum memory per job in MB
    max_total_memory_mb: int = 2048  # Maximum total system memory for async jobs
    
    # CPU limits
    max_cpu_percent: float = 25.0  # Maximum CPU percentage per job
    max_total_cpu_percent: float = 70.0  # Maximum total CPU for async jobs
    
    # Time limits
    max_job_duration_seconds: int = 1200  # 20 minutes max per job
    max_idle_time_seconds: int = 300  # 5 minutes max idle time
    
    # Concurrency limits
    max_concurrent_jobs: int = 2  # Maximum parallel jobs
    max_queue_size: int = 10  # Maximum queued jobs
    
    # I/O limits
    max_file_descriptors: int = 100  # Maximum file descriptors per job
    max_network_connections: int = 20  # Maximum network connections per job


@dataclass
class ResourceUsage:
    """Current resource usage metrics."""
    
    # Memory usage
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    
    # CPU usage
    cpu_percent: float = 0.0
    
    # I/O metrics
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    
    # Process metrics
    open_files: int = 0
    open_connections: int = 0
    
    # Timestamps
    measured_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "memory_mb": round(self.memory_mb, 2),
            "memory_percent": round(self.memory_percent, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "disk_io_read_mb": round(self.disk_io_read_mb, 2),
            "disk_io_write_mb": round(self.disk_io_write_mb, 2),
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv,
            "open_files": self.open_files,
            "open_connections": self.open_connections,
            "measured_at": self.measured_at
        }


@dataclass
class JobResourceTracker:
    """Tracks resource usage for a specific job."""
    
    job_id: str
    process_id: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    peak_memory_mb: float = 0.0
    total_cpu_time: float = 0.0
    current_usage: ResourceUsage = field(default_factory=ResourceUsage)
    usage_history: List[ResourceUsage] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    
    def update_usage(self, usage: ResourceUsage):
        """Update current usage and maintain history."""
        self.current_usage = usage
        self.peak_memory_mb = max(self.peak_memory_mb, usage.memory_mb)
        
        # Keep last 100 measurements
        self.usage_history.append(usage)
        if len(self.usage_history) > 100:
            self.usage_history.pop(0)
    
    def get_duration(self) -> float:
        """Get job duration in seconds."""
        return time.time() - self.start_time
    
    def check_violations(self, limits: ResourceLimits) -> List[str]:
        """Check for resource limit violations."""
        violations = []
        usage = self.current_usage
        
        # Memory violations
        if usage.memory_mb > limits.max_memory_mb:
            violations.append(f"Memory limit exceeded: {usage.memory_mb:.1f}MB > {limits.max_memory_mb}MB")
        
        # CPU violations
        if usage.cpu_percent > limits.max_cpu_percent:
            violations.append(f"CPU limit exceeded: {usage.cpu_percent:.1f}% > {limits.max_cpu_percent}%")
        
        # Time violations
        duration = self.get_duration()
        if duration > limits.max_job_duration_seconds:
            violations.append(f"Duration limit exceeded: {duration:.1f}s > {limits.max_job_duration_seconds}s")
        
        # File descriptor violations
        if usage.open_files > limits.max_file_descriptors:
            violations.append(f"File descriptor limit exceeded: {usage.open_files} > {limits.max_file_descriptors}")
        
        # Network connection violations
        if usage.open_connections > limits.max_network_connections:
            violations.append(f"Network connection limit exceeded: {usage.open_connections} > {limits.max_network_connections}")
        
        # Update violations list
        for violation in violations:
            if violation not in self.violations:
                self.violations.append(violation)
        
        return violations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "process_id": self.process_id,
            "duration_seconds": round(self.get_duration(), 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "total_cpu_time": round(self.total_cpu_time, 2),
            "current_usage": self.current_usage.to_dict(),
            "violations": self.violations.copy(),
            "measurements_count": len(self.usage_history)
        }


class ResourceMonitor:
    """
    Monitors system and job-level resource usage.
    
    Provides real-time monitoring, limit enforcement, and alerting
    for the async analysis system.
    """
    
    def __init__(self, limits: ResourceLimits = None):
        self.limits = limits or ResourceLimits()
        self.job_trackers: Dict[str, JobResourceTracker] = {}
        self.system_usage_history: List[ResourceUsage] = []
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.lock = Lock()
        
        # Cache process objects to avoid repeated lookups
        self._process_cache = {}
        self._cache_timeout = 30  # Seconds
        self._last_cache_cleanup = time.time()
        
        logger.info(f"ResourceMonitor initialized with limits: {self.limits}")
    
    async def start_monitoring(self, interval_seconds: float = 5.0):
        """Start continuous resource monitoring."""
        if self.monitoring_active:
            logger.warning("Resource monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info(f"Started resource monitoring with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped resource monitoring")
    
    def register_job(self, job_id: str, process_id: Optional[int] = None) -> JobResourceTracker:
        """Register a new job for monitoring."""
        with self.lock:
            tracker = JobResourceTracker(job_id=job_id, process_id=process_id)
            self.job_trackers[job_id] = tracker
            logger.info(f"Registered job {job_id} for resource monitoring")
            return tracker
    
    def unregister_job(self, job_id: str):
        """Unregister a job from monitoring."""
        with self.lock:
            if job_id in self.job_trackers:
                del self.job_trackers[job_id]
                logger.info(f"Unregistered job {job_id} from resource monitoring")
    
    def get_system_usage(self) -> ResourceUsage:
        """Get current system resource usage."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # CPU usage (non-blocking)
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_sent = net_io.bytes_sent if net_io else 0
            net_recv = net_io.bytes_recv if net_io else 0
            
            # Process counts
            try:
                open_files = len(psutil.Process().open_files())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                open_files = 0
            
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            return ResourceUsage(
                memory_mb=memory.used / (1024 * 1024),
                memory_percent=memory.percent,
                cpu_percent=cpu_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_bytes_sent=net_sent,
                network_bytes_recv=net_recv,
                open_files=open_files,
                open_connections=connections
            )
            
        except Exception as e:
            logger.warning(f"Error getting system usage: {e}")
            return ResourceUsage()
    
    def get_job_usage(self, job_id: str) -> Optional[ResourceUsage]:
        """Get resource usage for a specific job."""
        with self.lock:
            tracker = self.job_trackers.get(job_id)
            if not tracker or not tracker.process_id:
                return None
        
        try:
            process = self._get_process(tracker.process_id)
            if not process:
                return None
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=None)
            
            # I/O usage
            try:
                io_counters = process.io_counters()
                disk_read_mb = io_counters.read_bytes / (1024 * 1024)
                disk_write_mb = io_counters.write_bytes / (1024 * 1024)
            except (AttributeError, psutil.AccessDenied):
                disk_read_mb = disk_write_mb = 0
            
            # File descriptors and connections
            try:
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            try:
                connections = len(process.connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            return ResourceUsage(
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                cpu_percent=cpu_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                open_files=open_files,
                open_connections=connections
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"Cannot access process {tracker.process_id} for job {job_id}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error getting job usage for {job_id}: {e}")
            return None
    
    def check_system_limits(self) -> Dict[str, Any]:
        """Check if system is within resource limits."""
        usage = self.get_system_usage()
        violations = []
        warnings_list = []
        
        # Check total memory usage by async jobs
        total_job_memory = sum(
            tracker.current_usage.memory_mb 
            for tracker in self.job_trackers.values()
        )
        
        if total_job_memory > self.limits.max_total_memory_mb:
            violations.append(f"Total job memory exceeded: {total_job_memory:.1f}MB > {self.limits.max_total_memory_mb}MB")
        elif total_job_memory > self.limits.max_total_memory_mb * 0.8:
            warnings_list.append(f"Total job memory at 80%: {total_job_memory:.1f}MB")
        
        # Check concurrent jobs
        active_jobs = len(self.job_trackers)
        if active_jobs > self.limits.max_concurrent_jobs:
            violations.append(f"Too many concurrent jobs: {active_jobs} > {self.limits.max_concurrent_jobs}")
        
        # Check system CPU
        if usage.cpu_percent > self.limits.max_total_cpu_percent:
            violations.append(f"System CPU exceeded: {usage.cpu_percent:.1f}% > {self.limits.max_total_cpu_percent}%")
        elif usage.cpu_percent > self.limits.max_total_cpu_percent * 0.8:
            warnings_list.append(f"System CPU at 80%: {usage.cpu_percent:.1f}%")
        
        # Check system memory
        if usage.memory_percent > 90:
            violations.append(f"System memory critically high: {usage.memory_percent:.1f}%")
        elif usage.memory_percent > 80:
            warnings_list.append(f"System memory high: {usage.memory_percent:.1f}%")
        
        return {
            "within_limits": len(violations) == 0,
            "violations": violations,
            "warnings": warnings_list,
            "current_usage": usage.to_dict(),
            "active_jobs": active_jobs,
            "total_job_memory_mb": round(total_job_memory, 2)
        }
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive resource monitoring status."""
        system_check = self.check_system_limits()
        
        # Job-level status
        job_status = {}
        total_violations = 0
        
        with self.lock:
            for job_id, tracker in self.job_trackers.items():
                violations = tracker.check_violations(self.limits)
                total_violations += len(violations)
                
                job_status[job_id] = {
                    "status": "healthy" if not violations else "violating",
                    "duration_seconds": tracker.get_duration(),
                    "peak_memory_mb": tracker.peak_memory_mb,
                    "current_violations": violations,
                    "total_violations": len(tracker.violations)
                }
        
        return {
            "monitoring_active": self.monitoring_active,
            "system_status": system_check,
            "job_count": len(self.job_trackers),
            "job_status": job_status,
            "total_violations": total_violations,
            "limits": {
                "max_memory_mb": self.limits.max_memory_mb,
                "max_cpu_percent": self.limits.max_cpu_percent,
                "max_concurrent_jobs": self.limits.max_concurrent_jobs,
                "max_job_duration_seconds": self.limits.max_job_duration_seconds
            },
            "timestamp": time.time()
        }
    
    def should_accept_new_job(self) -> Tuple[bool, str]:
        """Check if system can accept a new job."""
        system_check = self.check_system_limits()
        
        if not system_check["within_limits"]:
            return False, f"System limit violations: {'; '.join(system_check['violations'])}"
        
        if len(self.job_trackers) >= self.limits.max_concurrent_jobs:
            return False, f"Maximum concurrent jobs reached: {len(self.job_trackers)}"
        
        # Check memory headroom
        available_memory = self.limits.max_total_memory_mb - system_check["total_job_memory_mb"]
        if available_memory < self.limits.max_memory_mb:
            return False, f"Insufficient memory headroom: {available_memory:.1f}MB available"
        
        return True, "System ready for new job"
    
    async def _monitoring_loop(self, interval_seconds: float):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Update system usage
                system_usage = self.get_system_usage()
                self.system_usage_history.append(system_usage)
                
                # Keep last 1000 system measurements
                if len(self.system_usage_history) > 1000:
                    self.system_usage_history.pop(0)
                
                # Update job usage
                with self.lock:
                    for job_id, tracker in list(self.job_trackers.items()):
                        job_usage = self.get_job_usage(job_id)
                        if job_usage:
                            tracker.update_usage(job_usage)
                            
                            # Check for violations
                            violations = tracker.check_violations(self.limits)
                            if violations:
                                logger.warning(f"Job {job_id} resource violations: {violations}")
                
                # Cleanup old cache entries
                await self._cleanup_process_cache()
                
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    def _get_process(self, pid: int) -> Optional[psutil.Process]:
        """Get process object with caching."""
        current_time = time.time()
        
        # Check cache
        if pid in self._process_cache:
            process, cached_time = self._process_cache[pid]
            if current_time - cached_time < self._cache_timeout:
                return process
        
        # Create new process object
        try:
            process = psutil.Process(pid)
            self._process_cache[pid] = (process, current_time)
            return process
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Remove from cache if exists
            self._process_cache.pop(pid, None)
            return None
    
    async def _cleanup_process_cache(self):
        """Clean up old process cache entries."""
        current_time = time.time()
        
        if current_time - self._last_cache_cleanup > 60:  # Cleanup every minute
            expired_pids = [
                pid for pid, (_, cached_time) in self._process_cache.items()
                if current_time - cached_time > self._cache_timeout
            ]
            
            for pid in expired_pids:
                self._process_cache.pop(pid, None)
            
            self._last_cache_cleanup = current_time
            
            if expired_pids:
                logger.debug(f"Cleaned up {len(expired_pids)} expired process cache entries")


# Global resource monitor instance
_global_monitor: Optional[ResourceMonitor] = None
_monitor_lock = Lock()


def get_global_resource_monitor(limits: ResourceLimits = None) -> ResourceMonitor:
    """Get or create the global resource monitor."""
    global _global_monitor
    
    with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = ResourceMonitor(limits)
        return _global_monitor


def shutdown_global_resource_monitor():
    """Shutdown the global resource monitor."""
    global _global_monitor
    
    with _monitor_lock:
        if _global_monitor is not None:
            asyncio.create_task(_global_monitor.stop_monitoring())
            _global_monitor = None