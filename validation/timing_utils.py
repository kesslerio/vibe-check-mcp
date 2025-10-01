#!/usr/bin/env python3
"""
Performance timing utilities for validation scripts
Provides timing measurements for performance monitoring and regression detection
"""

import time
from typing import Dict, List, Any, Optional
from functools import wraps
from contextlib import contextmanager


class PerformanceTimer:
    """High-precision timer for performance measurements"""

    def __init__(self):
        self.timings: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.total_time: float = 0.0

    def start_session(self) -> None:
        """Start a timing session"""
        self.start_time = time.perf_counter()
        self.timings.clear()

    def end_session(self) -> float:
        """End timing session and return total time"""
        if self.start_time is None:
            return 0.0

        self.total_time = time.perf_counter() - self.start_time
        return self.total_time

    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing individual operations"""
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            duration = end - start
            self.timings.append(
                {"operation": operation_name, "duration": duration, "timestamp": start}
            )

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 0.001:
            return f"{seconds * 1000000:.0f}μs"
        elif seconds < 1.0:
            return f"{seconds * 1000:.1f}ms"
        elif seconds < 60.0:
            return f"{seconds:.2f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"

    def check_threshold(self, duration: float, threshold: float = 1.0) -> bool:
        """Check if duration exceeds threshold (default 1 second)"""
        return duration > threshold

    def get_summary(self, threshold: float = 1.0) -> Dict[str, Any]:
        """Get performance summary with statistics"""
        if not self.timings:
            return {
                "total_operations": 0,
                "total_time": self.format_duration(self.total_time),
                "total_time_raw": self.total_time,
                "warnings": [],
            }

        durations = [t["duration"] for t in self.timings]
        warnings = []

        # Check for slow operations
        for timing in self.timings:
            if self.check_threshold(timing["duration"], threshold):
                warnings.append(
                    f"⚠️  {timing['operation']}: {self.format_duration(timing['duration'])} "
                    f"(exceeds {self.format_duration(threshold)} threshold)"
                )

        return {
            "total_operations": len(self.timings),
            "total_time": self.format_duration(self.total_time),
            "total_time_raw": self.total_time,
            "average_time": self.format_duration(sum(durations) / len(durations)),
            "min_time": self.format_duration(min(durations)),
            "max_time": self.format_duration(max(durations)),
            "warnings": warnings,
            "operations": [
                {
                    "name": t["operation"],
                    "duration": self.format_duration(t["duration"]),
                    "duration_raw": t["duration"],
                }
                for t in self.timings
            ],
        }

    def print_summary(self, threshold: float = 1.0, verbose: bool = False) -> None:
        """Print formatted performance summary"""
        summary = self.get_summary(threshold)

        print("\n" + "=" * 60)
        print("PERFORMANCE TIMING SUMMARY")
        print("=" * 60)

        print(f"Total Operations: {summary['total_operations']}")
        print(f"Total Time: {summary['total_time']}")

        if summary["total_operations"] > 0:
            print(f"Average Time: {summary['average_time']}")
            print(f"Min Time: {summary['min_time']}")
            print(f"Max Time: {summary['max_time']}")

        # Print warnings
        if summary["warnings"]:
            print(f"\n⚠️  Performance Warnings ({len(summary['warnings'])}):")
            for warning in summary["warnings"]:
                print(f"   {warning}")
        else:
            print(
                f"\n✅ All operations under {self.format_duration(threshold)} threshold"
            )

        # Print detailed timings if verbose
        if verbose and summary["operations"]:
            print(f"\nDetailed Timings:")
            print("-" * 40)
            for op in summary["operations"]:
                print(f"  {op['name']}: {op['duration']}")


def timed_function(operation_name: str = None, timer: PerformanceTimer = None):
    """Decorator to time function execution"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            if timer is None:
                # Create a standalone timer if none provided
                timer = PerformanceTimer()
                timer.start_session()
                standalone = True
            else:
                standalone = False

            name = operation_name or func.__name__

            with timer.time_operation(name):
                result = func(*args, **kwargs)

            if standalone:
                timer.end_session()
                timer.print_summary()

            return result

        return wrapper

    return decorator
