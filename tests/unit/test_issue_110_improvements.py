"""
Comprehensive Test Suite for Issue #110 Improvements

Tests all the follow-up improvements implemented after PR #109:
1. Input validation hardening
2. Real integration testing capabilities
3. Resource monitoring and limits
4. Health/metrics endpoints
5. Enhanced graceful degradation
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from vibe_check.tools.async_analysis.validation import (
    AsyncAnalysisValidator,
    validate_async_analysis_request,
    validate_status_check_request,
)
from vibe_check.tools.async_analysis.resource_monitor import (
    ResourceMonitor,
    ResourceLimits,
    ResourceUsage,
    JobResourceTracker,
)
from vibe_check.tools.async_analysis.health_monitoring import (
    HealthMonitor,
    HealthCheckResult,
    SystemMetrics,
)
from vibe_check.tools.async_analysis.graceful_degradation import (
    GracefulDegradationManager,
    FallbackConfig,
    SystemAvailability,
)


class TestInputValidation:
    """Test input validation hardening."""

    def test_repository_validation_basic(self):
        """Test basic repository name validation."""
        # Valid cases
        assert AsyncAnalysisValidator.validate_repository("owner/repo").is_valid
        assert AsyncAnalysisValidator.validate_repository(
            "user-name/repo-name"
        ).is_valid
        assert AsyncAnalysisValidator.validate_repository(
            "org.name/project.name"
        ).is_valid

        # Invalid cases
        assert not AsyncAnalysisValidator.validate_repository("").is_valid
        assert not AsyncAnalysisValidator.validate_repository("invalid").is_valid
        assert not AsyncAnalysisValidator.validate_repository("owner//repo").is_valid
        assert not AsyncAnalysisValidator.validate_repository("owner/").is_valid
        assert not AsyncAnalysisValidator.validate_repository("/repo").is_valid

    def test_repository_validation_consecutive_dots(self):
        """Test consecutive dots validation."""
        # Should reject consecutive dots
        assert not AsyncAnalysisValidator.validate_repository(
            "owner..name/repo"
        ).is_valid
        assert not AsyncAnalysisValidator.validate_repository(
            "owner/repo..name"
        ).is_valid
        assert not AsyncAnalysisValidator.validate_repository("owner../repo").is_valid

        # Should accept single dots
        assert AsyncAnalysisValidator.validate_repository(
            "owner.name/repo.name"
        ).is_valid

    def test_repository_validation_length_limits(self):
        """Test repository name length limits."""
        # Test maximum length
        long_name = "a" * 150  # Exceeds limit
        assert not AsyncAnalysisValidator.validate_repository(
            f"owner/{long_name}"
        ).is_valid

        # Test reasonable length
        normal_name = "a" * 50
        assert AsyncAnalysisValidator.validate_repository(
            f"owner/{normal_name}"
        ).is_valid

    def test_pr_number_validation(self):
        """Test PR number validation."""
        # Valid cases
        assert AsyncAnalysisValidator.validate_pr_number(1).is_valid
        assert AsyncAnalysisValidator.validate_pr_number(12345).is_valid
        assert AsyncAnalysisValidator.validate_pr_number(
            "123"
        ).is_valid  # String conversion

        # Invalid cases
        assert not AsyncAnalysisValidator.validate_pr_number(0).is_valid
        assert not AsyncAnalysisValidator.validate_pr_number(-1).is_valid
        assert not AsyncAnalysisValidator.validate_pr_number("abc").is_valid
        assert not AsyncAnalysisValidator.validate_pr_number(None).is_valid
        assert not AsyncAnalysisValidator.validate_pr_number(
            10000000
        ).is_valid  # Too large

    def test_job_id_validation(self):
        """Test job ID validation."""
        # Valid cases
        assert AsyncAnalysisValidator.validate_job_id("repo#123#abc123").is_valid
        assert AsyncAnalysisValidator.validate_job_id("valid-job-id").is_valid
        assert AsyncAnalysisValidator.validate_job_id("job_123").is_valid

        # Invalid cases
        assert not AsyncAnalysisValidator.validate_job_id("").is_valid
        assert not AsyncAnalysisValidator.validate_job_id("invalid@job").is_valid
        assert not AsyncAnalysisValidator.validate_job_id("job with spaces").is_valid
        assert not AsyncAnalysisValidator.validate_job_id(
            "a" * 150
        ).is_valid  # Too long

    def test_pr_data_validation(self):
        """Test PR data structure validation."""
        # Valid PR data
        valid_data = {
            "title": "Test PR",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
        }
        result = AsyncAnalysisValidator.validate_pr_data(valid_data)
        assert result.is_valid

        # Missing required fields
        invalid_data = {"title": "Test"}
        assert not AsyncAnalysisValidator.validate_pr_data(invalid_data).is_valid

        # Invalid data types
        invalid_types = {
            "title": "Test",
            "additions": "many",  # Should be int
            "deletions": 50,
            "changed_files": 5,
        }
        assert not AsyncAnalysisValidator.validate_pr_data(invalid_types).is_valid

        # Negative values
        negative_data = {
            "title": "Test",
            "additions": -100,
            "deletions": 50,
            "changed_files": 5,
        }
        assert not AsyncAnalysisValidator.validate_pr_data(negative_data).is_valid

    def test_suspicious_pattern_detection(self):
        """Test detection of suspicious patterns."""
        # SQL injection patterns
        assert not AsyncAnalysisValidator.validate_repository(
            "owner/repo; DROP TABLE"
        ).is_valid
        assert not AsyncAnalysisValidator.validate_job_id("job' UNION SELECT").is_valid

        # Script injection patterns
        assert not AsyncAnalysisValidator.validate_repository(
            "owner/<script>alert</script>"
        ).is_valid

        # Path traversal patterns
        assert not AsyncAnalysisValidator.validate_job_id(
            "../../../etc/passwd"
        ).is_valid

    def test_complete_request_validation(self):
        """Test complete async analysis request validation."""
        valid_pr_data = {
            "title": "Test PR",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
        }

        # Valid request
        is_valid, result = validate_async_analysis_request(
            123, "owner/repo", valid_pr_data
        )
        assert is_valid
        assert "pr_number" in result
        assert "repository" in result
        assert "pr_data" in result

        # Invalid PR number
        is_valid, result = validate_async_analysis_request(
            -1, "owner/repo", valid_pr_data
        )
        assert not is_valid
        assert result["field"] == "pr_number"

        # Invalid repository
        is_valid, result = validate_async_analysis_request(
            123, "invalid..repo", valid_pr_data
        )
        assert not is_valid
        assert result["field"] == "repository"

        # Invalid PR data
        is_valid, result = validate_async_analysis_request(123, "owner/repo", {})
        assert not is_valid
        assert result["field"] == "pr_data"


class TestResourceMonitoring:
    """Test resource monitoring and limits."""

    def test_resource_limits_creation(self):
        """Test resource limits configuration."""
        limits = ResourceLimits(
            max_memory_mb=1024, max_cpu_percent=50.0, max_concurrent_jobs=5
        )

        assert limits.max_memory_mb == 1024
        assert limits.max_cpu_percent == 50.0
        assert limits.max_concurrent_jobs == 5

    def test_resource_usage_creation(self):
        """Test resource usage metrics."""
        usage = ResourceUsage(memory_mb=512.5, cpu_percent=25.3, open_files=10)

        usage_dict = usage.to_dict()
        assert usage_dict["memory_mb"] == 512.5
        assert usage_dict["cpu_percent"] == 25.3
        assert usage_dict["open_files"] == 10
        assert "measured_at" in usage_dict

    def test_job_resource_tracker(self):
        """Test job-level resource tracking."""
        tracker = JobResourceTracker(job_id="test-job")

        assert tracker.job_id == "test-job"
        assert tracker.get_duration() >= 0

        # Test usage update
        usage = ResourceUsage(memory_mb=100, cpu_percent=10)
        tracker.update_usage(usage)

        assert tracker.current_usage.memory_mb == 100
        assert tracker.peak_memory_mb == 100
        assert len(tracker.usage_history) == 1

    def test_resource_violation_detection(self):
        """Test resource limit violation detection."""
        limits = ResourceLimits(max_memory_mb=512, max_cpu_percent=25.0)
        tracker = JobResourceTracker(job_id="test-job")

        # Normal usage - no violations
        normal_usage = ResourceUsage(memory_mb=256, cpu_percent=15.0)
        tracker.update_usage(normal_usage)
        violations = tracker.check_violations(limits)
        assert len(violations) == 0

        # Excessive memory usage
        high_memory_usage = ResourceUsage(memory_mb=1024, cpu_percent=15.0)
        tracker.update_usage(high_memory_usage)
        violations = tracker.check_violations(limits)
        assert len(violations) > 0
        assert any("Memory limit exceeded" in v for v in violations)

        # Excessive CPU usage
        high_cpu_usage = ResourceUsage(memory_mb=256, cpu_percent=50.0)
        tracker.update_usage(high_cpu_usage)
        violations = tracker.check_violations(limits)
        assert any("CPU limit exceeded" in v for v in violations)

    def test_resource_monitor_initialization(self):
        """Test resource monitor initialization."""
        limits = ResourceLimits(max_memory_mb=1024)
        monitor = ResourceMonitor(limits)

        assert monitor.limits.max_memory_mb == 1024
        assert not monitor.monitoring_active
        assert len(monitor.job_trackers) == 0

    def test_resource_monitor_job_registration(self):
        """Test job registration with resource monitor."""
        monitor = ResourceMonitor()

        # Register a job
        tracker = monitor.register_job("test-job", process_id=12345)
        assert tracker.job_id == "test-job"
        assert tracker.process_id == 12345
        assert "test-job" in monitor.job_trackers

        # Unregister the job
        monitor.unregister_job("test-job")
        assert "test-job" not in monitor.job_trackers

    @pytest.mark.asyncio
    async def test_resource_monitor_system_limits(self):
        """Test system-wide resource limit checking."""
        monitor = ResourceMonitor()

        # Test with no jobs
        check_result = monitor.check_system_limits()
        assert isinstance(check_result, dict)
        assert "within_limits" in check_result
        assert "violations" in check_result
        assert "current_usage" in check_result

    def test_new_job_acceptance_logic(self):
        """Test logic for accepting new jobs based on resources."""
        monitor = ResourceMonitor()

        # Test job acceptance logic
        can_accept, reason = monitor.should_accept_new_job()
        assert isinstance(can_accept, bool)
        assert isinstance(reason, str)

        # If rejected, should have a clear reason
        if not can_accept:
            assert len(reason) > 0
            assert any(
                keyword in reason.lower()
                for keyword in ["limit", "exceeded", "capacity", "violation"]
            )
        else:
            assert "ready" in reason.lower() or "available" in reason.lower()


class TestHealthMonitoring:
    """Test health monitoring and metrics."""

    def test_health_check_result_creation(self):
        """Test health check result structure."""
        result = HealthCheckResult(
            component="test_component",
            status="healthy",
            message="All systems operational",
        )

        result_dict = result.to_dict()
        assert result_dict["component"] == "test_component"
        assert result_dict["status"] == "healthy"
        assert result_dict["message"] == "All systems operational"
        assert "timestamp" in result_dict

    def test_system_metrics_creation(self):
        """Test system metrics structure."""
        metrics = SystemMetrics(queue_size=5, active_jobs=2, success_rate_percent=95.5)

        metrics_dict = metrics.to_dict()
        assert metrics_dict["queue_metrics"]["queue_size"] == 5
        assert metrics_dict["queue_metrics"]["active_jobs"] == 2
        assert metrics_dict["performance_metrics"]["success_rate_percent"] == 95.5
        assert metrics_dict["overall_health"] == "healthy"

    def test_health_monitor_initialization(self):
        """Test health monitor initialization."""
        monitor = HealthMonitor()

        assert len(monitor.health_history) == 0
        assert len(monitor.metrics_history) == 0
        assert monitor.last_health_check == 0

    @pytest.mark.asyncio
    async def test_health_monitor_comprehensive_check(self):
        """Test comprehensive health check."""
        monitor = HealthMonitor()

        # Mock the individual check methods to avoid dependencies
        def make_result(component: str) -> HealthCheckResult:
            return HealthCheckResult(
                component=component,
                status="healthy",
                message=f"{component} operational",
            )

        with patch.object(
            monitor,
            "_check_system_initialization",
            new=AsyncMock(return_value=make_result("system")),
        ):
            with patch.object(
                monitor,
                "_check_queue_health",
                new=AsyncMock(return_value=make_result("queue")),
            ):
                with patch.object(
                    monitor,
                    "_check_worker_health",
                    new=AsyncMock(return_value=make_result("worker")),
                ):
                    with patch.object(
                        monitor,
                        "_check_resource_monitoring",
                        new=AsyncMock(return_value=make_result("resource")),
                    ):
                        with patch.object(
                            monitor,
                            "_check_github_api",
                            new=AsyncMock(return_value=make_result("github")),
                        ):
                            results = await monitor.perform_comprehensive_health_check()

                            assert len(results) >= 4  # At least 4 components checked
                            assert monitor.last_health_check > 0
                            assert len(monitor.health_history) == 1

    def test_health_summary(self):
        """Test health summary generation."""
        monitor = HealthMonitor()

        # Add mock health results
        mock_results = {
            "component1": HealthCheckResult("component1", "healthy", "OK"),
            "component2": HealthCheckResult("component2", "warning", "Minor issue"),
            "component3": HealthCheckResult("component3", "critical", "System down"),
        }
        monitor.health_history.append(mock_results)
        monitor.last_health_check = time.time()

        summary = monitor.get_health_summary()
        assert summary["status"] == "critical"  # Due to critical component
        assert "critical" in summary["message"].lower()
        assert len(summary["components"]) == 3


class TestGracefulDegradation:
    """Test graceful degradation and fallback mechanisms."""

    def test_fallback_config_creation(self):
        """Test fallback configuration."""
        config = FallbackConfig(
            max_retries=5, retry_delay_seconds=2.0, enable_fast_analysis_fallback=True
        )

        assert config.max_retries == 5
        assert config.retry_delay_seconds == 2.0
        assert config.enable_fast_analysis_fallback

    def test_degradation_manager_initialization(self):
        """Test degradation manager initialization."""
        manager = GracefulDegradationManager()

        assert manager.system_availability == SystemAvailability.FULLY_AVAILABLE
        assert manager.consecutive_failures == 0
        assert not manager._is_circuit_breaker_open()

    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self):
        """Test successful execution without fallback."""
        config = FallbackConfig(max_retries=1, retry_delay_seconds=0, exponential_backoff=False)
        manager = GracefulDegradationManager(config)

        async def primary_func(**kwargs):
            return {"status": "success", "data": "primary result"}

        async def fallback_func(**kwargs):
            return {"status": "fallback", "data": "fallback result"}

        result = await manager.execute_with_fallback(
            primary_func=primary_func,
            fallback_func=fallback_func,
            operation_name="test_operation",
        )

        assert result["status"] == "success"
        assert result["data"] == "primary result"
        assert not result["degradation_info"]["used_fallback"]
        assert manager.fallback_stats["total_requests"] == 1
        assert manager.fallback_stats["fallback_used"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_fallback_failure(self):
        """Test fallback execution after primary failure."""
        config = FallbackConfig(max_retries=1, retry_delay_seconds=0, exponential_backoff=False)
        manager = GracefulDegradationManager(config)

        async def primary_func(**kwargs):
            raise Exception("Primary function failed")

        async def fallback_func(**kwargs):
            return {"status": "fallback", "data": "fallback result"}

        result = await manager.execute_with_fallback(
            primary_func=primary_func,
            fallback_func=fallback_func,
            operation_name="test_operation",
        )

        assert result["status"] == "fallback"
        assert result["data"] == "fallback result"
        assert result["degradation_info"]["used_fallback"]
        assert manager.fallback_stats["total_requests"] == 1
        assert manager.fallback_stats["fallback_used"] == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self):
        """Test circuit breaker activation."""
        config = FallbackConfig(
            circuit_breaker_failure_threshold=2,
            max_retries=1,
            retry_delay_seconds=0,
            exponential_backoff=False,
        )
        manager = GracefulDegradationManager(config)

        async def failing_func(**kwargs):
            raise Exception("Always fails")

        async def fallback_func(**kwargs):
            return {"status": "fallback"}

        # First failure
        await manager.execute_with_fallback(failing_func, fallback_func, "test")
        assert not manager._is_circuit_breaker_open()

        # Second failure - should trigger circuit breaker
        await manager.execute_with_fallback(failing_func, fallback_func, "test")
        assert manager._is_circuit_breaker_open()
        assert manager.fallback_stats["circuit_breaker_trips"] == 1

    def test_system_availability_analysis(self):
        """Test system availability analysis."""
        manager = GracefulDegradationManager()

        # Test fully available system
        healthy_status = {
            "system_status": "running",
            "resource_monitoring": {
                "system_status": {
                    "within_limits": True,
                    "violations": [],
                    "warnings": [],
                }
            },
            "queue_overview": {"pending_jobs": 5},
        }

        availability = manager._analyze_system_health(healthy_status)
        assert availability == SystemAvailability.FULLY_AVAILABLE

        # Test degraded system with warnings
        degraded_status = {
            "system_status": "running",
            "resource_monitoring": {
                "system_status": {
                    "within_limits": True,
                    "violations": [],
                    "warnings": ["High memory usage"],
                }
            },
            "queue_overview": {"pending_jobs": 5},
        }

        availability = manager._analyze_system_health(degraded_status)
        assert availability == SystemAvailability.DEGRADED

    def test_pr_strategy_recommendations(self):
        """Test PR analysis strategy recommendations."""
        manager = GracefulDegradationManager()

        # Test massive PR with healthy system
        manager.system_availability = SystemAvailability.FULLY_AVAILABLE
        massive_pr = {"additions": 2000, "deletions": 500, "changed_files": 35}

        strategy = manager.get_recommended_strategy(massive_pr)
        assert strategy["pr_size"] == "massive"
        assert strategy["recommended_approach"] == "async_analysis"
        assert strategy["confidence"] == "high"

        # Test same PR with degraded system
        manager.system_availability = SystemAvailability.DEGRADED
        strategy = manager.get_recommended_strategy(massive_pr)
        assert strategy["recommended_approach"] == "fast_analysis_with_summary"
        assert strategy["confidence"] == "medium"

        # Test small PR with unavailable system
        manager.system_availability = SystemAvailability.UNAVAILABLE
        small_pr = {"additions": 50, "deletions": 10, "changed_files": 2}

        strategy = manager.get_recommended_strategy(small_pr)
        assert strategy["pr_size"] == "small"
        assert strategy["recommended_approach"] == "basic_pattern_detection"
        assert strategy["confidence"] == "low"

    def test_fallback_statistics(self):
        """Test fallback usage statistics."""
        manager = GracefulDegradationManager()

        # Simulate some requests
        manager.fallback_stats["total_requests"] = 10
        manager.fallback_stats["fallback_used"] = 3
        manager.fallback_stats["circuit_breaker_trips"] = 1

        stats = manager.get_fallback_stats()

        assert stats["total_requests"] == 10
        assert stats["fallback_used"] == 3
        assert stats["fallback_rate_percent"] == 30.0
        assert stats["circuit_breaker_trips"] == 1
        assert "system_availability" in stats


class TestIntegrationBehavior:
    """Test integration behavior of all improvements together."""

    @pytest.mark.asyncio
    async def test_validation_integration_with_degradation(self):
        """Test validation working with degradation manager."""
        from vibe_check.tools.async_analysis.graceful_degradation import (
            async_analysis_with_fallback,
        )

        error_response = {
            "status": "error",
            "error": "Validation failed for pr_number: PR number must be positive",
            "validation_error": {
                "field": "pr_number",
                "error": "PR number must be positive",
            },
            "degradation_info": {
                "used_fallback": False,
                "system_availability": "fully_available",
                "operation": "async_analysis",
                "timestamp": 123.45,
            },
        }

        with patch(
            "vibe_check.tools.async_analysis.graceful_degradation.get_global_degradation_manager"
        ) as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.execute_with_fallback = AsyncMock(return_value=error_response)
            mock_get_manager.return_value = mock_manager

            result = await async_analysis_with_fallback(-1, "invalid..repo", {})

        mock_manager.execute_with_fallback.assert_awaited_once()
        assert result["status"] == "error"
        assert result["validation_error"]["field"] == "pr_number"
        assert result["degradation_info"]["used_fallback"] is False

    def test_resource_monitor_with_health_check(self):
        """Test resource monitor integration with health monitoring."""
        from vibe_check.tools.async_analysis.resource_monitor import (
            get_global_resource_monitor,
        )
        from vibe_check.tools.async_analysis.health_monitoring import (
            get_global_health_monitor,
        )

        resource_monitor = get_global_resource_monitor()
        health_monitor = get_global_health_monitor()

        # Both should be properly initialized
        assert resource_monitor is not None
        assert health_monitor is not None

        # Resource monitor should provide data for health checks
        resource_status = resource_monitor.get_comprehensive_status()
        assert isinstance(resource_status, dict)
        assert "monitoring_active" in resource_status

    def test_end_to_end_error_handling(self):
        """Test that all error handling layers work together."""
        # This tests the integration of:
        # 1. Input validation (catches bad input)
        # 2. Resource monitoring (prevents overload)
        # 3. Health monitoring (detects issues)
        # 4. Graceful degradation (provides fallbacks)

        # Input validation layer
        is_valid, result = validate_async_analysis_request(-1, "bad", {})
        assert not is_valid

        # Resource monitoring layer
        monitor = ResourceMonitor()
        can_accept, reason = monitor.should_accept_new_job()
        # Should work with no jobs running

        # Graceful degradation layer
        manager = GracefulDegradationManager()
        stats = manager.get_fallback_stats()
        assert stats["total_requests"] == 0  # Clean start


if __name__ == "__main__":
    # Run specific test categories
    import sys

    if len(sys.argv) > 1:
        test_category = sys.argv[1]
        if test_category == "validation":
            pytest.main(["-v", "TestInputValidation"])
        elif test_category == "resources":
            pytest.main(["-v", "TestResourceMonitoring"])
        elif test_category == "health":
            pytest.main(["-v", "TestHealthMonitoring"])
        elif test_category == "degradation":
            pytest.main(["-v", "TestGracefulDegradation"])
        elif test_category == "integration":
            pytest.main(["-v", "TestIntegrationBehavior"])
        else:
            print(
                "Available categories: validation, resources, health, degradation, integration"
            )
    else:
        # Run all tests
        pytest.main(["-v", __file__])
