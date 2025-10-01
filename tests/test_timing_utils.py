#!/usr/bin/env python3
"""
Tests for timing utilities
Validates performance measurement functionality
"""

import pytest
import time
from validation.timing_utils import PerformanceTimer, timed_function


class TestPerformanceTimer:
    """Test cases for PerformanceTimer class"""

    def test_timer_initialization(self):
        """Test timer initialization"""
        timer = PerformanceTimer()
        assert timer.timings == []
        assert timer.start_time is None
        assert timer.total_time == 0.0

    def test_session_management(self):
        """Test session start and end"""
        timer = PerformanceTimer()

        timer.start_session()
        assert timer.start_time is not None
        assert timer.timings == []

        time.sleep(0.01)  # Small delay
        total_time = timer.end_session()

        assert total_time > 0.0
        assert timer.total_time == total_time
        assert timer.total_time >= 0.01

    def test_time_operation_context_manager(self):
        """Test timing operations with context manager"""
        timer = PerformanceTimer()
        timer.start_session()

        with timer.time_operation("test_operation"):
            time.sleep(0.01)

        assert len(timer.timings) == 1
        assert timer.timings[0]["operation"] == "test_operation"
        assert timer.timings[0]["duration"] >= 0.01
        assert "timestamp" in timer.timings[0]

    def test_multiple_operations(self):
        """Test timing multiple operations"""
        timer = PerformanceTimer()
        timer.start_session()

        operations = ["op1", "op2", "op3"]
        for op in operations:
            with timer.time_operation(op):
                time.sleep(0.005)  # Small delay

        assert len(timer.timings) == 3
        for i, timing in enumerate(timer.timings):
            assert timing["operation"] == operations[i]
            assert timing["duration"] >= 0.005

    def test_format_duration(self):
        """Test duration formatting"""
        timer = PerformanceTimer()

        # Test microseconds
        assert "μs" in timer.format_duration(0.0005)

        # Test milliseconds
        assert "ms" in timer.format_duration(0.05)

        # Test seconds
        assert "s" in timer.format_duration(1.5)
        assert "ms" not in timer.format_duration(1.5)

        # Test minutes
        formatted = timer.format_duration(125.0)
        assert "m" in formatted and "s" in formatted

    def test_threshold_checking(self):
        """Test threshold checking functionality"""
        timer = PerformanceTimer()

        # Test default threshold (1 second)
        assert not timer.check_threshold(0.5)
        assert timer.check_threshold(1.5)

        # Test custom threshold
        assert not timer.check_threshold(0.5, threshold=0.6)
        assert timer.check_threshold(0.5, threshold=0.4)

    def test_summary_generation(self):
        """Test performance summary generation"""
        timer = PerformanceTimer()
        timer.start_session()

        # Add some operations
        with timer.time_operation("fast_op"):
            time.sleep(0.01)

        with timer.time_operation("slow_op"):
            time.sleep(0.05)

        timer.end_session()
        summary = timer.get_summary(threshold=0.03)

        # Check summary structure
        assert "total_operations" in summary
        assert "total_time" in summary
        assert "average_time" in summary
        assert "min_time" in summary
        assert "max_time" in summary
        assert "warnings" in summary
        assert "operations" in summary

        # Check values
        assert summary["total_operations"] == 2
        assert len(summary["operations"]) == 2

        # Check warnings (slow_op should trigger warning)
        assert len(summary["warnings"]) > 0
        assert "slow_op" in summary["warnings"][0]

    def test_empty_summary(self):
        """Test summary with no operations"""
        timer = PerformanceTimer()
        timer.start_session()
        timer.end_session()

        summary = timer.get_summary()
        assert summary["total_operations"] == 0
        assert summary["warnings"] == []
        assert "operations" not in summary or len(summary["operations"]) == 0


class TestTimedFunction:
    """Test cases for timed_function decorator"""

    def test_decorator_basic_functionality(self):
        """Test basic decorator functionality"""
        timer = PerformanceTimer()
        timer.start_session()

        @timed_function("test_function", timer)
        def sample_function():
            time.sleep(0.01)
            return "result"

        result = sample_function()

        assert result == "result"
        assert len(timer.timings) == 1
        assert timer.timings[0]["operation"] == "test_function"
        assert timer.timings[0]["duration"] >= 0.01

    def test_decorator_without_name(self):
        """Test decorator using function name"""
        timer = PerformanceTimer()
        timer.start_session()

        @timed_function(timer=timer)
        def another_function():
            time.sleep(0.005)
            return 42

        result = another_function()

        assert result == 42
        assert len(timer.timings) == 1
        assert timer.timings[0]["operation"] == "another_function"

    def test_decorator_standalone(self):
        """Test decorator without external timer"""

        @timed_function("standalone_test")
        def standalone_function():
            time.sleep(0.01)
            return "standalone"

        # This should work without throwing exceptions
        # The decorator creates its own timer internally
        result = standalone_function()
        assert result == "standalone"


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""

    def test_validation_script_simulation(self):
        """Simulate validation script timing"""
        timer = PerformanceTimer()
        timer.start_session()

        # Simulate different validation operations
        validation_operations = [
            ("load_patterns", 0.005),
            ("validate_cognee_case", 0.015),
            ("validate_good_case", 0.010),
            ("validate_additional_cases", 0.025),
            ("generate_summary", 0.003),
        ]

        for op_name, sleep_time in validation_operations:
            with timer.time_operation(op_name):
                time.sleep(sleep_time)

        total_time = timer.end_session()
        summary = timer.get_summary(threshold=0.02)

        # Verify all operations were recorded
        assert len(timer.timings) == 5
        assert summary["total_operations"] == 5

        # Check that total time is reasonable
        expected_min_time = sum(sleep_time for _, sleep_time in validation_operations)
        assert total_time >= expected_min_time

        # Verify operations that should trigger warnings
        warnings = summary["warnings"]
        warning_ops = [w for w in warnings if "validate_additional_cases" in w]
        assert len(warning_ops) > 0  # Should warn about slow operation

    def test_performance_regression_detection(self):
        """Test performance regression detection capabilities"""
        timer = PerformanceTimer()

        # Baseline measurement
        timer.start_session()
        with timer.time_operation("baseline_operation"):
            time.sleep(0.01)
        baseline_time = timer.end_session()

        # Simulated regression (slower operation)
        timer.start_session()
        with timer.time_operation("regression_operation"):
            time.sleep(0.025)  # 2.5x slower
        regression_time = timer.end_session()

        # Verify regression detection logic
        regression_ratio = regression_time / baseline_time
        assert regression_ratio > 2.0  # Significant regression

        # Test warning generation
        summary = timer.get_summary(threshold=0.015)
        assert len(summary["warnings"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
