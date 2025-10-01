"""
Basic Telemetry System for Vibe Check Mentor

Provides minimal telemetry collection for MCP sampling integration without
over-engineering. Focuses on essential metrics only.
"""

import time
import logging
import functools
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from threading import Lock

from .metrics import (
    ResponseMetrics,
    RouteMetricsAggregate,
    TelemetrySummary,
    LatencyStats,
    RouteType,
    TimingContext,
)

logger = logging.getLogger(__name__)


class BasicTelemetryCollector:
    """
    Minimal telemetry collector that aggregates metrics without external dependencies.

    Designed for simplicity and low overhead (<5% performance impact).
    """

    def __init__(self, max_metrics_history: int = 1000):
        """
        Initialize telemetry collector

        Args:
            max_metrics_history: Maximum number of recent metrics to keep in memory
        """
        self.max_metrics_history = max_metrics_history
        self.start_time = time.time()

        # Thread-safe collections
        self._lock = Lock()

        # Recent metrics (sliding window)
        self._recent_metrics: deque = deque(maxlen=max_metrics_history)

        # Aggregated metrics by route type
        self._route_aggregates: Dict[RouteType, RouteMetricsAggregate] = {
            route_type: RouteMetricsAggregate(route_type=route_type)
            for route_type in RouteType
        }

        # Component references (set during integration)
        self._circuit_breaker = None
        self._cache = None

        logger.info(
            f"BasicTelemetryCollector initialized with {max_metrics_history} max history"
        )

    def set_circuit_breaker(self, circuit_breaker):
        """Set reference to circuit breaker for status monitoring"""
        self._circuit_breaker = circuit_breaker

    def set_cache(self, cache):
        """Set reference to response cache for statistics"""
        self._cache = cache

    def record_response(
        self,
        route_type: RouteType,
        latency_ms: float,
        success: bool,
        intent: str,
        query_length: int,
        response_length: int = 0,
        error_type: Optional[str] = None,
        cache_hit: bool = False,
    ):
        """
        Record a response metric

        Args:
            route_type: Type of routing decision made
            latency_ms: Response latency in milliseconds
            success: Whether the response was successful
            intent: Detected intent type
            query_length: Length of the user query
            response_length: Length of the generated response
            error_type: Type of error if success=False
            cache_hit: Whether this was a cache hit
        """
        try:
            with self._lock:
                # Create metric record with validation
                try:
                    metric = ResponseMetrics(
                        timestamp=time.time(),
                        route_type=route_type,
                        latency_ms=max(0.0, float(latency_ms)),  # Ensure non-negative
                        success=bool(success),
                        intent=str(intent)[:100],  # Limit intent length
                        query_length=max(0, int(query_length)),
                        response_length=max(0, int(response_length)),
                        error_type=(
                            str(error_type)[:50] if error_type else None
                        ),  # Limit error type
                        cache_hit=bool(cache_hit),
                        circuit_breaker_state=self._get_circuit_breaker_state(),
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create metric record: {e} (route={route_type}, latency={latency_ms})"
                    )
                    return  # Graceful failure

                # Add to recent metrics (thread-safe due to deque)
                self._recent_metrics.append(metric)

                # Update aggregates (atomic operation)
                try:
                    self._route_aggregates[route_type].add_metric(metric)
                except Exception as e:
                    logger.warning(f"Failed to update route aggregates: {e}")

                # Update latency stats for this route type (optimized)
                if success:  # Only update stats for successful requests
                    try:
                        # Get successful latencies for this route type
                        route_latencies = [
                            m.latency_ms
                            for m in list(self._recent_metrics)  # Create snapshot
                            if m.route_type == route_type and m.success
                        ]
                        if route_latencies:  # Only update if we have data
                            self._route_aggregates[route_type].update_latency_stats(
                                route_latencies
                            )
                    except Exception as e:
                        logger.warning(f"Failed to update latency stats: {e}")

                logger.debug(
                    f"Recorded {route_type.value} response: {latency_ms:.1f}ms, success={success}"
                )

        except Exception as e:
            logger.error(f"Telemetry recording failed: {e}")
            # Don't propagate telemetry errors to main application

    def get_summary(self) -> TelemetrySummary:
        """
        Get complete telemetry summary for export

        Returns:
            TelemetrySummary with all current metrics
        """
        try:
            with self._lock:
                # Calculate overall stats with error handling
                try:
                    total_requests = sum(
                        agg.total_requests for agg in self._route_aggregates.values()
                    )
                    total_successes = sum(
                        agg.successful_requests
                        for agg in self._route_aggregates.values()
                    )
                    total_failures = sum(
                        agg.failed_requests for agg in self._route_aggregates.values()
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate request totals: {e}")
                    total_requests = total_successes = total_failures = 0

                overall_success_rate = (
                    (total_successes / total_requests * 100)
                    if total_requests > 0
                    else 0.0
                )

                # Calculate overall latency stats with optimization
                overall_latency_stats = LatencyStats()
                try:
                    # Create snapshot to avoid lock contention during calculation
                    metrics_snapshot = list(self._recent_metrics)
                    all_successful_latencies = [
                        m.latency_ms
                        for m in metrics_snapshot
                        if m.success and m.latency_ms >= 0
                    ]
                    if all_successful_latencies:
                        overall_latency_stats.update(all_successful_latencies)
                except Exception as e:
                    logger.warning(f"Failed to calculate latency stats: {e}")

                # Get component status with error handling
                try:
                    circuit_breaker_status = self._get_circuit_breaker_status()
                    cache_stats = self._get_cache_stats()
                except Exception as e:
                    logger.warning(f"Failed to get component status: {e}")
                    circuit_breaker_status = {"state": "error", "error": str(e)}
                    cache_stats = {"status": "error", "error": str(e)}

                return TelemetrySummary(
                    timestamp=time.time(),
                    uptime_seconds=time.time() - self.start_time,
                    total_requests=total_requests,
                    total_successes=total_successes,
                    total_failures=total_failures,
                    overall_success_rate=overall_success_rate,
                    route_metrics={
                        route_type.value: aggregate
                        for route_type, aggregate in self._route_aggregates.items()
                    },
                    circuit_breaker_status=circuit_breaker_status,
                    cache_stats=cache_stats,
                    average_latency_ms=overall_latency_stats.mean,
                    p95_latency_ms=overall_latency_stats.p95,
                )

        except Exception as e:
            logger.error(f"Failed to generate telemetry summary: {e}")
            # Return minimal summary on error
            return TelemetrySummary(
                timestamp=time.time(),
                uptime_seconds=time.time() - self.start_time,
                total_requests=0,
                total_successes=0,
                total_failures=0,
                overall_success_rate=0.0,
                route_metrics={},
                circuit_breaker_status={"state": "error", "error": str(e)},
                cache_stats={"status": "error", "error": str(e)},
                average_latency_ms=0.0,
                p95_latency_ms=0.0,
            )

    def get_recent_metrics(self, count: int = 100) -> List[ResponseMetrics]:
        """
        Get recent response metrics

        Args:
            count: Maximum number of recent metrics to return

        Returns:
            List of recent ResponseMetrics
        """
        with self._lock:
            recent = list(self._recent_metrics)
            return recent[-count:] if len(recent) > count else recent

    def get_stats_for_route(self, route_type: RouteType) -> RouteMetricsAggregate:
        """
        Get aggregated stats for a specific route type

        Args:
            route_type: Route type to get stats for

        Returns:
            RouteMetricsAggregate for the specified route
        """
        with self._lock:
            return self._route_aggregates[route_type]

    def reset_metrics(self):
        """Reset all collected metrics (useful for testing)"""
        with self._lock:
            self._recent_metrics.clear()
            self._route_aggregates = {
                route_type: RouteMetricsAggregate(route_type=route_type)
                for route_type in RouteType
            }
            self.start_time = time.time()
            logger.info("Telemetry metrics reset")

    def _get_circuit_breaker_state(self) -> str:
        """Get current circuit breaker state"""
        if self._circuit_breaker:
            return self._circuit_breaker.state.value
        return "unknown"

    def _get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get detailed circuit breaker status"""
        if self._circuit_breaker:
            status = self._circuit_breaker.get_status()
            status["last_checked"] = time.time()
            return status
        return {"state": "not_available", "last_checked": time.time()}

    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self._cache:
            return self._cache.get_stats()
        return {"status": "not_available"}


# Constants for security
MAX_QUERY_LENGTH = 10000  # 10KB limit for DoS protection
MAX_RESPONSE_LENGTH = 50000  # 50KB limit for response tracking

# Global telemetry collector instance
_global_collector = BasicTelemetryCollector()


def get_telemetry_collector() -> BasicTelemetryCollector:
    """Get the global telemetry collector instance"""
    return _global_collector


def track_latency(
    route_type: RouteType, intent: Optional[str] = None, record_success: bool = True
):
    """
    Decorator to track latency of function calls

    Args:
        route_type: Type of route being tracked
        intent: Optional intent type (will use function name if not provided)
        record_success: Whether to record the operation as successful by default

    Example:
        @track_latency(RouteType.DYNAMIC, intent="architecture_decision")
        async def generate_dynamic_response(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = record_success
            error_type = None
            response_length = 0

            # Try to extract query length from args/kwargs with bounds checking
            query_length = 0
            try:
                if args and isinstance(args[0], str):
                    query_length = min(len(args[0]), MAX_QUERY_LENGTH)
                elif "query" in kwargs and isinstance(kwargs["query"], str):
                    query_length = min(len(kwargs["query"]), MAX_QUERY_LENGTH)
            except (AttributeError, TypeError):
                query_length = 0  # Graceful fallback

            try:
                result = await func(*args, **kwargs)

                # Try to extract response length from result with bounds checking
                try:
                    if isinstance(result, dict) and "content" in result:
                        response_length = min(
                            len(str(result["content"])), MAX_RESPONSE_LENGTH
                        )
                    elif isinstance(result, str):
                        response_length = min(len(result), MAX_RESPONSE_LENGTH)
                    elif result is not None:
                        response_length = min(len(str(result)), MAX_RESPONSE_LENGTH)
                except (TypeError, AttributeError):
                    response_length = 0  # Graceful fallback

                return result

            except Exception as e:
                success = False
                error_type = type(e).__name__
                logger.error(f"Error in {func.__name__}: {e}")
                raise

            finally:
                latency_ms = (time.time() - start_time) * 1000

                _global_collector.record_response(
                    route_type=route_type,
                    latency_ms=latency_ms,
                    success=success,
                    intent=intent or func.__name__,
                    query_length=query_length,
                    response_length=response_length,
                    error_type=error_type,
                    cache_hit=False,  # Will be updated by cache layer if applicable
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = record_success
            error_type = None
            response_length = 0

            # Try to extract query length with bounds checking
            query_length = 0
            try:
                if args and isinstance(args[0], str):
                    query_length = min(len(args[0]), MAX_QUERY_LENGTH)
                elif "query" in kwargs and isinstance(kwargs["query"], str):
                    query_length = min(len(kwargs["query"]), MAX_QUERY_LENGTH)
            except (AttributeError, TypeError):
                query_length = 0  # Graceful fallback

            try:
                result = func(*args, **kwargs)

                # Try to extract response length with bounds checking
                try:
                    if isinstance(result, dict) and "content" in result:
                        response_length = min(
                            len(str(result["content"])), MAX_RESPONSE_LENGTH
                        )
                    elif isinstance(result, str):
                        response_length = min(len(result), MAX_RESPONSE_LENGTH)
                    elif result is not None:
                        response_length = min(len(str(result)), MAX_RESPONSE_LENGTH)
                except (TypeError, AttributeError):
                    response_length = 0  # Graceful fallback

                return result

            except Exception as e:
                success = False
                error_type = type(e).__name__
                logger.error(f"Error in {func.__name__}: {e}")
                raise

            finally:
                latency_ms = (time.time() - start_time) * 1000

                _global_collector.record_response(
                    route_type=route_type,
                    latency_ms=latency_ms,
                    success=success,
                    intent=intent or func.__name__,
                    query_length=query_length,
                    response_length=response_length,
                    error_type=error_type,
                    cache_hit=False,
                )

        # Return appropriate wrapper based on function type
        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class TelemetryContext:
    """Context manager for manual telemetry tracking"""

    def __init__(self, route_type: RouteType, intent: str, query_length: int = 0):
        self.route_type = route_type
        self.intent = intent
        self.query_length = query_length
        self.start_time = 0.0
        self.success = True
        self.error_type = None
        self.response_length = 0
        self.cache_hit = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000

        if exc_type is not None:
            self.success = False
            self.error_type = exc_type.__name__

        _global_collector.record_response(
            route_type=self.route_type,
            latency_ms=latency_ms,
            success=self.success,
            intent=self.intent,
            query_length=self.query_length,
            response_length=self.response_length,
            error_type=self.error_type,
            cache_hit=self.cache_hit,
        )

    def set_cache_hit(self, cache_hit: bool):
        """Mark this operation as a cache hit/miss"""
        self.cache_hit = cache_hit

    def set_response_length(self, length: int):
        """Set the response length for this operation"""
        self.response_length = length
