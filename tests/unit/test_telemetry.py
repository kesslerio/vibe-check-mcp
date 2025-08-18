"""
Comprehensive Unit Tests for Telemetry System

Tests for metrics.py and telemetry.py components that provide telemetry
collection for the vibe_check_mentor MCP sampling integration.

Focus Areas:
- Metric validation and edge cases
- Percentile calculation accuracy 
- Aggregation logic correctness
- Thread safety and performance
- Decorator functionality
- Context manager behavior
"""

import pytest
import time
import asyncio
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import List
import json

from vibe_check.mentor.metrics import (
    ResponseMetrics,
    LatencyStats,
    RouteMetricsAggregate,
    TelemetrySummary,
    TimingContext,
    RouteType
)

from vibe_check.mentor.telemetry import (
    BasicTelemetryCollector,
    get_telemetry_collector,
    track_latency,
    TelemetryContext
)


class TestResponseMetrics:
    """Test ResponseMetrics dataclass validation and behavior."""
    
    def test_valid_response_metrics_creation(self):
        """Test creating valid ResponseMetrics instance."""
        metrics = ResponseMetrics(
            timestamp=time.time(),
            route_type=RouteType.DYNAMIC,
            latency_ms=150.5,
            success=True,
            intent="architecture_decision",
            query_length=100,
            response_length=500
        )
        
        assert metrics.route_type == RouteType.DYNAMIC
        assert metrics.latency_ms == 150.5
        assert metrics.success is True
        assert metrics.intent == "architecture_decision"
        assert metrics.query_length == 100
        assert metrics.response_length == 500
        assert metrics.error_type is None
        assert metrics.cache_hit is False
        assert metrics.circuit_breaker_state == "closed"
    
    def test_response_metrics_validation_negative_latency(self):
        """Test validation fails for negative latency."""
        with pytest.raises(ValueError, match="Latency cannot be negative"):
            ResponseMetrics(
                timestamp=time.time(),
                route_type=RouteType.STATIC,
                latency_ms=-10.0,
                success=True,
                intent="test",
                query_length=50,
                response_length=100
            )
    
    def test_response_metrics_validation_negative_query_length(self):
        """Test validation fails for negative query length."""
        with pytest.raises(ValueError, match="Query length cannot be negative"):
            ResponseMetrics(
                timestamp=time.time(),
                route_type=RouteType.STATIC,
                latency_ms=100.0,
                success=True,
                intent="test",
                query_length=-5,
                response_length=100
            )
    
    def test_response_metrics_validation_negative_response_length(self):
        """Test validation fails for negative response length."""
        with pytest.raises(ValueError, match="Response length cannot be negative"):
            ResponseMetrics(
                timestamp=time.time(),
                route_type=RouteType.STATIC,
                latency_ms=100.0,
                success=True,
                intent="test",
                query_length=50,
                response_length=-10
            )
    
    def test_response_metrics_with_error(self):
        """Test ResponseMetrics with error information."""
        metrics = ResponseMetrics(
            timestamp=time.time(),
            route_type=RouteType.DYNAMIC,
            latency_ms=1000.0,
            success=False,
            intent="failed_request",
            query_length=75,
            response_length=0,
            error_type="TimeoutError",
            cache_hit=False,
            circuit_breaker_state="half_open"
        )
        
        assert metrics.success is False
        assert metrics.error_type == "TimeoutError"
        assert metrics.circuit_breaker_state == "half_open"
        assert metrics.response_length == 0
    
    def test_route_type_enum_values(self):
        """Test all RouteType enum values are supported."""
        for route_type in RouteType:
            metrics = ResponseMetrics(
                timestamp=time.time(),
                route_type=route_type,
                latency_ms=100.0,
                success=True,
                intent="test",
                query_length=50,
                response_length=100
            )
            assert metrics.route_type == route_type


class TestLatencyStats:
    """Test LatencyStats calculations and edge cases."""
    
    def test_empty_latency_stats(self):
        """Test LatencyStats with no data."""
        stats = LatencyStats()
        assert stats.count == 0
        assert stats.mean == 0.0
        assert stats.p50 == 0.0
        assert stats.p95 == 0.0
        assert stats.p99 == 0.0
        assert stats.min == float('inf')
        assert stats.max == 0.0
    
    def test_single_value_latency_stats(self):
        """Test LatencyStats with single value."""
        stats = LatencyStats()
        stats.update([100.0])
        
        assert stats.count == 1
        assert stats.mean == 100.0
        assert stats.p50 == 100.0
        assert stats.p95 == 100.0
        assert stats.p99 == 100.0
        assert stats.min == 100.0
        assert stats.max == 100.0
    
    def test_multiple_values_latency_stats(self):
        """Test LatencyStats with multiple values."""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        stats = LatencyStats()
        stats.update(latencies)
        
        assert stats.count == 10
        assert stats.mean == 55.0
        assert stats.min == 10.0
        assert stats.max == 100.0
        assert stats.p50 == 55.0  # Median of 10 values
        # Allow for floating point precision issues
        assert abs(stats.p95 - 95.5) < 0.01  # 95th percentile
        assert abs(stats.p99 - 99.1) < 0.01  # 99th percentile
    
    def test_percentile_calculation_accuracy(self):
        """Test percentile calculation with known values."""
        # Test with 100 values from 1 to 100
        latencies = list(range(1, 101))  # 1, 2, 3, ..., 100
        stats = LatencyStats()
        stats.update(latencies)
        
        assert stats.count == 100
        assert stats.mean == 50.5
        assert stats.p50 == 50.5  # 50th percentile
        assert stats.p95 == 95.05  # 95th percentile
        assert stats.p99 == 99.01  # 99th percentile
    
    def test_percentile_edge_case_two_values(self):
        """Test percentile calculation with two values."""
        stats = LatencyStats()
        stats.update([10.0, 90.0])
        
        assert stats.count == 2
        assert stats.mean == 50.0
        assert stats.p50 == 50.0  # Interpolated median
        # With only 2 values, percentiles will be calculated differently
        # 95th percentile of [10.0, 90.0] should be close to the higher value
        assert 80.0 <= stats.p95 <= 90.0  # Should be in reasonable range
        assert 85.0 <= stats.p99 <= 90.0  # Should be very close to max
    
    def test_latency_stats_update_empty_list(self):
        """Test updating with empty list does nothing."""
        stats = LatencyStats()
        stats.count = 5
        stats.mean = 100.0
        
        stats.update([])
        
        # Values should remain unchanged
        assert stats.count == 5
        assert stats.mean == 100.0
    
    def test_percentile_calculation_duplicate_values(self):
        """Test percentile calculation with duplicate values."""
        latencies = [50.0] * 10  # All same value
        stats = LatencyStats()
        stats.update(latencies)
        
        assert stats.count == 10
        assert stats.mean == 50.0
        assert stats.p50 == 50.0
        assert stats.p95 == 50.0
        assert stats.p99 == 50.0
        assert stats.min == 50.0
        assert stats.max == 50.0
    
    def test_percentile_calculation_empty_values_direct(self):
        """Test percentile calculation with empty values directly."""
        stats = LatencyStats()
        # Test the _percentile method directly with empty list
        result = stats._percentile([], 50)
        assert result == 0.0


class TestRouteMetricsAggregate:
    """Test RouteMetricsAggregate functionality."""
    
    def test_route_metrics_aggregate_initialization(self):
        """Test RouteMetricsAggregate initializes correctly."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.DYNAMIC)
        
        assert aggregate.route_type == RouteType.DYNAMIC
        assert aggregate.total_requests == 0
        assert aggregate.successful_requests == 0
        assert aggregate.failed_requests == 0
        assert aggregate.success_rate == 0.0
        assert aggregate.failure_rate == 0.0
        assert isinstance(aggregate.latency_stats, LatencyStats)
        assert aggregate.error_counts == {}
    
    def test_success_rate_calculation(self):
        """Test success rate calculation with various scenarios."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.STATIC)
        
        # Test zero requests
        assert aggregate.success_rate == 0.0
        assert aggregate.failure_rate == 0.0
        
        # Test all successful requests
        aggregate.total_requests = 10
        aggregate.successful_requests = 10
        aggregate.failed_requests = 0
        assert aggregate.success_rate == 100.0
        assert aggregate.failure_rate == 0.0
        
        # Test mixed requests
        aggregate.total_requests = 10
        aggregate.successful_requests = 7
        aggregate.failed_requests = 3
        assert aggregate.success_rate == 70.0
        assert aggregate.failure_rate == 30.0
        
        # Test all failed requests
        aggregate.total_requests = 5
        aggregate.successful_requests = 0
        aggregate.failed_requests = 5
        assert aggregate.success_rate == 0.0
        assert aggregate.failure_rate == 100.0
    
    def test_add_metric_success(self):
        """Test adding successful metric to aggregate."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.DYNAMIC)
        
        metric = ResponseMetrics(
            timestamp=time.time(),
            route_type=RouteType.DYNAMIC,
            latency_ms=150.0,
            success=True,
            intent="test",
            query_length=50,
            response_length=100
        )
        
        aggregate.add_metric(metric)
        
        assert aggregate.total_requests == 1
        assert aggregate.successful_requests == 1
        assert aggregate.failed_requests == 0
        assert aggregate.success_rate == 100.0
        assert len(aggregate.error_counts) == 0
    
    def test_add_metric_failure(self):
        """Test adding failed metric to aggregate."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.HYBRID)
        
        metric = ResponseMetrics(
            timestamp=time.time(),
            route_type=RouteType.HYBRID,
            latency_ms=2000.0,
            success=False,
            intent="test",
            query_length=50,
            response_length=0,
            error_type="TimeoutError"
        )
        
        aggregate.add_metric(metric)
        
        assert aggregate.total_requests == 1
        assert aggregate.successful_requests == 0
        assert aggregate.failed_requests == 1
        assert aggregate.failure_rate == 100.0
        assert aggregate.error_counts["TimeoutError"] == 1
    
    def test_add_metric_wrong_route_type_ignored(self):
        """Test that metrics for wrong route type are ignored."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.STATIC)
        
        metric = ResponseMetrics(
            timestamp=time.time(),
            route_type=RouteType.DYNAMIC,  # Different route type
            latency_ms=150.0,
            success=True,
            intent="test",
            query_length=50,
            response_length=100
        )
        
        aggregate.add_metric(metric)
        
        # Should remain unchanged
        assert aggregate.total_requests == 0
        assert aggregate.successful_requests == 0
        assert aggregate.failed_requests == 0
    
    def test_multiple_error_types_tracking(self):
        """Test tracking multiple different error types."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.DYNAMIC)
        
        # Add different error types
        errors = ["TimeoutError", "ConnectionError", "TimeoutError", "ValidationError"]
        
        for error_type in errors:
            metric = ResponseMetrics(
                timestamp=time.time(),
                route_type=RouteType.DYNAMIC,
                latency_ms=1000.0,
                success=False,
                intent="test",
                query_length=50,
                response_length=0,
                error_type=error_type
            )
            aggregate.add_metric(metric)
        
        assert aggregate.total_requests == 4
        assert aggregate.failed_requests == 4
        assert aggregate.error_counts["TimeoutError"] == 2
        assert aggregate.error_counts["ConnectionError"] == 1
        assert aggregate.error_counts["ValidationError"] == 1
    
    def test_update_latency_stats(self):
        """Test updating latency statistics."""
        aggregate = RouteMetricsAggregate(route_type=RouteType.CACHE_HIT)
        latencies = [100.0, 150.0, 200.0, 250.0, 300.0]
        
        aggregate.update_latency_stats(latencies)
        
        assert aggregate.latency_stats.count == 5
        assert aggregate.latency_stats.mean == 200.0
        assert aggregate.latency_stats.min == 100.0
        assert aggregate.latency_stats.max == 300.0


class TestTelemetrySummary:
    """Test TelemetrySummary functionality and JSON export."""
    
    def test_telemetry_summary_initialization(self):
        """Test TelemetrySummary initializes correctly."""
        current_time = time.time()
        summary = TelemetrySummary(
            timestamp=current_time,
            uptime_seconds=3600.0,
            total_requests=100,
            total_successes=95,
            total_failures=5,
            overall_success_rate=95.0
        )
        
        assert summary.timestamp == current_time
        assert summary.uptime_seconds == 3600.0
        assert summary.total_requests == 100
        assert summary.total_successes == 95
        assert summary.total_failures == 5
        assert summary.overall_success_rate == 95.0
    
    def test_to_dict_basic_structure(self):
        """Test to_dict produces correct JSON structure."""
        current_time = time.time()
        summary = TelemetrySummary(
            timestamp=current_time,
            uptime_seconds=1800.0,
            total_requests=50,
            total_successes=45,
            total_failures=5,
            overall_success_rate=90.0,
            average_latency_ms=150.5,
            p95_latency_ms=350.0
        )
        
        result = summary.to_dict()
        
        # Validate structure
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert "overview" in result
        assert "routes" in result
        assert "components" in result
        
        # Validate overview section
        overview = result["overview"]
        assert overview["total_requests"] == 50
        assert overview["total_successes"] == 45
        assert overview["total_failures"] == 5
        assert overview["overall_success_rate"] == 90.0
        assert overview["average_latency_ms"] == 150.5
        assert overview["p95_latency_ms"] == 350.0
    
    def test_to_dict_with_route_metrics(self):
        """Test to_dict with route metrics included."""
        summary = TelemetrySummary(
            timestamp=time.time(),
            uptime_seconds=3600.0,
            total_requests=100,
            total_successes=90,
            total_failures=10,
            overall_success_rate=90.0
        )
        
        # Add route metrics
        dynamic_aggregate = RouteMetricsAggregate(route_type=RouteType.DYNAMIC)
        dynamic_aggregate.total_requests = 60
        dynamic_aggregate.successful_requests = 55
        dynamic_aggregate.failed_requests = 5
        dynamic_aggregate.error_counts = {"TimeoutError": 3, "ConnectionError": 2}
        dynamic_aggregate.update_latency_stats([100.0, 150.0, 200.0])
        
        summary.route_metrics["dynamic"] = dynamic_aggregate
        
        result = summary.to_dict()
        
        # Validate route metrics
        assert "dynamic" in result["routes"]
        route_data = result["routes"]["dynamic"]
        assert route_data["total_requests"] == 60
        assert route_data["success_rate"] == dynamic_aggregate.success_rate
        assert route_data["failure_rate"] == dynamic_aggregate.failure_rate
        assert "latency" in route_data
        assert "errors" in route_data
        assert route_data["errors"]["TimeoutError"] == 3
        assert route_data["errors"]["ConnectionError"] == 2
    
    def test_to_dict_json_serializable(self):
        """Test that to_dict output is JSON serializable."""
        summary = TelemetrySummary(
            timestamp=time.time(),
            uptime_seconds=1200.0,
            total_requests=25,
            total_successes=23,
            total_failures=2,
            overall_success_rate=92.0
        )
        
        result = summary.to_dict()
        
        # Should not raise an exception
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["overview"]["total_requests"] == 25


class TestTimingContext:
    """Test TimingContext context manager."""
    
    def test_timing_context_creation(self):
        """Test TimingContext creates correctly."""
        context = TimingContext(operation_name="test_operation")
        assert context.operation_name == "test_operation"
        assert isinstance(context.start_time, float)
    
    def test_timing_context_manager(self):
        """Test TimingContext as context manager."""
        with TimingContext(operation_name="test") as context:
            time.sleep(0.01)  # Small delay
            elapsed = context.elapsed_ms
            
        assert elapsed > 0
        assert elapsed < 100  # Should be much less than 100ms
    
    def test_timing_context_elapsed_calculation(self):
        """Test elapsed time calculation accuracy."""
        context = TimingContext(operation_name="test")
        
        with context:
            start_check = time.time()
            time.sleep(0.02)
            end_check = time.time()
        
        elapsed_seconds = (end_check - start_check)
        expected_ms = elapsed_seconds * 1000
        
        # Allow for some variance in timing
        assert abs(context.elapsed_ms - expected_ms) < 5


class TestBasicTelemetryCollector:
    """Test BasicTelemetryCollector functionality."""
    
    @pytest.fixture
    def collector(self):
        """Create a fresh telemetry collector for each test."""
        return BasicTelemetryCollector(max_metrics_history=100)
    
    def test_collector_initialization(self, collector):
        """Test collector initializes correctly."""
        assert collector.max_metrics_history == 100
        assert isinstance(collector.start_time, float)
        assert len(collector._recent_metrics) == 0
        assert len(collector._route_aggregates) == len(RouteType)
        
        # Check all route types have aggregates
        for route_type in RouteType:
            assert route_type in collector._route_aggregates
            assert collector._route_aggregates[route_type].route_type == route_type
    
    def test_record_response_basic(self, collector):
        """Test recording a basic response."""
        collector.record_response(
            route_type=RouteType.DYNAMIC,
            latency_ms=150.0,
            success=True,
            intent="test_intent",
            query_length=50,
            response_length=200
        )
        
        assert len(collector._recent_metrics) == 1
        metric = collector._recent_metrics[0]
        assert metric.route_type == RouteType.DYNAMIC
        assert metric.latency_ms == 150.0
        assert metric.success is True
        assert metric.intent == "test_intent"
        assert metric.query_length == 50
        assert metric.response_length == 200
    
    def test_record_response_updates_aggregates(self, collector):
        """Test that recording updates route aggregates."""
        collector.record_response(
            route_type=RouteType.STATIC,
            latency_ms=100.0,
            success=True,
            intent="static_response",
            query_length=30,
            response_length=150
        )
        
        static_aggregate = collector._route_aggregates[RouteType.STATIC]
        assert static_aggregate.total_requests == 1
        assert static_aggregate.successful_requests == 1
        assert static_aggregate.failed_requests == 0
        assert static_aggregate.success_rate == 100.0
    
    def test_record_response_with_error(self, collector):
        """Test recording response with error."""
        collector.record_response(
            route_type=RouteType.HYBRID,
            latency_ms=2000.0,
            success=False,
            intent="failed_request",
            query_length=75,
            response_length=0,
            error_type="TimeoutError"
        )
        
        hybrid_aggregate = collector._route_aggregates[RouteType.HYBRID]
        assert hybrid_aggregate.total_requests == 1
        assert hybrid_aggregate.successful_requests == 0
        assert hybrid_aggregate.failed_requests == 1
        assert hybrid_aggregate.failure_rate == 100.0
        assert hybrid_aggregate.error_counts["TimeoutError"] == 1
    
    def test_max_metrics_history_enforced(self):
        """Test that max metrics history is enforced."""
        collector = BasicTelemetryCollector(max_metrics_history=5)
        
        # Add more metrics than the limit
        for i in range(10):
            collector.record_response(
                route_type=RouteType.STATIC,
                latency_ms=100.0 + i,
                success=True,
                intent=f"intent_{i}",
                query_length=50,
                response_length=100
            )
        
        # Should only keep the last 5
        assert len(collector._recent_metrics) == 5
        
        # Check that it's the most recent ones
        latencies = [m.latency_ms for m in collector._recent_metrics]
        assert latencies == [105.0, 106.0, 107.0, 108.0, 109.0]
    
    def test_get_summary(self, collector):
        """Test getting telemetry summary."""
        # Add some test data
        collector.record_response(RouteType.DYNAMIC, 150.0, True, "test1", 50, 200)
        collector.record_response(RouteType.STATIC, 75.0, True, "test2", 30, 100)
        collector.record_response(RouteType.DYNAMIC, 300.0, False, "test3", 60, 0, "TimeoutError")
        
        summary = collector.get_summary()
        
        assert summary.total_requests == 3
        assert summary.total_successes == 2
        assert summary.total_failures == 1
        assert summary.overall_success_rate == (2/3) * 100
        assert summary.uptime_seconds > 0
        
        # Check route metrics are included
        assert "dynamic" in summary.route_metrics
        assert "static" in summary.route_metrics
        
        dynamic_metrics = summary.route_metrics["dynamic"]
        assert dynamic_metrics.total_requests == 2
        assert dynamic_metrics.successful_requests == 1
        assert dynamic_metrics.failed_requests == 1
    
    def test_get_recent_metrics(self, collector):
        """Test getting recent metrics."""
        # Add test data
        for i in range(10):
            collector.record_response(
                route_type=RouteType.STATIC,
                latency_ms=100.0 + i,
                success=True,
                intent=f"intent_{i}",
                query_length=50,
                response_length=100
            )
        
        # Get last 5 metrics
        recent = collector.get_recent_metrics(5)
        assert len(recent) == 5
        
        # Should be the most recent ones
        latencies = [m.latency_ms for m in recent]
        assert latencies == [105.0, 106.0, 107.0, 108.0, 109.0]
    
    def test_get_recent_metrics_fewer_than_requested(self, collector):
        """Test getting recent metrics when fewer exist than requested."""
        collector.record_response(RouteType.STATIC, 100.0, True, "test", 50, 100)
        
        recent = collector.get_recent_metrics(10)
        assert len(recent) == 1
        assert recent[0].latency_ms == 100.0
    
    def test_get_stats_for_route(self, collector):
        """Test getting stats for specific route type."""
        collector.record_response(RouteType.CACHE_HIT, 25.0, True, "cached1", 40, 150)
        collector.record_response(RouteType.CACHE_HIT, 30.0, True, "cached2", 45, 180)
        
        cache_stats = collector.get_stats_for_route(RouteType.CACHE_HIT)
        assert cache_stats.total_requests == 2
        assert cache_stats.successful_requests == 2
        assert cache_stats.success_rate == 100.0
    
    def test_reset_metrics(self, collector):
        """Test resetting metrics."""
        # Add some data
        collector.record_response(RouteType.DYNAMIC, 150.0, True, "test", 50, 100)
        collector.record_response(RouteType.STATIC, 75.0, False, "test", 30, 0, "Error")
        
        assert len(collector._recent_metrics) == 2
        assert collector._route_aggregates[RouteType.DYNAMIC].total_requests == 1
        
        # Reset
        initial_start_time = collector.start_time
        collector.reset_metrics()
        
        # Check everything is reset
        assert len(collector._recent_metrics) == 0
        for route_type in RouteType:
            aggregate = collector._route_aggregates[route_type]
            assert aggregate.total_requests == 0
            assert aggregate.successful_requests == 0
            assert aggregate.failed_requests == 0
        
        # Start time should be updated
        assert collector.start_time > initial_start_time
    
    def test_thread_safety(self, collector):
        """Test thread safety of telemetry collector."""
        def worker(thread_id: int):
            for i in range(10):
                collector.record_response(
                    route_type=RouteType.DYNAMIC,
                    latency_ms=100.0 + (thread_id * 10) + i,
                    success=True,
                    intent=f"thread_{thread_id}_req_{i}",
                    query_length=50,
                    response_length=100
                )
        
        # Start multiple threads
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=worker, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all metrics were recorded
        assert len(collector._recent_metrics) == 50
        dynamic_aggregate = collector._route_aggregates[RouteType.DYNAMIC]
        assert dynamic_aggregate.total_requests == 50
        assert dynamic_aggregate.successful_requests == 50
    
    def test_circuit_breaker_integration(self, collector):
        """Test circuit breaker integration."""
        mock_circuit_breaker = Mock()
        mock_circuit_breaker.state.value = "closed"
        mock_circuit_breaker.get_status.return_value = {"state": "closed", "failures": 0}
        
        collector.set_circuit_breaker(mock_circuit_breaker)
        
        collector.record_response(
            route_type=RouteType.DYNAMIC,
            latency_ms=150.0,
            success=True,
            intent="test",
            query_length=50,
            response_length=100
        )
        
        # Check that circuit breaker state was recorded
        metric = collector._recent_metrics[0]
        assert metric.circuit_breaker_state == "closed"
        
        # Check summary includes circuit breaker status
        summary = collector.get_summary()
        assert summary.circuit_breaker_status["state"] == "closed"
    
    def test_cache_integration(self, collector):
        """Test cache integration."""
        mock_cache = Mock()
        mock_cache.get_stats.return_value = {"hits": 10, "misses": 5, "hit_rate": 0.67}
        
        collector.set_cache(mock_cache)
        
        summary = collector.get_summary()
        assert summary.cache_stats["hits"] == 10
        assert summary.cache_stats["misses"] == 5
        assert summary.cache_stats["hit_rate"] == 0.67


class TestTrackLatencyDecorator:
    """Test the @track_latency decorator."""
    
    @pytest.fixture
    def fresh_collector(self):
        """Get a fresh collector and reset global state."""
        from vibe_check.mentor.telemetry import _global_collector
        _global_collector.reset_metrics()
        return _global_collector
    
    def test_track_latency_sync_function(self, fresh_collector):
        """Test decorator on synchronous function."""
        @track_latency(RouteType.STATIC, intent="sync_test")
        def sync_function(query: str) -> str:
            time.sleep(0.01)  # Small delay
            return f"Response to: {query}"
        
        result = sync_function("test query")
        
        assert result == "Response to: test query"
        assert len(fresh_collector._recent_metrics) == 1
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.route_type == RouteType.STATIC
        assert metric.success is True
        assert metric.intent == "sync_test"
        assert metric.query_length == len("test query")
        assert metric.response_length == len("Response to: test query")
        assert metric.latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_track_latency_async_function(self, fresh_collector):
        """Test decorator on async function."""
        @track_latency(RouteType.DYNAMIC, intent="async_test")
        async def async_function(query: str) -> dict:
            await asyncio.sleep(0.01)  # Small async delay
            return {"content": f"Async response to: {query}"}
        
        result = await async_function("async test query")
        
        assert result["content"] == "Async response to: async test query"
        assert len(fresh_collector._recent_metrics) == 1
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.route_type == RouteType.DYNAMIC
        assert metric.success is True
        assert metric.intent == "async_test"
        assert metric.query_length == len("async test query")
        assert metric.response_length == len("Async response to: async test query")
        assert metric.latency_ms > 0
    
    def test_track_latency_function_error(self, fresh_collector):
        """Test decorator handles function errors correctly."""
        @track_latency(RouteType.HYBRID, intent="error_test")
        def error_function(query: str) -> str:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            error_function("test query")
        
        assert len(fresh_collector._recent_metrics) == 1
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.route_type == RouteType.HYBRID
        assert metric.success is False
        assert metric.error_type == "ValueError"
        assert metric.intent == "error_test"
        assert metric.response_length == 0
    
    def test_track_latency_auto_intent(self, fresh_collector):
        """Test decorator uses function name as intent when not provided."""
        @track_latency(RouteType.CACHE_HIT)
        def my_special_function(query: str) -> str:
            return "response"
        
        my_special_function("test")
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.intent == "my_special_function"
    
    def test_track_latency_query_extraction_kwargs(self, fresh_collector):
        """Test query length extraction from kwargs when no string args."""
        @track_latency(RouteType.STATIC)
        def function_with_query_kwarg(data: dict, query: str, context: str) -> str:
            return "response"
        
        function_with_query_kwarg({"key": "value"}, query="test query from kwargs", context="context")
        
        metric = fresh_collector._recent_metrics[0]
        # Since first arg is not a string, should extract from query kwarg
        assert metric.query_length == len("test query from kwargs")
    
    def test_track_latency_no_query_extraction(self, fresh_collector):
        """Test when no query can be extracted."""
        @track_latency(RouteType.STATIC)
        def function_no_query(data: dict) -> str:
            return "response"
        
        function_no_query({"key": "value"})
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.query_length == 0  # Should default to 0
    
    def test_track_latency_response_length_dict(self, fresh_collector):
        """Test response length extraction from dict result."""
        @track_latency(RouteType.DYNAMIC)
        def function_dict_response(query: str) -> dict:
            return {"content": "This is the response content"}
        
        function_dict_response("test")
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.response_length == len("This is the response content")
    
    def test_track_latency_response_length_none(self, fresh_collector):
        """Test response length when function returns None."""
        @track_latency(RouteType.STATIC)
        def function_none_response(query: str) -> None:
            return None
        
        function_none_response("test")
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.response_length == 0
    
    def test_track_latency_response_length_object(self, fresh_collector):
        """Test response length when function returns non-string object."""
        @track_latency(RouteType.STATIC)
        def function_object_response(query: str) -> list:
            return [1, 2, 3, 4, 5]
        
        function_object_response("test")
        
        metric = fresh_collector._recent_metrics[0]
        # Should convert object to string and get length
        assert metric.response_length == len(str([1, 2, 3, 4, 5]))


class TestTelemetryContext:
    """Test TelemetryContext context manager."""
    
    @pytest.fixture
    def fresh_collector(self):
        """Get a fresh collector and reset global state."""
        from vibe_check.mentor.telemetry import _global_collector
        _global_collector.reset_metrics()
        return _global_collector
    
    def test_telemetry_context_basic(self, fresh_collector):
        """Test basic TelemetryContext usage."""
        with TelemetryContext(
            route_type=RouteType.HYBRID,
            intent="manual_tracking",
            query_length=25
        ) as ctx:
            time.sleep(0.01)
            ctx.set_response_length(150)
            ctx.set_cache_hit(True)
        
        assert len(fresh_collector._recent_metrics) == 1
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.route_type == RouteType.HYBRID
        assert metric.intent == "manual_tracking"
        assert metric.query_length == 25
        assert metric.response_length == 150
        assert metric.cache_hit is True
        assert metric.success is True
        assert metric.latency_ms > 0
    
    def test_telemetry_context_with_error(self, fresh_collector):
        """Test TelemetryContext handles exceptions."""
        with pytest.raises(RuntimeError, match="Test context error"):
            with TelemetryContext(
                route_type=RouteType.DYNAMIC,
                intent="error_test",
                query_length=50
            ):
                raise RuntimeError("Test context error")
        
        assert len(fresh_collector._recent_metrics) == 1
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.success is False
        assert metric.error_type == "RuntimeError"
        assert metric.intent == "error_test"
    
    def test_telemetry_context_defaults(self, fresh_collector):
        """Test TelemetryContext with default values."""
        with TelemetryContext(
            route_type=RouteType.CACHE_HIT,
            intent="defaults_test"
        ) as ctx:
            pass
        
        metric = fresh_collector._recent_metrics[0]
        assert metric.query_length == 0  # Default
        assert metric.response_length == 0  # Default
        assert metric.cache_hit is False  # Default
        assert metric.success is True


class TestPerformanceRequirements:
    """Test performance requirements and overhead."""
    
    def test_telemetry_overhead_measurement(self):
        """Test that telemetry adds reasonable overhead."""
        collector = BasicTelemetryCollector()
        
        # More realistic baseline with actual computation
        def baseline_function():
            """Simulate meaningful work"""
            result = 0
            for i in range(10000):
                result += i * i
            return result
        
        baseline_times = []
        for _ in range(50):
            start = time.perf_counter()
            baseline_function()
            baseline_times.append((time.perf_counter() - start) * 1000)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        
        # Measurement with telemetry
        @track_latency(RouteType.STATIC)
        def tracked_function():
            """Simulate same work with telemetry"""
            result = 0
            for i in range(10000):
                result += i * i
            return result
        
        tracked_times = []
        for _ in range(50):
            start = time.perf_counter()
            tracked_function()
            tracked_times.append((time.perf_counter() - start) * 1000)
        
        tracked_avg = sum(tracked_times) / len(tracked_times)
        
        # Calculate overhead percentage
        overhead_percent = ((tracked_avg - baseline_avg) / baseline_avg) * 100
        
        # Should be less than 50% overhead (more realistic for such micro-benchmarks)
        # In real-world usage with actual network calls, overhead would be much smaller
        assert overhead_percent < 50.0, f"Telemetry overhead {overhead_percent:.2f}% is excessive"
        
        # Ensure absolute overhead is small (should be microseconds)
        absolute_overhead_ms = tracked_avg - baseline_avg
        assert absolute_overhead_ms < 10.0, f"Absolute overhead {absolute_overhead_ms:.3f}ms is too high"
    
    def test_memory_usage_reasonable(self):
        """Test that memory usage stays reasonable."""
        import sys
        
        collector = BasicTelemetryCollector(max_metrics_history=1000)
        
        # Add maximum metrics
        for i in range(1000):
            collector.record_response(
                route_type=RouteType.DYNAMIC,
                latency_ms=100.0 + i,
                success=True,
                intent=f"test_{i}",
                query_length=50,
                response_length=100
            )
        
        # Check memory usage of recent metrics
        metrics_size = sys.getsizeof(collector._recent_metrics)
        
        # Should be reasonable (less than 1MB for 1000 metrics)
        assert metrics_size < 1024 * 1024, f"Metrics collection using {metrics_size} bytes"
    
    def test_concurrent_access_performance(self):
        """Test performance under concurrent access."""
        collector = BasicTelemetryCollector()
        
        def concurrent_worker():
            for i in range(100):
                collector.record_response(
                    route_type=RouteType.DYNAMIC,
                    latency_ms=100.0 + i,
                    success=True,
                    intent=f"concurrent_{i}",
                    query_length=50,
                    response_length=100
                )
        
        start_time = time.time()
        
        # Run 10 threads concurrently
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=concurrent_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Should complete in reasonable time (less than 5 seconds)
        duration = end_time - start_time
        assert duration < 5.0, f"Concurrent access took {duration:.2f} seconds"
        
        # Should have recorded all metrics
        assert len(collector._recent_metrics) == 1000


def test_global_collector_singleton():
    """Test that global collector is singleton."""
    collector1 = get_telemetry_collector()
    collector2 = get_telemetry_collector()
    
    assert collector1 is collector2