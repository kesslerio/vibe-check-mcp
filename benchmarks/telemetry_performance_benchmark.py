#!/usr/bin/env python3
"""
Performance Benchmark Suite for Telemetry System

Validates that the telemetry system meets performance requirements:
- <5% overhead on existing operations
- <10MB memory usage for normal operations  
- <1ms additional latency per operation
- 1000+ requests/minute throughput
"""

import asyncio
import gc
import json
import os
import psutil
import statistics
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.mentor.telemetry import (
    BasicTelemetryCollector,
    track_latency,
    get_telemetry_collector,
    TelemetryContext
)
from vibe_check.mentor.metrics import RouteType, ResponseMetrics


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test"""
    name: str
    baseline_ms: float
    with_telemetry_ms: float
    overhead_percent: float
    memory_mb: float
    throughput_per_sec: float
    passed: bool
    details: Dict[str, Any]


@dataclass  
class PerformanceReport:
    """Complete performance validation report"""
    timestamp: str
    system_info: Dict[str, str]
    results: List[BenchmarkResult]
    overall_passed: bool
    summary: Dict[str, Any]


class SystemProfiler:
    """Profile system resources during benchmarks"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = 0
    
    @contextmanager
    def measure_memory(self):
        """Context manager to measure memory usage"""
        gc.collect()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        yield
        
        gc.collect()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = current_memory - self.baseline_memory
        
        # Store result for access
        self.last_memory_delta = memory_delta
    
    def get_system_info(self) -> Dict[str, str]:
        """Get system information for benchmark report"""
        return {
            "python_version": sys.version,
            "cpu_count": str(psutil.cpu_count()),
            "memory_gb": f"{psutil.virtual_memory().total / 1024**3:.1f}",
            "platform": sys.platform
        }


class TelemetryBenchmarks:
    """Comprehensive telemetry performance benchmarks"""
    
    def __init__(self):
        self.profiler = SystemProfiler()
        self.results: List[BenchmarkResult] = []
    
    async def run_all_benchmarks(self) -> PerformanceReport:
        """Run complete benchmark suite"""
        print("🚀 Starting Telemetry Performance Benchmark Suite")
        print("=" * 60)
        
        # Test individual components
        await self.benchmark_decorator_overhead()
        self.benchmark_record_response_performance()
        self.benchmark_concurrent_access()
        self.benchmark_memory_usage()
        self.benchmark_json_export_performance()
        await self.benchmark_throughput_capacity()
        self.benchmark_cache_integration()
        
        # Generate report
        return self._generate_report()
    
    async def benchmark_decorator_overhead(self):
        """Measure @track_latency decorator overhead"""
        print("\n🔍 Testing @track_latency decorator overhead...")
        
        # Define test functions
        async def test_function_baseline():
            """Baseline function without telemetry"""
            await asyncio.sleep(0.001)  # Simulate 1ms work
            return "result"
        
        @track_latency(RouteType.STATIC, intent="test")
        async def test_function_with_telemetry():
            """Function with telemetry tracking"""
            await asyncio.sleep(0.001)  # Same 1ms work
            return "result"
        
        # Reset telemetry state
        collector = get_telemetry_collector()
        collector.reset_metrics()
        
        # Measure baseline performance
        baseline_times = []
        for _ in range(100):
            start = time.perf_counter()
            await test_function_baseline()
            baseline_times.append((time.perf_counter() - start) * 1000)
        
        baseline_ms = statistics.mean(baseline_times)
        
        # Measure with telemetry
        telemetry_times = []
        for _ in range(100):
            start = time.perf_counter()
            await test_function_with_telemetry()
            telemetry_times.append((time.perf_counter() - start) * 1000)
        
        telemetry_ms = statistics.mean(telemetry_times)
        overhead_percent = ((telemetry_ms - baseline_ms) / baseline_ms) * 100
        
        # Calculate additional latency per operation
        additional_latency_ms = telemetry_ms - baseline_ms
        
        passed = overhead_percent < 5.0 and additional_latency_ms < 1.0
        
        result = BenchmarkResult(
            name="Decorator Overhead",
            baseline_ms=baseline_ms,
            with_telemetry_ms=telemetry_ms,
            overhead_percent=overhead_percent,
            memory_mb=0,  # Not applicable for this test
            throughput_per_sec=0,  # Not applicable
            passed=passed,
            details={
                "additional_latency_ms": additional_latency_ms,
                "baseline_std": statistics.stdev(baseline_times),
                "telemetry_std": statistics.stdev(telemetry_times),
                "samples": 100
            }
        )
        
        self.results.append(result)
        self._print_result(result, 
                          f"Additional latency: {additional_latency_ms:.3f}ms")
    
    def benchmark_record_response_performance(self):
        """Measure BasicTelemetryCollector.record_response() performance"""
        print("\n📊 Testing record_response() performance...")
        
        collector = BasicTelemetryCollector()
        collector.reset_metrics()
        
        # Baseline: measure time without recording
        def baseline_operation():
            # Simulate the work that would happen without telemetry
            data = {
                "route_type": RouteType.STATIC,
                "latency_ms": 100.0,
                "success": True,
                "intent": "test",
                "query_length": 50,
                "response_length": 200
            }
            return data
        
        baseline_times = []
        for _ in range(1000):
            start = time.perf_counter()
            baseline_operation()
            baseline_times.append((time.perf_counter() - start) * 1000)
        
        baseline_ms = statistics.mean(baseline_times)
        
        # With telemetry: measure record_response time
        def telemetry_operation():
            collector.record_response(
                route_type=RouteType.STATIC,
                latency_ms=100.0,
                success=True,
                intent="test",
                query_length=50,
                response_length=200
            )
        
        telemetry_times = []
        for _ in range(1000):
            start = time.perf_counter()
            telemetry_operation()
            telemetry_times.append((time.perf_counter() - start) * 1000)
        
        telemetry_ms = statistics.mean(telemetry_times)
        overhead_percent = ((telemetry_ms - baseline_ms) / baseline_ms) * 100 if baseline_ms > 0 else 0
        
        passed = telemetry_ms < 1.0  # Should be sub-millisecond
        
        result = BenchmarkResult(
            name="Record Response Performance",
            baseline_ms=baseline_ms,
            with_telemetry_ms=telemetry_ms,
            overhead_percent=overhead_percent,
            memory_mb=0,
            throughput_per_sec=1000 / (telemetry_ms / 1000) if telemetry_ms > 0 else 0,
            passed=passed,
            details={
                "recording_time_ms": telemetry_ms,
                "samples": 1000,
                "metrics_recorded": collector.get_summary().total_requests
            }
        )
        
        self.results.append(result)
        self._print_result(result, f"Recording time: {telemetry_ms:.4f}ms")
    
    def benchmark_concurrent_access(self):
        """Test thread safety and performance under concurrent access"""
        print("\n🔄 Testing concurrent access performance...")
        
        collector = BasicTelemetryCollector()
        collector.reset_metrics()
        
        def record_metrics_batch(thread_id: int, count: int):
            """Record metrics from a single thread"""
            times = []
            for i in range(count):
                start = time.perf_counter()
                collector.record_response(
                    route_type=RouteType.DYNAMIC,
                    latency_ms=float(i % 100),
                    success=(i % 10) != 0,  # 90% success rate
                    intent=f"thread_{thread_id}_intent",
                    query_length=50 + (i % 50),
                    response_length=200 + (i % 200)
                )
                times.append((time.perf_counter() - start) * 1000)
            return times
        
        # Test with multiple threads
        num_threads = 10
        operations_per_thread = 100
        
        with self.profiler.measure_memory():
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(record_metrics_batch, i, operations_per_thread)
                    for i in range(num_threads)
                ]
                
                all_times = []
                for future in as_completed(futures):
                    thread_times = future.result()
                    all_times.extend(thread_times)
            
            total_time = (time.perf_counter() - start_time) * 1000
        
        memory_used = self.profiler.last_memory_delta
        total_operations = num_threads * operations_per_thread
        avg_operation_time = statistics.mean(all_times)
        throughput_per_sec = total_operations / (total_time / 1000)
        
        # Validate data integrity
        summary = collector.get_summary()
        data_integrity_ok = summary.total_requests == total_operations
        
        passed = (avg_operation_time < 1.0 and 
                 throughput_per_sec > 1000 and 
                 data_integrity_ok and
                 memory_used < 10.0)
        
        result = BenchmarkResult(
            name="Concurrent Access",
            baseline_ms=0,  # Not applicable
            with_telemetry_ms=avg_operation_time,
            overhead_percent=0,  # Not applicable
            memory_mb=memory_used,
            throughput_per_sec=throughput_per_sec,
            passed=passed,
            details={
                "num_threads": num_threads,
                "operations_per_thread": operations_per_thread,
                "total_operations": total_operations,
                "data_integrity": data_integrity_ok,
                "p95_latency": statistics.quantiles(all_times, n=20)[18],  # ~p95
                "p99_latency": statistics.quantiles(all_times, n=100)[98] if len(all_times) > 100 else max(all_times)
            }
        )
        
        self.results.append(result)
        self._print_result(result, 
                          f"Throughput: {throughput_per_sec:.0f} ops/sec, "
                          f"Memory: {memory_used:.2f}MB")
    
    def benchmark_memory_usage(self):
        """Test memory usage with large numbers of metrics"""
        print("\n💾 Testing memory usage with 1000+ metrics...")
        
        collector = BasicTelemetryCollector(max_metrics_history=2000)
        collector.reset_metrics()
        
        with self.profiler.measure_memory():
            # Store 1500 metrics to test memory usage
            route_types = list(RouteType)
            for i in range(1500):
                collector.record_response(
                    route_type=route_types[i % len(route_types)],
                    latency_ms=float(i % 1000),
                    success=(i % 5) != 0,  # 80% success rate
                    intent=f"intent_{i % 20}",  # 20 different intents
                    query_length=50 + (i % 200),
                    response_length=100 + (i % 500)
                )
        
        memory_used = self.profiler.last_memory_delta
        
        # Test JSON export performance with large dataset
        start = time.perf_counter()
        summary = collector.get_summary()
        export_time = (time.perf_counter() - start) * 1000
        
        # Validate metrics are properly stored and bounded
        summary_dict = summary.to_dict()
        metrics_stored = len(collector.get_recent_metrics(2000))
        
        passed = (memory_used < 10.0 and 
                 export_time < 100.0 and  # <100ms for JSON export
                 metrics_stored <= 1500)
        
        result = BenchmarkResult(
            name="Memory Usage (1500 metrics)",
            baseline_ms=0,
            with_telemetry_ms=export_time,
            overhead_percent=0,
            memory_mb=memory_used,
            throughput_per_sec=0,
            passed=passed,
            details={
                "metrics_stored": metrics_stored,
                "json_export_time_ms": export_time,
                "json_size_chars": len(json.dumps(summary_dict)),
                "total_requests": summary.total_requests,
                "route_types_tracked": len(summary.route_metrics)
            }
        )
        
        self.results.append(result)
        self._print_result(result, 
                          f"Stored: {metrics_stored} metrics, "
                          f"JSON export: {export_time:.2f}ms")
    
    def benchmark_json_export_performance(self):
        """Test get_telemetry_summary() JSON export performance"""
        print("\n📄 Testing JSON export performance...")
        
        collector = BasicTelemetryCollector()
        collector.reset_metrics()
        
        # Fill with realistic data
        for i in range(500):
            collector.record_response(
                route_type=RouteType.DYNAMIC if i % 3 == 0 else RouteType.STATIC,
                latency_ms=50.0 + (i % 200),
                success=(i % 8) != 0,
                intent=f"intent_type_{i % 10}",
                query_length=20 + (i % 100),
                response_length=100 + (i % 300)
            )
        
        # Benchmark JSON export
        export_times = []
        json_sizes = []
        
        for _ in range(50):
            start = time.perf_counter()
            summary = collector.get_summary()
            summary_dict = summary.to_dict()
            json_str = json.dumps(summary_dict)
            export_time = (time.perf_counter() - start) * 1000
            
            export_times.append(export_time)
            json_sizes.append(len(json_str))
        
        avg_export_time = statistics.mean(export_times)
        avg_json_size = statistics.mean(json_sizes)
        
        passed = avg_export_time < 50.0  # <50ms for JSON export
        
        result = BenchmarkResult(
            name="JSON Export Performance",
            baseline_ms=0,
            with_telemetry_ms=avg_export_time,
            overhead_percent=0,
            memory_mb=0,
            throughput_per_sec=1000 / (avg_export_time / 1000) if avg_export_time > 0 else 0,
            passed=passed,
            details={
                "avg_json_size_chars": int(avg_json_size),
                "export_time_std": statistics.stdev(export_times),
                "samples": 50,
                "max_export_time": max(export_times)
            }
        )
        
        self.results.append(result)
        self._print_result(result, f"JSON size: {int(avg_json_size)} chars")
    
    async def benchmark_throughput_capacity(self):
        """Test sustained throughput capacity"""
        print("\n🚀 Testing sustained throughput capacity...")
        
        collector = BasicTelemetryCollector()
        collector.reset_metrics()
        
        # Test sustained load for 10 seconds
        test_duration = 10.0
        operations_completed = 0
        
        with self.profiler.measure_memory():
            start_time = time.perf_counter()
            end_time = start_time + test_duration
            
            while time.perf_counter() < end_time:
                collector.record_response(
                    route_type=RouteType.HYBRID,
                    latency_ms=75.0,
                    success=True,
                    intent="throughput_test",
                    query_length=100,
                    response_length=250
                )
                operations_completed += 1
                
                # Small delay to prevent overwhelming the CPU
                if operations_completed % 100 == 0:
                    await asyncio.sleep(0.001)
        
        actual_duration = time.perf_counter() - start_time
        throughput_per_sec = operations_completed / actual_duration
        throughput_per_min = throughput_per_sec * 60
        memory_used = self.profiler.last_memory_delta
        
        passed = throughput_per_min > 1000 and memory_used < 10.0
        
        result = BenchmarkResult(
            name="Sustained Throughput",
            baseline_ms=0,
            with_telemetry_ms=0,
            overhead_percent=0,
            memory_mb=memory_used,
            throughput_per_sec=throughput_per_sec,
            passed=passed,
            details={
                "test_duration_sec": actual_duration,
                "operations_completed": operations_completed,
                "throughput_per_minute": throughput_per_min,
                "final_memory_mb": memory_used
            }
        )
        
        self.results.append(result)
        self._print_result(result, 
                          f"Throughput: {throughput_per_min:.0f} ops/min")
    
    def benchmark_cache_integration(self):
        """Test performance impact on cache operations"""
        print("\n🗄️  Testing cache integration impact...")
        
        # Mock cache for testing
        class MockCache:
            def __init__(self):
                self.operations = 0
                
            def get_stats(self):
                return {"hits": self.operations // 2, "misses": self.operations // 2}
        
        cache = MockCache()
        collector = BasicTelemetryCollector()
        collector.set_cache(cache)
        collector.reset_metrics()
        
        # Baseline cache operations
        baseline_times = []
        for _ in range(1000):
            start = time.perf_counter()
            # Simulate cache operation
            cache.operations += 1
            stats = cache.get_stats()
            baseline_times.append((time.perf_counter() - start) * 1000)
        
        baseline_ms = statistics.mean(baseline_times)
        
        # Cache operations with telemetry integration
        telemetry_times = []
        for _ in range(1000):
            start = time.perf_counter()
            # Cache operation
            cache.operations += 1
            stats = cache.get_stats()
            # Telemetry recording
            collector.record_response(
                route_type=RouteType.CACHE_HIT,
                latency_ms=1.0,
                success=True,
                intent="cache_test",
                query_length=50,
                cache_hit=True
            )
            telemetry_times.append((time.perf_counter() - start) * 1000)
        
        telemetry_ms = statistics.mean(telemetry_times)
        overhead_percent = ((telemetry_ms - baseline_ms) / baseline_ms) * 100
        
        passed = overhead_percent < 5.0
        
        result = BenchmarkResult(
            name="Cache Integration",
            baseline_ms=baseline_ms,
            with_telemetry_ms=telemetry_ms,
            overhead_percent=overhead_percent,
            memory_mb=0,
            throughput_per_sec=0,
            passed=passed,
            details={
                "cache_operations": cache.operations,
                "telemetry_records": collector.get_summary().total_requests,
                "baseline_std": statistics.stdev(baseline_times),
                "telemetry_std": statistics.stdev(telemetry_times)
            }
        )
        
        self.results.append(result)
        self._print_result(result)
    
    def _print_result(self, result: BenchmarkResult, extra_info: str = ""):
        """Print formatted benchmark result"""
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"  {status} {result.name}")
        
        if result.baseline_ms > 0:
            print(f"    Baseline: {result.baseline_ms:.3f}ms")
            print(f"    With telemetry: {result.with_telemetry_ms:.3f}ms")
            print(f"    Overhead: {result.overhead_percent:.2f}%")
        
        if result.memory_mb > 0:
            print(f"    Memory: {result.memory_mb:.2f}MB")
        
        if result.throughput_per_sec > 0:
            print(f"    Throughput: {result.throughput_per_sec:.0f} ops/sec")
        
        if extra_info:
            print(f"    {extra_info}")
    
    def _generate_report(self) -> PerformanceReport:
        """Generate comprehensive performance report"""
        overall_passed = all(r.passed for r in self.results)
        
        # Calculate summary statistics
        overhead_values = [r.overhead_percent for r in self.results if r.overhead_percent > 0]
        memory_values = [r.memory_mb for r in self.results if r.memory_mb > 0]
        throughput_values = [r.throughput_per_sec for r in self.results if r.throughput_per_sec > 0]
        
        summary = {
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r.passed),
            "failed_tests": sum(1 for r in self.results if not r.passed),
            "max_overhead_percent": max(overhead_values) if overhead_values else 0,
            "max_memory_mb": max(memory_values) if memory_values else 0,
            "max_throughput_per_sec": max(throughput_values) if throughput_values else 0,
            "meets_requirements": {
                "overhead_under_5_percent": max(overhead_values) < 5.0 if overhead_values else True,
                "memory_under_10mb": max(memory_values) < 10.0 if memory_values else True,
                "throughput_over_1000_per_min": any(t * 60 > 1000 for t in throughput_values) if throughput_values else False
            }
        }
        
        return PerformanceReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            system_info=self.profiler.get_system_info(),
            results=self.results,
            overall_passed=overall_passed,
            summary=summary
        )


async def main():
    """Run the benchmark suite"""
    benchmarks = TelemetryBenchmarks()
    
    try:
        report = await benchmarks.run_all_benchmarks()
        
        print("\n" + "=" * 60)
        print("📊 TELEMETRY PERFORMANCE VALIDATION REPORT")
        print("=" * 60)
        
        print(f"Timestamp: {report.timestamp}")
        print(f"System: {report.system_info['platform']} - "
              f"{report.system_info['cpu_count']} CPUs - "
              f"{report.system_info['memory_gb']}GB RAM")
        
        print(f"\nResults: {report.summary['passed_tests']}/{report.summary['total_tests']} tests passed")
        print(f"Overall Status: {'✅ PASS' if report.overall_passed else '❌ FAIL'}")
        
        print("\nRequirement Validation:")
        req = report.summary['meets_requirements']
        print(f"  Overhead <5%: {'✅' if req['overhead_under_5_percent'] else '❌'} "
              f"(max {report.summary['max_overhead_percent']:.2f}%)")
        print(f"  Memory <10MB: {'✅' if req['memory_under_10mb'] else '❌'} "
              f"(max {report.summary['max_memory_mb']:.2f}MB)")
        print(f"  Throughput >1000/min: {'✅' if req['throughput_over_1000_per_min'] else '❌'} "
              f"(max {report.summary['max_throughput_per_sec'] * 60:.0f}/min)")
        
        # Save detailed report
        report_path = "/Users/kesslerio/GDrive/Projects/vibe-check-mcp/benchmarks/telemetry_performance_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                "timestamp": report.timestamp,
                "system_info": report.system_info,
                "results": [
                    {
                        "name": r.name,
                        "baseline_ms": r.baseline_ms,
                        "with_telemetry_ms": r.with_telemetry_ms,
                        "overhead_percent": r.overhead_percent,
                        "memory_mb": r.memory_mb,
                        "throughput_per_sec": r.throughput_per_sec,
                        "passed": r.passed,
                        "details": r.details
                    }
                    for r in report.results
                ],
                "overall_passed": report.overall_passed,
                "summary": report.summary
            }, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: {report_path}")
        
        # Exit with appropriate code
        sys.exit(0 if report.overall_passed else 1)
        
    except Exception as e:
        print(f"\n❌ Benchmark suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())