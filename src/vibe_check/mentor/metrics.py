"""
Telemetry Metrics Dataclasses

Defines structured data types for collecting and reporting telemetry metrics
from the vibe_check_mentor MCP sampling integration.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RouteType(Enum):
    """Types of routing decisions"""

    STATIC = "static"
    DYNAMIC = "dynamic"
    HYBRID = "hybrid"
    CACHE_HIT = "cache_hit"


@dataclass
class ResponseMetrics:
    """Metrics for a single response generation"""

    timestamp: float
    route_type: RouteType
    latency_ms: float
    success: bool
    intent: str
    query_length: int
    response_length: int
    error_type: Optional[str] = None
    cache_hit: bool = False
    circuit_breaker_state: str = "closed"

    def __post_init__(self):
        """Validate metrics data"""
        if self.latency_ms < 0:
            raise ValueError("Latency cannot be negative")
        if self.query_length < 0:
            raise ValueError("Query length cannot be negative")
        if self.response_length < 0:
            raise ValueError("Response length cannot be negative")


@dataclass
class LatencyStats:
    """Statistical summary of latency measurements"""

    count: int = 0
    mean: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    min: float = float("inf")
    max: float = 0.0

    def update(self, latencies: List[float]):
        """Update stats from a list of latency values"""
        if not latencies:
            return

        self.count = len(latencies)
        sorted_latencies = sorted(latencies)

        self.mean = sum(latencies) / len(latencies)
        self.min = min(latencies)
        self.max = max(latencies)

        # Calculate percentiles
        if len(sorted_latencies) >= 1:
            self.p50 = self._percentile(sorted_latencies, 50)
            self.p95 = self._percentile(sorted_latencies, 95)
            self.p99 = self._percentile(sorted_latencies, 99)

    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile using linear interpolation between values."""
        if not sorted_values:
            return 0.0

        index = (percentile / 100.0) * (len(sorted_values) - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


@dataclass
class RouteMetricsAggregate:
    """Aggregated metrics for a specific route type"""

    route_type: RouteType
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latency_stats: LatencyStats = field(default_factory=LatencyStats)
    error_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    def add_metric(self, metric: ResponseMetrics):
        """Add a single response metric to the aggregate"""
        if metric.route_type != self.route_type:
            return  # Ignore metrics for wrong route type

        self.total_requests += 1

        if metric.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

            # Track error types
            if metric.error_type:
                self.error_counts[metric.error_type] = (
                    self.error_counts.get(metric.error_type, 0) + 1
                )

    def update_latency_stats(self, latencies: List[float]):
        """Update latency statistics from a list of latencies"""
        self.latency_stats.update(latencies)


@dataclass
class TelemetrySummary:
    """Complete telemetry summary for export"""

    timestamp: float
    uptime_seconds: float
    total_requests: int
    total_successes: int
    total_failures: int
    overall_success_rate: float

    # Route-specific metrics
    route_metrics: Dict[str, RouteMetricsAggregate] = field(default_factory=dict)

    # Component-specific metrics
    circuit_breaker_status: Dict[str, Any] = field(default_factory=dict)
    cache_stats: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export"""
        return {
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime_seconds,
            "overview": {
                "total_requests": self.total_requests,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "overall_success_rate": self.overall_success_rate,
                "average_latency_ms": self.average_latency_ms,
                "p95_latency_ms": self.p95_latency_ms,
            },
            "routes": {
                route_type: {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.success_rate,
                    "failure_rate": metrics.failure_rate,
                    "latency": {
                        "count": metrics.latency_stats.count,
                        "mean": metrics.latency_stats.mean,
                        "p50": metrics.latency_stats.p50,
                        "p95": metrics.latency_stats.p95,
                        "p99": metrics.latency_stats.p99,
                        "min": metrics.latency_stats.min,
                        "max": metrics.latency_stats.max,
                    },
                    "errors": metrics.error_counts,
                }
                for route_type, metrics in self.route_metrics.items()
            },
            "components": {
                "circuit_breaker": self.circuit_breaker_status,
                "cache": self.cache_stats,
            },
        }


@dataclass
class TimingContext:
    """Context manager for tracking operation timing"""

    operation_name: str
    start_time: float = field(default_factory=time.time)

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Timing is handled by the calling code
        pass

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        return (time.time() - self.start_time) * 1000
