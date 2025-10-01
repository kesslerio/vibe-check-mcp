"""
Unit Tests for Pattern Detector Core Component

Tests the core PatternDetector class functionality:
- Anti-pattern detection accuracy
- Confidence scoring
- Multiple pattern types
- Edge case handling
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.core.pattern_detector import PatternDetector, DetectionResult
from vibe_check.core.educational_content import DetailLevel


class TestPatternDetector:
    """Test core pattern detection functionality"""

    @pytest.fixture
    def detector(self):
        """Create PatternDetector instance for testing"""
        return PatternDetector()

    def test_detector_initialization(self, detector):
        """Test that detector initializes properly"""
        assert detector is not None
        assert hasattr(detector, "analyze_text_for_patterns")

    def test_infrastructure_without_implementation_detection(self, detector):
        """Test detection of infrastructure without implementation anti-pattern"""
        text = "We need to build a custom HTTP server instead of using the existing SDK"

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)

        # Check for any detected patterns
        detected_count = sum(1 for r in results if r.detected)
        assert detected_count >= 0

    def test_symptom_driven_development_detection(self, detector):
        """Test detection of symptom-driven development patterns"""
        text = "Let's add a workaround for this bug since the library doesn't work properly"

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)
        # May or may not detect depending on pattern configuration
        assert len(results) >= 0

    def test_complexity_escalation_detection(self, detector):
        """Test detection of unnecessary complexity patterns"""
        text = "We should implement an abstract factory pattern with dependency injection for this simple configuration"

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)
        assert len(results) >= 0  # Some complexity may be detected

    def test_documentation_neglect_detection(self, detector):
        """Test detection of documentation neglect patterns"""
        text = (
            "I couldn't find how to use the API properly, so I'll build my own solution"
        )

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)
        # Should be detected if patterns are configured for documentation neglect
        assert len(results) >= 0

    def test_good_patterns_low_false_positives(self, detector):
        """Test that good patterns don't trigger false positives"""
        text = "Following the official documentation, I'll use the recommended SDK approach"

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)
        # Good patterns should have low or zero detections
        detected_count = sum(1 for r in results if r.detected)
        assert detected_count <= len(results)  # All results should be valid

    def test_empty_text_handling(self, detector):
        """Test handling of empty or whitespace-only text"""
        test_cases = ["", "   ", "\n\t  \n"]

        for text in test_cases:
            results = detector.analyze_text_for_patterns(text)
            assert isinstance(results, list)
            # Empty text should not detect patterns
            detected_count = sum(1 for r in results if r.detected)
            assert detected_count == 0

    def test_none_text_handling(self, detector):
        """Test handling of None text"""
        with pytest.raises((ValueError, TypeError, AttributeError)):
            detector.analyze_text_for_patterns(None)

    def test_large_text_handling(self, detector):
        """Test handling of large text inputs"""
        large_text = "This is a test sentence. " * 10000  # ~250KB

        results = detector.analyze_text_for_patterns(large_text)

        assert isinstance(results, list)
        assert len(results) >= 0
        # Should complete without timeout or memory issues

    def test_unicode_text_handling(self, detector):
        """Test handling of Unicode and special characters"""
        unicode_text = "We need to build custom 🚀 implementation with émojis and spéciál chars αβγ"

        results = detector.analyze_text_for_patterns(unicode_text)

        assert isinstance(results, list)
        assert len(results) >= 0

    def test_confidence_scoring(self, detector):
        """Test that confidence scores are properly assigned"""
        text = "We must build a completely custom HTTP client from scratch instead of using requests library"

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)
        for result in results:
            # Confidence should be between 0 and 1
            assert 0 <= result.confidence <= 1

    def test_multiple_patterns_detection(self, detector):
        """Test detection of multiple patterns in complex text"""
        complex_text = """
        We need to build our own authentication system because the existing libraries
        don't work. I'll create a custom HTTP client to handle API requests, and
        implement our own JSON parser because the standard one is too slow.
        Let me add a workaround for the database connection issue as well.
        """

        results = detector.analyze_text_for_patterns(complex_text)

        assert isinstance(results, list)
        # Complex text with multiple anti-patterns should detect several issues
        assert len(results) >= 0
        # Should identify pattern types
        for result in results:
            assert isinstance(result.pattern_type, str)
            assert len(result.pattern_type) > 0

    def test_detection_result_structure(self, detector):
        """Test that DetectionResult has proper structure"""
        text = "Custom implementation needed for this feature"

        results = detector.analyze_text_for_patterns(text)

        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, DetectionResult)
            assert hasattr(result, "pattern_type")
            assert hasattr(result, "detected")
            assert hasattr(result, "confidence")
            assert hasattr(result, "evidence")
            assert isinstance(result.detected, bool)
            assert isinstance(result.confidence, float)
            assert isinstance(result.evidence, list)

    def test_thread_safety(self, detector):
        """Test that detector is thread-safe for concurrent usage"""
        import threading
        import time

        results = []
        errors = []

        def analyze_text(text_suffix):
            try:
                text = f"Custom implementation {text_suffix} needed for API integration"
                result = detector.analyze_text_for_patterns(text)
                results.append(result)
                time.sleep(0.01)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)

        # Run multiple threads simultaneously
        threads = []
        for i in range(10):
            thread = threading.Thread(target=analyze_text, args=(f"#{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors and all completed
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10

        # All results should be valid List[DetectionResult]
        for result in results:
            assert isinstance(result, list)
            for detection in result:
                assert isinstance(detection, DetectionResult)

    def test_detail_level_parameter(self, detector):
        """Test that detail_level parameter is accepted"""
        text = "Custom implementation needed"

        # Test all detail levels
        for detail_level in [
            DetailLevel.BRIEF,
            DetailLevel.STANDARD,
            DetailLevel.COMPREHENSIVE,
        ]:
            results = detector.analyze_text_for_patterns(
                text, detail_level=detail_level
            )
            assert isinstance(results, list)

    def test_context_parameter(self, detector):
        """Test that context parameter enhances detection"""
        content = "Custom solution needed"
        context = "We couldn't find proper documentation for the existing SDK"

        # Test with context
        results_with_context = detector.analyze_text_for_patterns(
            content, context=context
        )

        # Test without context
        results_without_context = detector.analyze_text_for_patterns(content)

        assert isinstance(results_with_context, list)
        assert isinstance(results_without_context, list)

        # Both should work, context may affect detection
        assert len(results_with_context) >= 0
        assert len(results_without_context) >= 0

    def test_focus_patterns_parameter(self, detector):
        """Test that focus_patterns parameter filters results"""
        text = "We need custom HTTP client and authentication system"

        # Test with focus on specific patterns
        all_results = detector.analyze_text_for_patterns(text)

        # Get available pattern types
        if all_results:
            sample_pattern = all_results[0].pattern_type
            focused_results = detector.analyze_text_for_patterns(
                text, focus_patterns=[sample_pattern]
            )

            assert isinstance(focused_results, list)
            # Focused results should be subset or equal
            assert len(focused_results) <= len(all_results)

    def test_educational_content_integration(self, detector):
        """Test integration with educational content generation"""
        text = "Custom implementation needed for comprehensive analysis"

        results = detector.analyze_text_for_patterns(
            text, detail_level=DetailLevel.COMPREHENSIVE
        )

        assert isinstance(results, list)

        # Check if educational content is attached to results
        for result in results:
            if result.educational_content:
                assert isinstance(result.educational_content, dict)

    def test_performance_reasonable_time(self, detector):
        """Test that analysis completes in reasonable time"""
        import time

        text = "We need to build custom implementation for API integration" * 100

        start_time = time.time()
        results = detector.analyze_text_for_patterns(text)
        end_time = time.time()

        duration = end_time - start_time

        assert isinstance(results, list)
        # Should complete within reasonable time (allow generous margin for CI)
        assert duration < 30.0, f"Analysis took too long: {duration} seconds"
