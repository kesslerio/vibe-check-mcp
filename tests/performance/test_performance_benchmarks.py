"""
Performance Tests and Benchmarks

Tests performance characteristics and establishes benchmarks:
- Response time benchmarks
- Memory usage monitoring
- Concurrent request handling
- Large input processing
- Resource utilization limits
"""

import pytest
import time
import threading
import psutil
import os
import sys
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.tools.analyze_text_nollm import analyze_text_demo


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Test performance characteristics and establish benchmarks"""

    def test_small_input_response_time(self, benchmark):
        """Benchmark response time for small input (< 1KB)"""
        small_text = "We need to build a custom HTTP client instead of using the SDK"
        
        def analyze_small():
            return analyze_text_demo(small_text)
        
        result = benchmark(analyze_small)
        
        assert isinstance(result, dict)
        assert 'status' in result
        # Benchmark automatically measures and reports timing

    def test_medium_input_response_time(self, benchmark):
        """Benchmark response time for medium input (~10KB)"""
        medium_text = """
        We need to build a comprehensive custom solution from scratch.
        This involves creating our own HTTP client, authentication system,
        database abstraction layer, caching mechanism, and logging framework.
        The existing solutions don't meet our specific requirements.
        """ * 100  # ~10KB
        
        def analyze_medium():
            return analyze_text_demo(medium_text)
        
        result = benchmark(analyze_medium)
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_large_input_response_time(self, benchmark):
        """Benchmark response time for large input (~100KB)"""
        large_text = """
        Complex custom implementation requirements for enterprise solution.
        We need to build everything from scratch including HTTP clients,
        authentication, authorization, database layers, caching, logging,
        monitoring, alerting, and much more infrastructure.
        """ * 500  # ~100KB
        
        def analyze_large():
            return analyze_text_demo(large_text, detail_level="brief")  # Use brief for speed
        
        result = benchmark(analyze_large)
        
        assert isinstance(result, dict)
        assert 'status' in result

    def test_memory_usage_small_input(self):
        """Test memory usage for small input processing"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        small_text = "Custom implementation needed for API integration"
        
        # Run multiple times to check for memory leaks
        for _ in range(100):
            result = analyze_text_demo(small_text)
            assert isinstance(result, dict)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal for small inputs
        assert memory_increase < 50 * 1024 * 1024, f"Excessive memory usage: {memory_increase} bytes"

    def test_memory_usage_large_input(self):
        """Test memory usage for large input processing"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        large_text = "Custom implementation needed. " * 10000  # ~300KB
        
        result = analyze_text_demo(large_text)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        assert isinstance(result, dict)
        assert 'status' in result
        
        # Memory usage should be proportional but not excessive
        assert memory_increase < 500 * 1024 * 1024, f"Excessive memory usage: {memory_increase} bytes"

    def test_concurrent_request_performance(self):
        """Test performance under concurrent request load"""
        def analyze_concurrent(text_id):
            text = f"Custom implementation needed for request {text_id}"
            start_time = time.time()
            result = analyze_text_demo(text)
            end_time = time.time()
            return {
                'result': result,
                'duration': end_time - start_time,
                'text_id': text_id
            }
        
        # Test with moderate concurrency
        num_concurrent = 10
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(analyze_concurrent, i) for i in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # All requests should complete successfully
        assert len(results) == num_concurrent
        for result_info in results:
            assert isinstance(result_info['result'], dict)
            assert 'status' in result_info['result']
            # Individual requests should complete in reasonable time
            assert result_info['duration'] < 10.0
        
        # Total time should be reasonable (with parallelization)
        assert total_duration < 30.0, f"Concurrent requests took too long: {total_duration}s"
        
        # Calculate average response time
        avg_duration = sum(r['duration'] for r in results) / len(results)
        assert avg_duration < 5.0, f"Average response time too high: {avg_duration}s"

    def test_cpu_usage_monitoring(self):
        """Test CPU usage during processing"""
        process = psutil.Process(os.getpid())
        
        # Get initial CPU percent (need baseline)
        initial_cpu = process.cpu_percent()
        time.sleep(0.1)  # Brief pause for CPU measurement baseline
        
        # Run analysis that should use moderate CPU
        text = "Complex custom implementation analysis. " * 1000
        
        start_time = time.time()
        result = analyze_text_demo(text)
        end_time = time.time()
        
        # Get CPU usage during processing
        cpu_percent = process.cpu_percent()
        
        assert isinstance(result, dict)
        assert 'status' in result
        
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 15.0, f"Processing took too long: {duration}s"
        
        # CPU usage should be reasonable (not max out single core)
        assert cpu_percent < 200.0, f"Excessive CPU usage: {cpu_percent}%"

    def test_response_time_consistency(self):
        """Test consistency of response times across multiple runs"""
        text = "Custom implementation needed for consistency test"
        
        durations = []
        for _ in range(20):
            start_time = time.time()
            result = analyze_text_demo(text)
            end_time = time.time()
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            durations.append(end_time - start_time)
        
        # Calculate statistics
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Response times should be consistent
        assert avg_duration < 3.0, f"Average response time too high: {avg_duration}s"
        assert max_duration < 10.0, f"Max response time too high: {max_duration}s"
        
        # Variance should be reasonable (max shouldn't be much higher than average)
        variance_ratio = max_duration / avg_duration if avg_duration > 0 else float('inf')
        assert variance_ratio < 5.0, f"Response time variance too high: {variance_ratio}x"

    def test_throughput_measurement(self):
        """Test throughput (requests per second) capability"""
        texts = [
            f"Custom implementation needed for throughput test {i}"
            for i in range(50)
        ]
        
        start_time = time.time()
        
        results = []
        for text in texts:
            result = analyze_text_demo(text)
            results.append(result)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # All requests should succeed
        assert len(results) == 50
        for result in results:
            assert isinstance(result, dict)
            assert 'status' in result
        
        # Calculate throughput
        throughput = len(texts) / total_duration  # requests per second
        
        # Should achieve reasonable throughput
        assert throughput > 1.0, f"Throughput too low: {throughput} req/s"
        assert total_duration < 120.0, f"Total processing time too high: {total_duration}s"

    @pytest.mark.slow
    def test_stress_test_large_volume(self):
        """Stress test with large volume of requests"""
        num_requests = 100
        
        def stress_analyze(request_id):
            text = f"Stress test custom implementation {request_id}"
            try:
                result = analyze_text_demo(text)
                return {'success': True, 'result': result, 'id': request_id}
            except Exception as e:
                return {'success': False, 'error': str(e), 'id': request_id}
        
        start_time = time.time()
        
        # Use thread pool for concurrent stress testing
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(stress_analyze, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = len(successful) / len(results)
        
        # Most requests should succeed under stress
        assert success_rate > 0.8, f"Success rate too low under stress: {success_rate}"
        assert len(successful) >= 80, f"Too many failures: {len(failed)} out of {num_requests}"
        
        # Should complete within reasonable time even under stress
        assert total_duration < 300.0, f"Stress test took too long: {total_duration}s"

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run many iterations to detect memory leaks
        for i in range(200):
            text = f"Memory leak test iteration {i}"
            result = analyze_text_demo(text)
            
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Check memory every 50 iterations
            if i % 50 == 0 and i > 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be bounded (allowing for reasonable growth)
                assert memory_increase < 200 * 1024 * 1024, f"Potential memory leak detected: {memory_increase} bytes after {i} iterations"
        
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # Final memory usage should be reasonable
        assert total_increase < 300 * 1024 * 1024, f"Total memory increase too high: {total_increase} bytes"

    def test_detail_level_performance_comparison(self):
        """Compare performance across different detail levels"""
        text = "Custom implementation requirements for performance comparison" * 10
        
        detail_levels = ['brief', 'standard', 'comprehensive']
        timings = {}
        
        for level in detail_levels:
            durations = []
            for _ in range(10):
                start_time = time.time()
                result = analyze_text_demo(text, detail_level=level)
                end_time = time.time()
                
                assert isinstance(result, dict)
                assert 'status' in result
                
                durations.append(end_time - start_time)
            
            timings[level] = sum(durations) / len(durations)
        
        # Brief should be fastest, comprehensive should be slowest
        assert timings['brief'] <= timings['standard'] * 1.5, "Brief should be faster than standard"
        assert timings['standard'] <= timings['comprehensive'] * 1.5, "Standard should be faster than comprehensive"
        
        # All levels should complete in reasonable time
        for level, avg_time in timings.items():
            assert avg_time < 10.0, f"{level} detail level too slow: {avg_time}s"

    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up"""
        import gc
        import weakref
        
        initial_objects = len(gc.get_objects())
        
        # Create and process analysis objects
        for i in range(50):
            text = f"Resource cleanup test {i}"
            result = analyze_text_demo(text)
            assert isinstance(result, dict)
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        # Final garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        object_increase = final_objects - initial_objects
        
        # Object count increase should be reasonable
        assert object_increase < 1000, f"Too many objects created: {object_increase}"