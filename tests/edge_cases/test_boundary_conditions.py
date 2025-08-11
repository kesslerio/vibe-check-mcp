"""
Edge Case Tests for Boundary Conditions and Error Handling

Tests unusual inputs, boundary conditions, and error scenarios:
- Malformed inputs
- Extreme values
- Resource exhaustion scenarios
- Concurrent access edge cases
- System limit testing
"""

import pytest
import sys
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.tools.analyze_text_nollm import analyze_text_demo


@pytest.mark.edge_case
class TestBoundaryConditions:
    """Test boundary conditions and edge cases"""

    def test_extreme_input_sizes(self):
        """Test with extremely small and large inputs"""
        # Test extremely small inputs
        tiny_inputs = ["", "a", "🚀", "\n", " "]
        
        for tiny_input in tiny_inputs:
            result = analyze_text_demo(tiny_input)
            assert isinstance(result, dict)
            assert 'status' in result

        # Test moderately large input
        large_input = "Custom implementation needed for testing. " * 10000  # ~400KB
        
        try:
            result = analyze_text_demo(large_input, detail_level="brief")
            assert isinstance(result, dict)
            assert 'status' in result
        except Exception as e:
            # Large inputs may be rejected, which is acceptable
            assert "size" in str(e).lower() or "limit" in str(e).lower()

    def test_malformed_unicode_input(self):
        """Test with malformed Unicode sequences"""
        malformed_unicode = [
            "\ud800",  # High surrogate without low surrogate
            "\udc00",  # Low surrogate without high surrogate
            "\uffff",  # Non-character
            "\ufffe",  # Non-character
            b'\xff\xfe'.decode('utf-8', errors='ignore'),  # Byte order mark issues
        ]
        
        for malformed in malformed_unicode:
            try:
                result = analyze_text_demo(malformed)
                assert isinstance(result, dict)
                assert 'status' in result
            except UnicodeError:
                # Unicode errors are acceptable for malformed input
                pass

    def test_deeply_nested_structures(self):
        """Test with deeply nested or recursive text patterns"""
        nested_text = "(" * 1000 + "custom implementation" + ")" * 1000
        
        try:
            result = analyze_text_demo(nested_text)
            assert isinstance(result, dict)
            assert 'status' in result
        except (RecursionError, MemoryError):
            # Stack overflow or memory errors are acceptable for extreme nesting
            pass

    def test_special_characters_boundary(self):
        """Test boundary cases with special characters"""
        special_chars = [
            "\x00\x01\x02\x03",  # Control characters
            "\u200b\u200c\u200d",  # Zero-width characters
            "\ufeff",  # Byte order mark
            "​‌‍",  # Various Unicode spaces
            "\r\n\r\n\r\n" * 1000,  # Excessive line breaks
        ]
        
        for chars in special_chars:
            result = analyze_text_demo(chars)
            assert isinstance(result, dict)
            assert 'status' in result

    def test_parameter_boundary_values(self):
        """Test boundary values for parameters"""
        text = "Test boundary parameters"
        
        # Test invalid detail levels
        invalid_levels = ["", "invalid", None, 123, []]
        
        for invalid_level in invalid_levels:
            try:
                result = analyze_text_demo(text, detail_level=invalid_level)
                assert isinstance(result, dict)
                assert 'status' in result
            except (ValueError, TypeError):
                # Type/value errors are acceptable for invalid parameters
                pass

    def test_concurrent_resource_contention(self):
        """Test resource contention under high concurrency"""
        results = []
        errors = []
        
        def heavy_analysis(thread_id):
            try:
                # Use different text to avoid caching effects
                text = f"Complex custom implementation analysis for thread {thread_id}" * 100
                result = analyze_text_demo(text, detail_level="comprehensive")
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))
        
        # High concurrency test
        threads = []
        for i in range(20):
            thread = threading.Thread(target=heavy_analysis, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait with timeout
        for thread in threads:
            thread.join(timeout=30)
            if thread.is_alive():
                pytest.fail("Thread did not complete within timeout")
        
        # Most should succeed even under high contention
        success_rate = len(results) / (len(results) + len(errors))
        assert success_rate > 0.7, f"Too many failures under contention: {success_rate}"

    def test_rapid_succession_calls(self):
        """Test rapid successive calls without delays"""
        num_calls = 100
        start_time = time.time()
        
        results = []
        for i in range(num_calls):
            result = analyze_text_demo(f"Rapid call {i}")
            results.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All should succeed
        assert len(results) == num_calls
        for result in results:
            assert isinstance(result, dict)
            assert 'status' in result
        
        # Should handle rapid calls efficiently
        calls_per_second = num_calls / duration
        assert calls_per_second > 5, f"Too slow for rapid calls: {calls_per_second} calls/sec"

    def test_memory_pressure_conditions(self):
        """Test behavior under memory pressure"""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create memory pressure by processing many large texts
        large_texts = [f"Memory pressure test {i}: " + "x" * 10000 for i in range(50)]
        
        results = []
        for text in large_texts:
            try:
                result = analyze_text_demo(text, detail_level="brief")
                results.append(result)
                
                # Force GC periodically
                if len(results) % 10 == 0:
                    gc.collect()
                    
            except MemoryError:
                # Memory errors are acceptable under extreme pressure
                break
        
        # Should handle some level of memory pressure
        assert len(results) > 10, "Failed too early under memory pressure"
        
        # Check for memory leaks
        gc.collect()
        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects
        
        # Object count shouldn't explode
        assert object_increase < len(results) * 100, f"Potential memory leak: {object_increase} objects"

    def test_file_system_edge_cases(self):
        """Test edge cases related to file system access"""
        import tempfile
        import shutil
        
        # Test with non-existent project root
        result = analyze_text_demo(
            "File system test",
            project_root="/nonexistent/path/12345",
            use_project_context=True
        )
        assert isinstance(result, dict)
        assert 'status' in result
        
        # Test with permission denied scenario (simulate)
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Create and immediately remove directory to simulate access issues
                test_dir = os.path.join(temp_dir, "removed")
                os.makedirs(test_dir)
                shutil.rmtree(test_dir)
                
                result = analyze_text_demo(
                    "Permission test",
                    project_root=test_dir,
                    use_project_context=True
                )
                assert isinstance(result, dict)
                assert 'status' in result
                
            except PermissionError:
                # Permission errors are expected and acceptable
                pass

    def test_encoding_edge_cases(self):
        """Test various encoding edge cases"""
        # Different encoding scenarios
        encoding_tests = [
            "ASCII text",
            "UTF-8: café résumé naïve",
            "Emojis: 🚀🎉🔥💯",
            "Mathematical: ∑∏∆∇√∞",
            "Currency: $€¥₹₿",
            "Chinese: 自定义实现需求",
            "Arabic: تنفيذ مخصص مطلوب",
            "Russian: требуется пользовательская реализация",
        ]
        
        for test_text in encoding_tests:
            result = analyze_text_demo(test_text)
            assert isinstance(result, dict)
            assert 'status' in result
            
            # Response should be properly encoded
            response_str = str(result)
            assert len(response_str) > 0

    def test_regex_edge_cases(self):
        """Test edge cases that might break regex processing"""
        regex_breaking_texts = [
            "((((((((((Custom implementation))))))))))",  # Excessive parentheses
            "Custom\\\\\\\\\\implementation\\\\\\\\",      # Excessive backslashes
            "Custom.*.*.*.*.*implementation",              # Regex metacharacters
            "Custom[[[[[implementation]]]]]",              # Square brackets
            "Custom{{{{{implementation}}}}}",              # Curly braces
            "Custom^$*+?.|(){}[]\\implementation",         # All regex metacharacters
        ]
        
        for regex_text in regex_breaking_texts:
            try:
                result = analyze_text_demo(regex_text)
                assert isinstance(result, dict)
                assert 'status' in result
            except re.error:
                # Regex errors are acceptable for malicious patterns
                pass

    def test_json_serialization_edge_cases(self):
        """Test edge cases that might break JSON serialization"""
        import json
        
        # Test inputs that might produce non-serializable responses
        problematic_inputs = [
            "Custom implementation with ∞ complexity",
            "Implementation with NaN performance",
            "Custom solution with undefined behavior",
            float('inf'),  # This should cause TypeError
            float('nan'),  # This should cause TypeError
        ]
        
        for problematic_input in problematic_inputs:
            try:
                if isinstance(problematic_input, (float, int)):
                    # Skip non-string inputs for text analysis
                    continue
                    
                result = analyze_text_demo(problematic_input)
                assert isinstance(result, dict)
                assert 'status' in result
                
                # Result should be JSON serializable
                json_str = json.dumps(result)
                parsed = json.loads(json_str)
                assert isinstance(parsed, dict)
                
            except (TypeError, ValueError) as e:
                if "serializable" in str(e) or "JSON" in str(e):
                    pytest.fail(f"Result not JSON serializable: {e}")

    def test_threading_edge_cases(self):
        """Test threading edge cases and race conditions"""
        shared_results = []
        lock = threading.Lock()
        
        def thread_with_shared_state(thread_id):
            # Simulate shared state access
            local_results = []
            
            for i in range(10):
                result = analyze_text_demo(f"Thread {thread_id} iteration {i}")
                local_results.append(result)
                time.sleep(0.001)  # Small delay to encourage race conditions
            
            with lock:
                shared_results.extend(local_results)
        
        # Create multiple threads accessing shared state
        threads = []
        for i in range(10):
            thread = threading.Thread(target=thread_with_shared_state, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All results should be valid
        assert len(shared_results) == 100
        for result in shared_results:
            assert isinstance(result, dict)
            assert 'status' in result

    def test_error_propagation_edge_cases(self):
        """Test edge cases in error handling and propagation"""
        # Mock an internal component to raise various exceptions
        with patch('vibe_check.tools.analyze_text_nollm.PatternDetector') as mock_detector:
            # Test different exception types
            exception_types = [
                ValueError("Invalid pattern configuration"),
                KeyError("Missing pattern key"),
                AttributeError("Attribute not found"),
                RuntimeError("Runtime failure"),
                MemoryError("Out of memory"),
                TimeoutError("Operation timed out"),
            ]
            
            for exception in exception_types:
                mock_detector.side_effect = exception
                
                try:
                    result = analyze_text_demo("Exception propagation test")
                    
                    # If no exception raised, should be proper error format
                    assert isinstance(result, dict)
                    assert 'status' in result
                    if result['status'] == 'error':
                        assert 'error' in result or 'message' in result
                        
                except Exception as e:
                    # Some exceptions may propagate, which is acceptable
                    assert isinstance(e, type(exception))

    def test_cleanup_edge_cases(self):
        """Test resource cleanup in edge cases"""
        import tempfile
        import weakref
        
        # Create temporary resources that should be cleaned up
        temp_files = []
        weak_refs = []
        
        for i in range(10):
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(f"Temporary content {i}".encode())
            temp_file.close()
            temp_files.append(temp_file.name)
            
            # Create weak reference to track cleanup
            temp_obj = [f"temp_object_{i}"]
            weak_ref = weakref.ref(temp_obj)
            weak_refs.append(weak_ref)
            
            # Analyze with reference to temporary resources
            result = analyze_text_demo(f"Cleanup test {i} with temp file {temp_file.name}")
            assert isinstance(result, dict)
            assert 'status' in result
        
        # Force cleanup
        import gc
        gc.collect()
        
        # Check that weak references are cleaned up
        alive_refs = sum(1 for ref in weak_refs if ref() is not None)
        assert alive_refs <= len(weak_refs) // 2, "Too many objects not cleaned up"
        
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass  # File may already be cleaned up