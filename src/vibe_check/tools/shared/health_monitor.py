"""
Health Monitoring System for Claude CLI

Comprehensive health monitoring and diagnostics for Claude CLI operations.
Tracks performance metrics, failure patterns, and system health indicators.

Part of Phase 2 implementation for issue #102.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, NamedTuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta

from .circuit_breaker import ClaudeCliCircuitBreaker, CircuitBreakerState


logger = logging.getLogger(__name__)


class HealthStatus(NamedTuple):
    """Health status classification."""

    is_healthy: bool
    level: str  # "HEALTHY", "DEGRADED", "UNHEALTHY", "CRITICAL"
    score: float  # 0.0 to 1.0
    issues: List[str]


@dataclass
class PerformanceMetrics:
    """Performance metrics for health assessment."""

    # Response time metrics
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0

    # Throughput metrics
    requests_per_minute: float = 0.0
    successful_requests_per_minute: float = 0.0

    # Error metrics
    error_rate: float = 0.0
    timeout_rate: float = 0.0

    # Recent trends
    trend_direction: str = "STABLE"  # "IMPROVING", "DEGRADING", "STABLE"
    trend_confidence: float = 0.0


@dataclass
class HealthThresholds:
    """Configurable thresholds for health assessment."""

    # Success rate thresholds
    healthy_success_rate: float = 0.95
    degraded_success_rate: float = 0.80
    unhealthy_success_rate: float = 0.50

    # Response time thresholds (seconds)
    healthy_avg_response_time: float = 30.0
    degraded_avg_response_time: float = 60.0
    unhealthy_avg_response_time: float = 120.0

    # Consecutive failure thresholds
    healthy_max_consecutive_failures: int = 2
    degraded_max_consecutive_failures: int = 5
    unhealthy_max_consecutive_failures: int = 10

    # Time without success thresholds (seconds)
    healthy_max_time_without_success: float = 300  # 5 minutes
    degraded_max_time_without_success: float = 900  # 15 minutes
    unhealthy_max_time_without_success: float = 1800  # 30 minutes


@dataclass
class CallRecord:
    """Record of a single Claude CLI call."""

    timestamp: float
    success: bool
    duration: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    timeout: bool = False


class ClaudeCliHealthMonitor:
    """
    Comprehensive health monitor for Claude CLI operations.

    Tracks performance metrics, failure patterns, and provides
    health assessments with actionable recommendations.
    """

    def __init__(
        self,
        circuit_breaker: ClaudeCliCircuitBreaker,
        thresholds: Optional[HealthThresholds] = None,
        history_size: int = 1000,
    ):
        self.circuit_breaker = circuit_breaker
        self.thresholds = thresholds or HealthThresholds()
        self.history_size = history_size

        # Call history for detailed analysis
        self.call_history: deque[CallRecord] = deque(maxlen=history_size)

        # Real-time metrics
        self.current_metrics = PerformanceMetrics()

        # Health assessment cache
        self._last_health_check: Optional[float] = None
        self._cached_health_status: Optional[HealthStatus] = None
        self._health_cache_duration = 30.0  # seconds

        logger.info(
            f"Health monitor initialized for circuit breaker '{circuit_breaker.name}'",
            extra={
                "history_size": history_size,
                "thresholds": self.thresholds.__dict__,
            },
        )

    def record_call(
        self,
        success: bool,
        duration: float,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        timeout: bool = False,
    ):
        """Record a Claude CLI call for health monitoring."""
        record = CallRecord(
            timestamp=time.time(),
            success=success,
            duration=duration,
            error_type=error_type,
            error_message=error_message,
            timeout=timeout,
        )

        self.call_history.append(record)
        self._update_metrics()

        # Invalidate health cache
        self._cached_health_status = None

        logger.debug(
            f"Call recorded: success={success}, duration={duration:.2f}s",
            extra={
                "success": success,
                "duration": duration,
                "error_type": error_type,
                "timeout": timeout,
            },
        )

    def _update_metrics(self):
        """Update current performance metrics from call history."""
        if not self.call_history:
            return

        # Get recent calls (last 5 minutes)
        cutoff_time = time.time() - 300
        recent_calls = [
            call for call in self.call_history if call.timestamp >= cutoff_time
        ]

        if not recent_calls:
            return

        # Calculate response time metrics
        durations = [call.duration for call in recent_calls]
        durations.sort()

        self.current_metrics.avg_response_time = sum(durations) / len(durations)
        self.current_metrics.min_response_time = min(durations)
        self.current_metrics.max_response_time = max(durations)

        # Calculate percentiles
        if len(durations) >= 20:  # Only calculate percentiles with sufficient data
            p95_idx = int(0.95 * len(durations))
            p99_idx = int(0.99 * len(durations))
            self.current_metrics.p95_response_time = durations[p95_idx]
            self.current_metrics.p99_response_time = durations[p99_idx]

        # Calculate rates
        successful_calls = [call for call in recent_calls if call.success]
        timeout_calls = [call for call in recent_calls if call.timeout]

        time_span = 300  # 5 minutes
        self.current_metrics.requests_per_minute = len(recent_calls) * 60 / time_span
        self.current_metrics.successful_requests_per_minute = (
            len(successful_calls) * 60 / time_span
        )

        # Calculate error rates
        total_calls = len(recent_calls)
        if total_calls > 0:
            self.current_metrics.error_rate = (
                total_calls - len(successful_calls)
            ) / total_calls
            self.current_metrics.timeout_rate = len(timeout_calls) / total_calls

        # Analyze trends
        self._analyze_trends()

    def _analyze_trends(self):
        """Analyze recent trends in performance."""
        if len(self.call_history) < 20:
            self.current_metrics.trend_direction = "STABLE"
            self.current_metrics.trend_confidence = 0.0
            return

        # Split recent history into two halves
        recent_calls = list(self.call_history)[-20:]
        first_half = recent_calls[:10]
        second_half = recent_calls[10:]

        # Compare success rates
        first_success_rate = sum(1 for call in first_half if call.success) / len(
            first_half
        )
        second_success_rate = sum(1 for call in second_half if call.success) / len(
            second_half
        )

        # Compare average response times
        first_avg_time = sum(call.duration for call in first_half) / len(first_half)
        second_avg_time = sum(call.duration for call in second_half) / len(second_half)

        # Determine trend
        success_rate_diff = second_success_rate - first_success_rate
        response_time_diff = second_avg_time - first_avg_time

        # Weighted scoring (success rate is more important)
        trend_score = (success_rate_diff * 0.7) - (response_time_diff / 60.0 * 0.3)

        if abs(trend_score) < 0.05:
            self.current_metrics.trend_direction = "STABLE"
        elif trend_score > 0:
            self.current_metrics.trend_direction = "IMPROVING"
        else:
            self.current_metrics.trend_direction = "DEGRADING"

        self.current_metrics.trend_confidence = min(abs(trend_score) * 2, 1.0)

    def get_health_status(self, force_refresh: bool = False) -> HealthStatus:
        """
        Get current health status with caching.

        Args:
            force_refresh: Force recalculation ignoring cache

        Returns:
            Current health status
        """
        current_time = time.time()

        # Return cached result if still valid
        if (
            not force_refresh
            and self._cached_health_status
            and self._last_health_check
            and current_time - self._last_health_check < self._health_cache_duration
        ):
            return self._cached_health_status

        # Calculate fresh health status
        health_status = self._calculate_health_status()

        # Cache the result
        self._cached_health_status = health_status
        self._last_health_check = current_time

        return health_status

    def _calculate_health_status(self) -> HealthStatus:
        """Calculate current health status based on multiple factors."""
        issues = []
        health_score = 1.0

        # Factor 1: Circuit breaker state
        if self.circuit_breaker.state == CircuitBreakerState.OPEN:
            issues.append("Circuit breaker is OPEN - service unavailable")
            health_score *= 0.0
        elif self.circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            issues.append("Circuit breaker is HALF_OPEN - testing recovery")
            health_score *= 0.5

        # Factor 2: Success rate
        success_rate = self.circuit_breaker.stats.success_rate
        if success_rate < self.thresholds.unhealthy_success_rate:
            issues.append(f"Low success rate: {success_rate:.1%}")
            health_score *= 0.2
        elif success_rate < self.thresholds.degraded_success_rate:
            issues.append(f"Degraded success rate: {success_rate:.1%}")
            health_score *= 0.6
        elif success_rate < self.thresholds.healthy_success_rate:
            health_score *= 0.8

        # Factor 3: Consecutive failures
        consecutive_failures = self.circuit_breaker.stats.consecutive_failures
        if consecutive_failures >= self.thresholds.unhealthy_max_consecutive_failures:
            issues.append(f"High consecutive failures: {consecutive_failures}")
            health_score *= 0.1
        elif consecutive_failures >= self.thresholds.degraded_max_consecutive_failures:
            issues.append(f"Elevated consecutive failures: {consecutive_failures}")
            health_score *= 0.5
        elif consecutive_failures >= self.thresholds.healthy_max_consecutive_failures:
            health_score *= 0.7

        # Factor 4: Time since last success
        if self.circuit_breaker.stats.last_success_time:
            time_since_success = (
                time.time() - self.circuit_breaker.stats.last_success_time
            )
            if time_since_success > self.thresholds.unhealthy_max_time_without_success:
                issues.append(f"No success for {time_since_success/60:.1f} minutes")
                health_score *= 0.1
            elif time_since_success > self.thresholds.degraded_max_time_without_success:
                issues.append(
                    f"No recent success ({time_since_success/60:.1f} minutes)"
                )
                health_score *= 0.4
            elif time_since_success > self.thresholds.healthy_max_time_without_success:
                health_score *= 0.7

        # Factor 5: Response time performance
        avg_response_time = self.current_metrics.avg_response_time
        if avg_response_time > self.thresholds.unhealthy_avg_response_time:
            issues.append(f"Slow response time: {avg_response_time:.1f}s")
            health_score *= 0.6
        elif avg_response_time > self.thresholds.degraded_avg_response_time:
            issues.append(f"Elevated response time: {avg_response_time:.1f}s")
            health_score *= 0.8
        elif avg_response_time > self.thresholds.healthy_avg_response_time:
            health_score *= 0.9

        # Factor 6: Trend analysis
        if self.current_metrics.trend_direction == "DEGRADING":
            trend_impact = 1.0 - (self.current_metrics.trend_confidence * 0.2)
            health_score *= trend_impact
            if self.current_metrics.trend_confidence > 0.5:
                issues.append("Performance trending downward")

        # Determine health level
        if health_score >= 0.9:
            level = "HEALTHY"
            is_healthy = True
        elif health_score >= 0.7:
            level = "DEGRADED"
            is_healthy = False
        elif health_score >= 0.3:
            level = "UNHEALTHY"
            is_healthy = False
        else:
            level = "CRITICAL"
            is_healthy = False

        return HealthStatus(
            is_healthy=is_healthy, level=level, score=health_score, issues=issues
        )

    def get_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report."""
        health_status = self.get_health_status(force_refresh=True)
        circuit_breaker_status = self.circuit_breaker.get_status()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": {
                "is_healthy": health_status.is_healthy,
                "level": health_status.level,
                "score": health_status.score,
                "issues": health_status.issues,
            },
            "performance_metrics": {
                "avg_response_time": self.current_metrics.avg_response_time,
                "p95_response_time": self.current_metrics.p95_response_time,
                "p99_response_time": self.current_metrics.p99_response_time,
                "requests_per_minute": self.current_metrics.requests_per_minute,
                "error_rate": self.current_metrics.error_rate,
                "timeout_rate": self.current_metrics.timeout_rate,
                "trend_direction": self.current_metrics.trend_direction,
                "trend_confidence": self.current_metrics.trend_confidence,
            },
            "circuit_breaker": circuit_breaker_status,
            "call_history_summary": {
                "total_calls": len(self.call_history),
                "recent_calls_5min": len(
                    [
                        call
                        for call in self.call_history
                        if call.timestamp >= time.time() - 300
                    ]
                ),
                "oldest_record": (
                    datetime.fromtimestamp(self.call_history[0].timestamp).isoformat()
                    if self.call_history
                    else None
                ),
                "newest_record": (
                    datetime.fromtimestamp(self.call_history[-1].timestamp).isoformat()
                    if self.call_history
                    else None
                ),
            },
            "recommendations": self._generate_recommendations(health_status),
        }

    def _generate_recommendations(self, health_status: HealthStatus) -> List[str]:
        """Generate actionable recommendations based on health status."""
        recommendations = []

        if health_status.level == "CRITICAL":
            recommendations.extend(
                [
                    "Immediate attention required - service is severely degraded",
                    "Check Claude CLI authentication and connectivity",
                    "Consider manual intervention or service restart",
                    "Review recent error logs for patterns",
                ]
            )
        elif health_status.level == "UNHEALTHY":
            recommendations.extend(
                [
                    "Service is experiencing significant issues",
                    "Monitor circuit breaker recovery",
                    "Check for network or authentication problems",
                    "Consider reducing load if possible",
                ]
            )
        elif health_status.level == "DEGRADED":
            recommendations.extend(
                [
                    "Service performance is below optimal",
                    "Monitor for further degradation",
                    "Check system resources and dependencies",
                    "Review recent changes that might impact performance",
                ]
            )
        else:
            recommendations.append("Service is operating normally")

        # Specific recommendations based on issues
        for issue in health_status.issues:
            if "success rate" in issue.lower():
                recommendations.append(
                    "Review error patterns and implement targeted fixes"
                )
            elif "response time" in issue.lower():
                recommendations.append("Investigate performance bottlenecks")
            elif "consecutive failures" in issue.lower():
                recommendations.append(
                    "Check for persistent issues requiring intervention"
                )
            elif "trending downward" in issue.lower():
                recommendations.append(
                    "Investigate recent changes that may impact performance"
                )

        return list(set(recommendations))  # Remove duplicates
