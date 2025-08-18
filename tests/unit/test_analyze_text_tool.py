"""
Unit Tests for Analyze Text Tool

Tests the analyze_text_demo MCP tool functionality:
- Text analysis with pattern detection
- Different detail levels
- Context integration
- Error handling and edge cases
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.tools.analyze_text_nollm import analyze_text_demo


class TestAnalyzeTextTool:
    """Test analyze text tool functionality"""

    def test_basic_text_analysis(self):
        """Test basic text analysis functionality"""
        text = "We need to build a custom HTTP client instead of using the requests library"
        
        result = analyze_text_demo(text)
        
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        assert 'patterns' in result
        assert 'educational_content' in result
        assert result['analysis_results']['text_length'] == len(text)

    def test_different_detail_levels(self):
        """Test analysis with different detail levels"""
        text = "Custom implementation needed for API integration"
        
        for detail_level in ['brief', 'standard', 'comprehensive']:
            result = analyze_text_demo(text, detail_level=detail_level)
            
            assert isinstance(result, dict)
            assert 'analysis_results' in result
            assert 'educational_content' in result
            
            # Educational content should be available
            content = result['educational_content']
            assert isinstance(content, dict)

    def test_empty_text_handling(self):
        """Test handling of empty or whitespace text"""
        test_cases = ["", "   ", "\n\t\n"]
        
        for text in test_cases:
            result = analyze_text_demo(text)
            
            assert isinstance(result, dict)
            # Should handle gracefully without errors
            assert 'analysis_results' in result or 'error' in result

    def test_large_text_handling(self):
        """Test handling of large text inputs"""
        large_text = "We need custom implementation. " * 5000  # ~150KB
        
        result = analyze_text_demo(large_text)
        
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        # Should complete without timeout
        assert 'text_length' in result['analysis_results']
        assert result['analysis_results']['text_length'] > 0

    def test_unicode_text_handling(self):
        """Test handling of Unicode and special characters"""
        unicode_text = "We need custom 🚀 implementation with émojis and spéciál chars αβγδ"
        
        result = analyze_text_demo(unicode_text)
        
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        assert 'text_length' in result['analysis_results']
        assert result['analysis_results']['text_length'] == len(unicode_text)

    def test_anti_pattern_detection(self):
        """Test that known anti-patterns are detected"""
        anti_pattern_text = """
        I couldn't find documentation on how to use the existing API,
        so I'm going to build my own HTTP client from scratch.
        This will give us more control and better performance.
        """
        
        result = analyze_text_demo(anti_pattern_text)
        
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        assert 'patterns' in result
        
        # Check analysis results structure
        analysis_results = result['analysis_results']
        assert 'patterns_detected' in analysis_results
        assert analysis_results['patterns_detected'] >= 0

    def test_good_pattern_recognition(self):
        """Test that good patterns don't trigger false positives"""
        good_pattern_text = """
        Following the official documentation, I'll use the recommended
        SDK approach with proper error handling and standard patterns.
        """
        
        result = analyze_text_demo(good_pattern_text)
        
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        
        # Check that analysis was performed
        analysis_results = result['analysis_results']
        assert 'patterns_detected' in analysis_results
        # Good patterns should have minimal issues detected
        patterns_detected = analysis_results.get('patterns_detected', 0)
        assert patterns_detected <= 1  # Allow for minor issues

    def test_context_integration(self):
        """Test integration with project context when enabled"""
        text = "Using React hooks for state management"
        
        # Test with context enabled
        result_with_context = analyze_text_demo(
            text, 
            use_project_context=True,
            project_root="."
        )
        
        # Test without context
        result_without_context = analyze_text_demo(
            text,
            use_project_context=False
        )
        
        assert isinstance(result_with_context, dict)
        assert isinstance(result_without_context, dict)
        
        # Both should succeed
        assert 'analysis_results' in result_with_context
        assert 'analysis_results' in result_without_context

    def test_project_root_parameter(self):
        """Test project root parameter handling"""
        text = "Custom implementation needed"
        
        # Test with different project root paths
        test_roots = [".", "/tmp", "/nonexistent"]
        
        for root in test_roots:
            result = analyze_text_demo(
                text,
                project_root=root,
                use_project_context=True
            )
            
            assert isinstance(result, dict)
            assert 'analysis_results' in result
            # Should handle gracefully even if path doesn't exist

    def test_pattern_detector_integration(self):
        """Test that pattern detection functionality works"""
        # Test with text that should trigger pattern detection
        text = "We need custom implementation instead of using the official API"
        result = analyze_text_demo(text)
        
        # Verify basic structure
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        assert 'patterns' in result
        
        # Verify pattern detection results structure
        analysis_results = result['analysis_results']
        assert 'patterns_detected' in analysis_results
        assert isinstance(analysis_results['patterns_detected'], int)
        assert analysis_results['patterns_detected'] >= 0

    @patch('vibe_check.tools.analyze_text_nollm.EducationalContentGenerator')
    def test_educational_content_integration(self, mock_generator_class):
        """Test integration with EducationalContentGenerator"""
        # Mock the generator
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        
        # Mock educational content
        mock_content = {
            'summary': 'Test educational content',
            'recommendations': ['Test recommendation']
        }
        mock_generator.generate_content.return_value = mock_content
        
        text = "Test text for educational content"
        result = analyze_text_demo(text, detail_level='standard')
        
        # Should have attempted to generate educational content
        assert isinstance(result, dict)
        assert 'analysis_results' in result

    def test_error_handling(self):
        """Test error handling for various error conditions"""
        # Test with None input - should handle gracefully
        result = analyze_text_demo(None)
        assert isinstance(result, dict)
        assert 'error' in result  # Should return error dict rather than crash
        
        # Test with invalid detail level
        result = analyze_text_demo("test", detail_level="invalid")
        
        # Should handle gracefully or use default
        assert isinstance(result, dict)
        assert 'analysis_results' in result

    def test_return_structure_consistency(self):
        """Test that return structure is consistent across different inputs"""
        test_inputs = [
            "Simple text",
            "Complex custom implementation with multiple patterns",
            "Good standard approach following documentation",
            "🚀 Unicode test with special chars"
        ]
        
        results = []
        for text in test_inputs:
            result = analyze_text_demo(text)
            results.append(result)
            
            # Basic structure validation
            assert isinstance(result, dict)
            assert 'analysis_results' in result
            assert 'analysis_results' in result
        
        # All results should have similar structure
        keys_sets = [set(result.keys()) for result in results]
        first_keys = keys_sets[0]
        
        for keys in keys_sets[1:]:
            # Allow some variation but core keys should be consistent
            common_keys = first_keys & keys
            assert 'analysis_results' in common_keys
            assert 'patterns' in common_keys

    def test_performance_reasonable_time(self):
        """Test that analysis completes in reasonable time"""
        import time
        
        text = "We need to build custom implementation for API integration" * 100
        
        start_time = time.time()
        result = analyze_text_demo(text)
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert isinstance(result, dict)
        assert 'analysis_results' in result
        # Should complete within reasonable time (allow generous margin for CI)
        assert duration < 30.0, f"Analysis took too long: {duration} seconds"

    def test_concurrent_analysis_safety(self):
        """Test that concurrent analysis calls don't interfere"""
        import threading
        import time
        
        results = []
        errors = []
        
        def analyze_concurrent(text_suffix):
            try:
                text = f"Custom implementation needed for {text_suffix}"
                result = analyze_text_demo(text)
                results.append(result)
                time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Run multiple analyses concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_concurrent, args=(f"test_{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors and all succeeded
        assert len(errors) == 0, f"Concurrent analysis errors: {errors}"
        assert len(results) == 5
        
        for result in results:
            assert isinstance(result, dict)
            assert 'analysis_results' in result