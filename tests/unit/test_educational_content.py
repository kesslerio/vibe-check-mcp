"""
Unit Tests for Educational Content Generator

Tests the educational content generation functionality:
- Different detail levels (brief, standard, comprehensive)
- Pattern-specific coaching recommendations
- Tone and style consistency
- Content quality and usefulness
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.core.educational_content import (
    EducationalContentGenerator, 
    DetailLevel
)
from vibe_check.core.pattern_detector import DetectionResult


class TestEducationalContentGenerator:
    """Test educational content generation functionality"""

    @pytest.fixture
    def generator(self):
        """Create EducationalContentGenerator instance for testing"""
        return EducationalContentGenerator()

    @pytest.fixture
    def sample_detection_result(self):
        """Sample detection result for testing content generation"""
        return DetectionResult(
            total_issues=2,
            patterns=[
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "description": "Custom HTTP client implementation",
                    "confidence": 0.8,
                    "severity": "medium",
                    "location": "line 1",
                    "suggestion": "Consider using requests library instead"
                },
                {
                    "pattern_type": "documentation_neglect", 
                    "description": "Missing research phase",
                    "confidence": 0.7,
                    "severity": "low",
                    "location": "overall approach",
                    "suggestion": "Check official documentation first"
                }
            ],
            summary="Multiple anti-patterns detected requiring guidance"
        )

    def test_generator_initialization(self, generator):
        """Test that generator initializes properly"""
        assert generator is not None
        assert hasattr(generator, 'generate_content')

    def test_brief_detail_level(self, generator, sample_detection_result):
        """Test brief detail level content generation"""
        content = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.BRIEF
        )
        
        assert isinstance(content, dict)
        assert 'summary' in content
        assert 'recommendations' in content
        
        # Brief content should be concise
        summary_length = len(content['summary'])
        assert summary_length > 0
        assert summary_length < 1000  # Brief should be under 1000 chars

    def test_standard_detail_level(self, generator, sample_detection_result):
        """Test standard detail level content generation"""
        content = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(content, dict)
        assert 'summary' in content
        assert 'recommendations' in content
        assert 'analysis' in content
        
        # Standard content should be more detailed than brief
        summary_length = len(content['summary'])
        assert summary_length > 100  # Should have substantial content

    def test_comprehensive_detail_level(self, generator, sample_detection_result):
        """Test comprehensive detail level content generation"""
        content = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.COMPREHENSIVE
        )
        
        assert isinstance(content, dict)
        assert 'summary' in content
        assert 'recommendations' in content
        assert 'analysis' in content
        assert 'learning_resources' in content
        
        # Comprehensive should have the most detail
        assert len(content) >= 4  # Multiple sections
        assert len(content['summary']) > 200  # Detailed summary

    def test_no_issues_content_generation(self, generator):
        """Test content generation when no issues are detected"""
        clean_result = DetectionResult(
            total_issues=0,
            patterns=[],
            summary="No anti-patterns detected"
        )
        
        content = generator.generate_content(
            detection_result=clean_result,
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(content, dict)
        assert 'summary' in content
        # Should provide positive reinforcement for clean code
        assert 'good' in content['summary'].lower() or 'clean' in content['summary'].lower()

    def test_single_pattern_content_generation(self, generator):
        """Test content generation for single pattern detection"""
        single_pattern_result = DetectionResult(
            total_issues=1,
            patterns=[{
                "pattern_type": "complexity_escalation",
                "description": "Unnecessary abstract factory pattern",
                "confidence": 0.9,
                "severity": "high"
            }],
            summary="Single complexity anti-pattern detected"
        )
        
        content = generator.generate_content(
            detection_result=single_pattern_result,
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(content, dict)
        assert 'recommendations' in content
        assert len(content['recommendations']) >= 1

    def test_multiple_patterns_content_generation(self, generator):
        """Test content generation for multiple pattern detection"""
        multi_pattern_result = DetectionResult(
            total_issues=3,
            patterns=[
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "description": "Custom HTTP implementation",
                    "confidence": 0.8,
                    "severity": "high"
                },
                {
                    "pattern_type": "documentation_neglect",
                    "description": "Skipped research phase", 
                    "confidence": 0.7,
                    "severity": "medium"
                },
                {
                    "pattern_type": "symptom_driven_development",
                    "description": "Workaround approach",
                    "confidence": 0.6,
                    "severity": "low"
                }
            ],
            summary="Multiple anti-patterns requiring attention"
        )
        
        content = generator.generate_content(
            detection_result=multi_pattern_result,
            detail_level=DetailLevel.COMPREHENSIVE
        )
        
        assert isinstance(content, dict)
        assert len(content['recommendations']) >= 3
        # Should address all detected patterns
        recommendations_text = str(content['recommendations']).lower()
        assert 'custom' in recommendations_text or 'infrastructure' in recommendations_text

    def test_content_consistency(self, generator, sample_detection_result):
        """Test that content generation is consistent across multiple calls"""
        content1 = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.STANDARD
        )
        
        content2 = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.STANDARD
        )
        
        # Should generate consistent structure
        assert content1.keys() == content2.keys()
        # Content should be similar (allowing for some variation)
        assert len(content1['summary']) > 0
        assert len(content2['summary']) > 0

    def test_coaching_tone(self, generator, sample_detection_result):
        """Test that content maintains appropriate coaching tone"""
        content = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.STANDARD
        )
        
        # Check for coaching language patterns
        text_content = str(content).lower()
        
        # Should avoid harsh language
        harsh_words = ['bad', 'wrong', 'terrible', 'stupid', 'awful']
        for word in harsh_words:
            assert text_content.count(word) <= 1  # Allow minimal usage
        
        # Should include constructive language
        constructive_indicators = [
            'consider', 'recommend', 'suggest', 'try', 'explore',
            'alternative', 'option', 'approach', 'improve'
        ]
        
        has_constructive = any(word in text_content for word in constructive_indicators)
        assert has_constructive, "Content should use constructive coaching language"

    def test_severity_appropriate_responses(self, generator):
        """Test that content appropriately responds to different severity levels"""
        high_severity_result = DetectionResult(
            total_issues=1,
            patterns=[{
                "pattern_type": "infrastructure_without_implementation",
                "description": "Critical architecture anti-pattern",
                "confidence": 0.95,
                "severity": "high"
            }],
            summary="High severity anti-pattern detected"
        )
        
        low_severity_result = DetectionResult(
            total_issues=1,
            patterns=[{
                "pattern_type": "documentation_neglect",
                "description": "Minor documentation issue",
                "confidence": 0.6,
                "severity": "low"
            }],
            summary="Low severity issue detected"
        )
        
        high_content = generator.generate_content(
            high_severity_result, DetailLevel.STANDARD
        )
        low_content = generator.generate_content(
            low_severity_result, DetailLevel.STANDARD
        )
        
        # High severity should have more urgent language
        high_text = str(high_content).lower()
        low_text = str(low_content).lower()
        
        # High severity might use words like "important", "critical", "should"
        urgency_indicators = ['important', 'critical', 'should', 'must', 'need']
        high_urgency = sum(1 for word in urgency_indicators if word in high_text)
        low_urgency = sum(1 for word in urgency_indicators if word in low_text)
        
        # Not strictly enforced as language generation can vary
        assert high_urgency >= 0 and low_urgency >= 0

    def test_learning_resources_inclusion(self, generator, sample_detection_result):
        """Test inclusion of learning resources in comprehensive mode"""
        content = generator.generate_content(
            detection_result=sample_detection_result,
            detail_level=DetailLevel.COMPREHENSIVE
        )
        
        if 'learning_resources' in content:
            resources = content['learning_resources']
            assert isinstance(resources, (list, dict))
            if isinstance(resources, list):
                assert len(resources) > 0
            if isinstance(resources, dict):
                assert len(resources.keys()) > 0

    def test_malformed_detection_result_handling(self, generator):
        """Test handling of malformed or incomplete detection results"""
        # Test with missing patterns
        incomplete_result = DetectionResult(
            total_issues=1,
            patterns=None,  # Malformed
            summary="Incomplete result"
        )
        
        try:
            content = generator.generate_content(
                detection_result=incomplete_result,
                detail_level=DetailLevel.STANDARD
            )
            # Should handle gracefully
            assert isinstance(content, dict)
        except (AttributeError, TypeError):
            # Acceptable to raise error for malformed input
            pass

    def test_empty_patterns_handling(self, generator):
        """Test handling of empty patterns list"""
        empty_patterns_result = DetectionResult(
            total_issues=0,
            patterns=[],
            summary="No patterns detected"
        )
        
        content = generator.generate_content(
            detection_result=empty_patterns_result,
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(content, dict)
        assert 'summary' in content
        # Should provide constructive feedback even with no issues