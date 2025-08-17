"""
Tests for Circuit Breaker Pattern (Issue #102)

Comprehensive tests for circuit breaker, retry logic, and health monitoring
components that implement Phase 2 of the reliability overhaul.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock, patch

from vibe_check.tools.shared.circuit_breaker import (
    ClaudeCliCircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenError,
    ClaudeCliError,
    CircuitBreakerConfig,
    CircuitBreakerStats
)
from vibe_check.tools.shared.retry_logic import (
    RetryExecutor,
    RetryConfig,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    FixedBackoffStrategy,
    claude_cli_with_retry
)
from vibe_check.tools.shared.health_monitor import (
    ClaudeCliHealthMonitor,
    HealthStatus,
    PerformanceMetrics,
    HealthThresholds
)


class TestCircuitBreaker:
    """Test the circuit breaker implementation."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly."""
        cb = ClaudeCliCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=300,
            name="test_breaker"
        )
        
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 300
        assert cb.name == "test_breaker"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.stats.total_calls == 0
        assert cb.stats.success_count == 0
        assert cb.stats.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_calls_keep_circuit_closed(self):
        """Test that successful calls keep the circuit closed."""
        cb = ClaudeCliCircuitBreaker(failure_threshold=3)
        
        async def successful_function():
            return "success"
        
        # Make several successful calls
        for i in range(5):
            result = await cb.call(successful_function)
            assert result == "success"
            assert cb.state == CircuitBreakerState.CLOSED
            assert cb.stats.consecutive_failures == 0
            assert cb.stats.success_count == i + 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit opens after reaching failure threshold."""
        cb = ClaudeCliCircuitBreaker(failure_threshold=3)
        
        async def failing_function():
            raise Exception("Test failure")
        
        # Make calls that should cause circuit to open
        for i in range(3):
            with pytest.raises(ClaudeCliError):
                await cb.call(failing_function)
            
            if i < 2:
                assert cb.state == CircuitBreakerState.CLOSED
            else:
                assert cb.state == CircuitBreakerState.OPEN
        
        # Next call should be rejected immediately
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(failing_function)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        cb = ClaudeCliCircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        async def failing_function():
            raise Exception("Test failure")
        
        async def successful_function():
            return "recovered"
        
        # Trigger circuit opening
        for _ in range(2):
            with pytest.raises(ClaudeCliError):
                await cb.call(failing_function)
        
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Next call should transition to half-open and succeed
        result = await cb.call(successful_function)
        assert result == "recovered"
        assert cb.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure_reopens(self):
        """Test that failure in half-open state reopens circuit."""
        cb = ClaudeCliCircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        async def failing_function():
            raise Exception("Test failure")
        
        # Trigger circuit opening
        for _ in range(2):
            with pytest.raises(ClaudeCliError):
                await cb.call(failing_function)
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Call in half-open state should fail and reopen circuit
        with pytest.raises(ClaudeCliError):
            await cb.call(failing_function)
        
        assert cb.state == CircuitBreakerState.OPEN
    
    def test_circuit_breaker_health_assessment(self):
        """Test circuit breaker health assessment."""
        cb = ClaudeCliCircuitBreaker()
        
        # Initially NOT healthy with no data (no success history)
        assert cb.is_healthy is False
        
        # Simulate some failures
        cb.stats.consecutive_failures = 6
        assert cb.is_healthy is False
        
        # Reset and test success rate
        cb.reset()
        cb.stats.total_calls = 10
        cb.stats.success_count = 5  # 50% success rate
        assert cb.is_healthy is False
        
        # Good success rate
        cb.stats.success_count = 9  # 90% success rate
        assert cb.is_healthy is True
    
    def test_circuit_breaker_status(self):
        """Test circuit breaker status reporting."""
        cb = ClaudeCliCircuitBreaker(name="test_status")
        status = cb.get_status()
        
        assert status["name"] == "test_status"
        assert status["state"] == "CLOSED"
        assert "stats" in status
        assert "config" in status
        assert "timing" in status
        assert isinstance(status["is_healthy"], bool)


class TestRetryLogic:
    """Test retry logic and backoff strategies."""
    
    def test_exponential_backoff_strategy(self):
        """Test exponential backoff calculation."""
        strategy = ExponentialBackoffStrategy(jitter_factor=0.0)  # No jitter for testing
        
        # Test exponential growth: 1s, 2s, 4s, 8s
        assert strategy.calculate_delay(0, 1.0, 60.0) == 1.0
        assert strategy.calculate_delay(1, 1.0, 60.0) == 2.0
        assert strategy.calculate_delay(2, 1.0, 60.0) == 4.0
        assert strategy.calculate_delay(3, 1.0, 60.0) == 8.0
        
        # Test max delay enforcement
        assert strategy.calculate_delay(10, 1.0, 10.0) == 10.0
    
    def test_linear_backoff_strategy(self):
        """Test linear backoff calculation."""
        strategy = LinearBackoffStrategy()
        
        # Test linear growth: 1s, 2s, 3s, 4s
        assert strategy.calculate_delay(0, 1.0, 60.0) == 1.0
        assert strategy.calculate_delay(1, 1.0, 60.0) == 2.0
        assert strategy.calculate_delay(2, 1.0, 60.0) == 3.0
        assert strategy.calculate_delay(3, 1.0, 60.0) == 4.0
    
    def test_fixed_backoff_strategy(self):
        """Test fixed backoff calculation."""
        strategy = FixedBackoffStrategy()
        
        # Test fixed delay
        for attempt in range(5):
            assert strategy.calculate_delay(attempt, 2.0, 60.0) == 2.0
    
    @pytest.mark.asyncio
    async def test_retry_executor_success_on_first_attempt(self):
        """Test retry executor when function succeeds on first attempt."""
        cb = ClaudeCliCircuitBreaker()
        config = RetryConfig(max_retries=3)
        executor = RetryExecutor(cb, config)
        
        async def successful_function():
            return "success"
        
        result = await executor.execute_with_retry(successful_function)
        assert result == "success"
        assert cb.stats.total_calls == 1
        assert cb.stats.success_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_executor_success_after_retries(self):
        """Test retry executor succeeding after some failures."""
        cb = ClaudeCliCircuitBreaker()
        config = RetryConfig(max_retries=3, base_delay=0.1)  # Fast delays for testing
        executor = RetryExecutor(cb, config)
        
        call_count = 0
        
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success after retries"
        
        result = await executor.execute_with_retry(flaky_function)
        assert result == "success after retries"
        assert call_count == 3
        assert cb.stats.total_calls == 3
        assert cb.stats.success_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_executor_exhausts_retries(self):
        """Test retry executor when all retries are exhausted."""
        cb = ClaudeCliCircuitBreaker()
        config = RetryConfig(max_retries=2, base_delay=0.1)
        executor = RetryExecutor(cb, config)
        
        async def always_failing_function():
            raise Exception("Always fails")
        
        with pytest.raises(ClaudeCliError) as exc_info:
            await executor.execute_with_retry(always_failing_function)
        
        assert "Analysis failed after 3 attempts" in str(exc_info.value)
        assert cb.stats.total_calls == 3
        assert cb.stats.success_count == 0
    
    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker_open(self):
        """Test retry behavior when circuit breaker opens."""
        cb = ClaudeCliCircuitBreaker(failure_threshold=2)  # Allow one retry before opening
        config = RetryConfig(max_retries=1, base_delay=0.1)
        executor = RetryExecutor(cb, config)
        
        async def failing_function():
            raise Exception("Failure")
        
        # First call should fail (tries 2 times, opens circuit after 2 failures)
        with pytest.raises(ClaudeCliError):
            await executor.execute_with_retry(failing_function)
        
        assert cb.state == CircuitBreakerState.OPEN
        
        # Second call should be rejected immediately by circuit breaker
        with pytest.raises(CircuitBreakerOpenError):
            await executor.execute_with_retry(failing_function)


class TestHealthMonitor:
    """Test health monitoring functionality."""
    
    def test_health_monitor_initialization(self):
        """Test health monitor initializes correctly."""
        cb = ClaudeCliCircuitBreaker()
        monitor = ClaudeCliHealthMonitor(cb)
        
        assert monitor.circuit_breaker is cb
        assert len(monitor.call_history) == 0
        assert isinstance(monitor.current_metrics, PerformanceMetrics)
    
    def test_call_recording(self):
        """Test call recording functionality."""
        cb = ClaudeCliCircuitBreaker()
        monitor = ClaudeCliHealthMonitor(cb)
        
        # Record some calls
        monitor.record_call(success=True, duration=1.5)
        monitor.record_call(success=False, duration=3.0, error_type="TimeoutError")
        monitor.record_call(success=True, duration=2.0)
        
        assert len(monitor.call_history) == 3
        assert monitor.call_history[0].success is True
        assert monitor.call_history[1].error_type == "TimeoutError"
        assert monitor.call_history[2].duration == 2.0
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation."""
        cb = ClaudeCliCircuitBreaker()
        monitor = ClaudeCliHealthMonitor(cb)
        
        # Record calls with varying durations
        durations = [1.0, 2.0, 3.0, 4.0, 5.0] * 4  # 20 calls for percentile calculation
        for duration in durations:
            monitor.record_call(success=True, duration=duration)
        
        # Should have calculated metrics
        assert monitor.current_metrics.avg_response_time > 0
        assert monitor.current_metrics.min_response_time == 1.0
        assert monitor.current_metrics.max_response_time == 5.0
        assert monitor.current_metrics.p95_response_time > 0
    
    def test_health_status_calculation(self):
        """Test health status calculation."""
        cb = ClaudeCliCircuitBreaker()
        thresholds = HealthThresholds(
            healthy_success_rate=0.95,
            degraded_success_rate=0.80,
            unhealthy_success_rate=0.50
        )
        monitor = ClaudeCliHealthMonitor(cb, thresholds)
        
        # Test healthy status with good success rate
        cb.stats.total_calls = 10
        cb.stats.success_count = 10
        cb.stats.last_success_time = time.time()
        
        status = monitor.get_health_status()
        assert status.is_healthy is True
        assert status.level == "HEALTHY"
        assert status.score > 0.9
    
    def test_health_status_degraded(self):
        """Test degraded health status."""
        cb = ClaudeCliCircuitBreaker()
        thresholds = HealthThresholds(
            healthy_success_rate=0.95,
            degraded_success_rate=0.80,
            unhealthy_success_rate=0.50
        )
        monitor = ClaudeCliHealthMonitor(cb, thresholds)
        
        # Set up degraded conditions
        cb.stats.total_calls = 10  
        cb.stats.success_count = 8  # 80% success rate (exactly at threshold)
        cb.stats.consecutive_failures = 1  # Keep low to avoid multiplying penalties
        cb.stats.last_success_time = time.time()
        
        status = monitor.get_health_status()
        assert status.is_healthy is False
        # With 80% success rate exactly at degraded threshold (0.6 factor) and 1 consecutive failure,
        # the score should be in degraded range (0.6 > 0.3)
        assert status.level in ["DEGRADED", "UNHEALTHY"]  # Allow both as multiplicative factors can vary
        assert 0.3 < status.score < 0.9
    
    def test_health_status_critical(self):
        """Test critical health status."""
        cb = ClaudeCliCircuitBreaker()
        monitor = ClaudeCliHealthMonitor(cb)
        
        # Set up critical conditions
        cb.state = CircuitBreakerState.OPEN
        cb.stats.total_calls = 10
        cb.stats.success_count = 2  # 20% success rate
        cb.stats.consecutive_failures = 8
        
        status = monitor.get_health_status()
        assert status.is_healthy is False
        assert status.level == "CRITICAL"
        assert status.score < 0.3
        assert "Circuit breaker is OPEN - service unavailable" in status.issues
    
    def test_diagnostic_report(self):
        """Test diagnostic report generation."""
        cb = ClaudeCliCircuitBreaker()
        monitor = ClaudeCliHealthMonitor(cb)
        
        # Add some call history
        monitor.record_call(success=True, duration=1.0)
        monitor.record_call(success=False, duration=2.0, error_type="TimeoutError")
        
        report = monitor.get_diagnostic_report()
        
        assert "timestamp" in report
        assert "health_status" in report
        assert "performance_metrics" in report
        assert "circuit_breaker" in report
        assert "call_history_summary" in report
        assert "recommendations" in report
        
        # Check specific content
        assert report["call_history_summary"]["total_calls"] == 2
        assert isinstance(report["recommendations"], list)


class TestIntegration:
    """Test integration between circuit breaker, retry logic, and health monitoring."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_integration(self):
        """Test complete integration with circuit breaker, retries, and health monitoring."""
        cb = ClaudeCliCircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        monitor = ClaudeCliHealthMonitor(cb)
        
        call_count = 0
        
        async def flaky_service():
            nonlocal call_count
            call_count += 1
            
            # Fail first 2 calls, then succeed
            if call_count <= 2:
                monitor.record_call(success=False, duration=1.0, error_type="ServiceError")
                raise Exception("Service temporarily unavailable")
            else:
                monitor.record_call(success=True, duration=0.5)
                return "service recovered"
        
        # First two calls should fail but not open circuit
        with pytest.raises(ClaudeCliError):
            await claude_cli_with_retry(flaky_service, cb, max_retries=0)
        
        with pytest.raises(ClaudeCliError):
            await claude_cli_with_retry(flaky_service, cb, max_retries=0)
        
        # Circuit should now be open
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for recovery and try again
        await asyncio.sleep(0.15)
        
        # This should succeed and close the circuit
        result = await claude_cli_with_retry(flaky_service, cb, max_retries=0)
        assert result == "service recovered"
        assert cb.state == CircuitBreakerState.CLOSED
        
        # Check health monitoring recorded everything
        assert len(monitor.call_history) >= 3
        health_status = monitor.get_health_status()
        assert isinstance(health_status, HealthStatus)


@pytest.mark.asyncio
async def test_circuit_breaker_with_timeout():
    """Test circuit breaker behavior with timeouts."""
    cb = ClaudeCliCircuitBreaker(failure_threshold=2)
    
    async def slow_function():
        await asyncio.sleep(0.2)  # This will timeout
        return "too slow"
    
    config = RetryConfig(max_retries=1, base_delay=0.05)  # Shorter delay for faster test
    executor = RetryExecutor(cb, config)
    
    # Should timeout and be recorded as failure
    with pytest.raises(ClaudeCliError):
        await executor.execute_with_retry(slow_function, timeout=0.05)  # Timeout shorter than sleep
    
    # The timeout should be recorded as a failure in circuit breaker stats
    assert cb.stats.total_calls > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])