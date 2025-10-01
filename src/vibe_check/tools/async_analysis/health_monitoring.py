"""
Health Monitoring and Metrics for Async Analysis System

Provides comprehensive health checks, metrics collection, and system diagnostics
for the async analysis infrastructure.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    component: str
    status: str  # "healthy", "warning", "critical", "unavailable"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "response_time_ms": round(self.response_time_ms, 2),
            "timestamp": self.timestamp,
        }


@dataclass
class SystemMetrics:
    """System performance metrics."""

    # Queue metrics
    queue_size: int = 0
    active_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0

    # Performance metrics
    average_job_duration_seconds: float = 0.0
    success_rate_percent: float = 100.0
    throughput_jobs_per_hour: float = 0.0

    # Resource metrics
    system_memory_percent: float = 0.0
    system_cpu_percent: float = 0.0
    active_workers: int = 0

    # Health status
    overall_health: str = "healthy"  # "healthy", "warning", "critical"
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "queue_metrics": {
                "queue_size": self.queue_size,
                "active_jobs": self.active_jobs,
                "completed_jobs": self.completed_jobs,
                "failed_jobs": self.failed_jobs,
            },
            "performance_metrics": {
                "average_job_duration_seconds": round(
                    self.average_job_duration_seconds, 2
                ),
                "success_rate_percent": round(self.success_rate_percent, 2),
                "throughput_jobs_per_hour": round(self.throughput_jobs_per_hour, 2),
            },
            "resource_metrics": {
                "system_memory_percent": round(self.system_memory_percent, 2),
                "system_cpu_percent": round(self.system_cpu_percent, 2),
                "active_workers": self.active_workers,
            },
            "overall_health": self.overall_health,
            "last_updated": self.last_updated,
        }


class HealthMonitor:
    """
    Comprehensive health monitoring for async analysis system.

    Provides health checks, metrics collection, and alerting for
    system components including queue, workers, and resources.
    """

    def __init__(self):
        self.health_history: List[Dict[str, HealthCheckResult]] = []
        self.metrics_history: List[SystemMetrics] = []
        self.last_health_check: float = 0
        self.alerts: List[Dict[str, Any]] = []

        logger.info("HealthMonitor initialized")

    async def perform_comprehensive_health_check(self) -> Dict[str, HealthCheckResult]:
        """
        Perform comprehensive health check of all system components.

        Returns:
            Dictionary of component -> health check result
        """
        results = {}
        start_time = time.time()

        # Check async system initialization
        results["system_initialization"] = await self._check_system_initialization()

        # Check queue health
        results["queue_system"] = await self._check_queue_health()

        # Check worker health
        results["worker_system"] = await self._check_worker_health()

        # Check resource monitoring
        results["resource_monitoring"] = await self._check_resource_monitoring()

        # Check external dependencies
        results["github_api"] = await self._check_github_api()

        # Store results in history
        self.health_history.append(results)
        if len(self.health_history) > 100:  # Keep last 100 checks
            self.health_history.pop(0)

        self.last_health_check = time.time()

        # Check for alerts
        await self._process_health_alerts(results)

        total_time = (time.time() - start_time) * 1000
        logger.info(f"Health check completed in {total_time:.2f}ms")

        return results

    async def collect_system_metrics(self) -> SystemMetrics:
        """
        Collect comprehensive system metrics.

        Returns:
            Current system metrics
        """
        metrics = SystemMetrics()

        try:
            # Get async system status if available
            from .integration import get_system_status, _system_initialized

            if _system_initialized:
                system_status = await get_system_status()

                # Extract queue metrics
                if "queue_overview" in system_status:
                    queue_info = system_status["queue_overview"]
                    metrics.queue_size = queue_info.get("pending_jobs", 0)
                    metrics.active_jobs = queue_info.get("active_jobs", 0)

                # Extract worker metrics
                if "worker_status" in system_status:
                    worker_info = system_status["worker_status"]
                    metrics.active_workers = len(worker_info.get("workers", []))

                # Extract resource metrics
                if "resource_monitoring" in system_status:
                    resource_info = system_status["resource_monitoring"]
                    system_check = resource_info.get("system_status", {})
                    if "current_usage" in system_check:
                        usage = system_check["current_usage"]
                        metrics.system_memory_percent = usage.get("memory_percent", 0)
                        metrics.system_cpu_percent = usage.get("cpu_percent", 0)

                    # Determine overall health
                    if not system_check.get("within_limits", True):
                        metrics.overall_health = "critical"
                    elif system_check.get("warnings", []):
                        metrics.overall_health = "warning"

            # Get performance metrics from global metrics
            from .config import ASYNC_METRICS

            metrics_data = ASYNC_METRICS.to_dict()

            metrics.completed_jobs = metrics_data.get("jobs_completed", 0)
            metrics.failed_jobs = metrics_data.get("jobs_failed", 0)
            metrics.success_rate_percent = metrics_data.get(
                "success_rate_percent", 100.0
            )
            metrics.average_job_duration_seconds = metrics_data.get(
                "average_duration_seconds", 0.0
            )

            # Calculate throughput (jobs per hour)
            if metrics.completed_jobs > 0 and metrics.average_job_duration_seconds > 0:
                metrics.throughput_jobs_per_hour = (
                    3600 / metrics.average_job_duration_seconds
                )

        except Exception as e:
            logger.warning(f"Error collecting metrics: {e}")
            metrics.overall_health = "warning"

        # Store metrics in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:  # Keep last 1000 metrics
            self.metrics_history.pop(0)

        return metrics

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of system health status.

        Returns:
            Health summary with key indicators
        """
        if not self.health_history:
            return {
                "status": "unknown",
                "message": "No health checks performed yet",
                "last_check": None,
            }

        latest_results = self.health_history[-1]

        # Determine overall status
        critical_count = sum(
            1 for r in latest_results.values() if r.status == "critical"
        )
        warning_count = sum(1 for r in latest_results.values() if r.status == "warning")

        if critical_count > 0:
            overall_status = "critical"
            message = f"{critical_count} critical issues detected"
        elif warning_count > 0:
            overall_status = "warning"
            message = f"{warning_count} warnings detected"
        else:
            overall_status = "healthy"
            message = "All systems operational"

        return {
            "status": overall_status,
            "message": message,
            "last_check": self.last_health_check,
            "components": {
                name: result.status for name, result in latest_results.items()
            },
            "alerts": len(self.alerts),
            "uptime_checks": len(self.health_history),
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of system metrics.

        Returns:
            Metrics summary with trends
        """
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics collected yet"}

        latest = self.metrics_history[-1]

        # Calculate trends if we have enough data
        trends = {}
        if len(self.metrics_history) >= 10:
            recent_10 = self.metrics_history[-10:]
            oldest_10 = (
                self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else []
            )

            if oldest_10:
                # Calculate average job duration trend
                recent_avg_duration = sum(
                    m.average_job_duration_seconds for m in recent_10
                ) / len(recent_10)
                old_avg_duration = sum(
                    m.average_job_duration_seconds for m in oldest_10
                ) / len(oldest_10)

                if old_avg_duration > 0:
                    duration_trend = (
                        (recent_avg_duration - old_avg_duration) / old_avg_duration
                    ) * 100
                    trends["duration_change_percent"] = round(duration_trend, 2)

                # Calculate success rate trend
                recent_success = sum(m.success_rate_percent for m in recent_10) / len(
                    recent_10
                )
                old_success = sum(m.success_rate_percent for m in oldest_10) / len(
                    oldest_10
                )

                success_trend = recent_success - old_success
                trends["success_rate_change"] = round(success_trend, 2)

        return {
            "current_metrics": latest.to_dict(),
            "trends": trends,
            "data_points": len(self.metrics_history),
            "collection_time": latest.last_updated,
        }

    async def _check_system_initialization(self) -> HealthCheckResult:
        """Check if async system is properly initialized."""
        start_time = time.time()

        try:
            from .integration import _system_initialized

            if _system_initialized:
                status = "healthy"
                message = "Async analysis system initialized and running"
            else:
                status = "unavailable"
                message = "Async analysis system not initialized"

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="system_initialization",
                status=status,
                message=message,
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="system_initialization",
                status="critical",
                message=f"Error checking system initialization: {str(e)}",
                response_time_ms=response_time,
            )

    async def _check_queue_health(self) -> HealthCheckResult:
        """Check queue system health."""
        start_time = time.time()

        try:
            from .queue_manager import get_global_queue

            queue = await get_global_queue()
            queue_size = queue.job_queue.qsize()
            max_size = queue.config.max_queue_size

            utilization = (queue_size / max_size) * 100

            if utilization > 90:
                status = "critical"
                message = (
                    f"Queue nearly full: {queue_size}/{max_size} ({utilization:.1f}%)"
                )
            elif utilization > 70:
                status = "warning"
                message = f"Queue high utilization: {queue_size}/{max_size} ({utilization:.1f}%)"
            else:
                status = "healthy"
                message = f"Queue normal: {queue_size}/{max_size} ({utilization:.1f}%)"

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="queue_system",
                status=status,
                message=message,
                details={
                    "queue_size": queue_size,
                    "max_size": max_size,
                    "utilization_percent": round(utilization, 2),
                    "active_jobs": len(queue.active_jobs),
                },
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="queue_system",
                status="critical",
                message=f"Queue health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def _check_worker_health(self) -> HealthCheckResult:
        """Check worker system health."""
        start_time = time.time()

        try:
            from .worker import get_global_worker_manager
            from .queue_manager import get_global_queue

            queue = await get_global_queue()
            worker_manager = await get_global_worker_manager(queue)
            worker_status = worker_manager.get_worker_status()

            active_workers = len(worker_status.get("workers", []))
            expected_workers = worker_manager.config.max_concurrent_workers

            if active_workers == 0:
                status = "critical"
                message = "No workers running"
            elif active_workers < expected_workers:
                status = "warning"
                message = f"Reduced workers: {active_workers}/{expected_workers}"
            else:
                status = "healthy"
                message = f"All workers running: {active_workers}/{expected_workers}"

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="worker_system",
                status=status,
                message=message,
                details={
                    "active_workers": active_workers,
                    "expected_workers": expected_workers,
                    "worker_details": worker_status.get("workers", []),
                },
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="worker_system",
                status="critical",
                message=f"Worker health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def _check_resource_monitoring(self) -> HealthCheckResult:
        """Check resource monitoring health."""
        start_time = time.time()

        try:
            from .resource_monitor import get_global_resource_monitor

            monitor = get_global_resource_monitor()
            status_info = monitor.get_comprehensive_status()

            if not status_info["monitoring_active"]:
                status = "warning"
                message = "Resource monitoring not active"
            elif status_info["total_violations"] > 0:
                status = "warning"
                message = (
                    f"Resource violations detected: {status_info['total_violations']}"
                )
            else:
                status = "healthy"
                message = "Resource monitoring operational"

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="resource_monitoring",
                status=status,
                message=message,
                details={
                    "monitoring_active": status_info["monitoring_active"],
                    "job_count": status_info["job_count"],
                    "total_violations": status_info["total_violations"],
                },
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="resource_monitoring",
                status="warning",
                message=f"Resource monitoring check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def _check_github_api(self) -> HealthCheckResult:
        """Check GitHub API connectivity."""
        start_time = time.time()

        try:
            from ..shared.github_abstraction import get_default_github_operations

            github_ops = get_default_github_operations()
            auth_result = github_ops.check_authentication()

            if auth_result.success:
                status = "healthy"
                message = "GitHub API authentication successful"
            else:
                status = "critical"
                message = f"GitHub API authentication failed: {auth_result.error}"

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="github_api",
                status=status,
                message=message,
                details={
                    "authenticated": auth_result.success,
                    "implementation": (
                        auth_result.data.get("implementation")
                        if auth_result.data
                        else None
                    ),
                },
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="github_api",
                status="critical",
                message=f"GitHub API check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def _process_health_alerts(self, results: Dict[str, HealthCheckResult]):
        """Process health check results and generate alerts."""
        for component, result in results.items():
            if result.status in ["critical", "warning"]:
                alert = {
                    "timestamp": result.timestamp,
                    "component": component,
                    "severity": result.status,
                    "message": result.message,
                    "details": result.details,
                }

                # Avoid duplicate alerts for the same issue
                recent_alerts = [
                    a for a in self.alerts if time.time() - a["timestamp"] < 300
                ]  # Last 5 minutes
                duplicate = any(
                    a["component"] == component and a["severity"] == result.status
                    for a in recent_alerts
                )

                if not duplicate:
                    self.alerts.append(alert)
                    logger.warning(f"Health alert: {component} - {result.message}")

        # Keep only recent alerts
        cutoff_time = time.time() - 3600  # Last hour
        self.alerts = [a for a in self.alerts if a["timestamp"] > cutoff_time]


# Global health monitor instance
_global_health_monitor: Optional[HealthMonitor] = None


def get_global_health_monitor() -> HealthMonitor:
    """Get or create the global health monitor."""
    global _global_health_monitor

    if _global_health_monitor is None:
        _global_health_monitor = HealthMonitor()

    return _global_health_monitor
