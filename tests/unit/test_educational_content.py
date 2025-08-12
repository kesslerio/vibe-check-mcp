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
    DetailLevel,
    EducationalResponse
)


class TestEducationalContentGenerator:
    """Test educational content generation functionality"""

    @pytest.fixture
    def generator(self):
        """Create EducationalContentGenerator instance for testing"""
        return EducationalContentGenerator()

    @pytest.fixture
    def sample_pattern_data(self):
        """Sample pattern data for testing content generation"""
        return {
            "pattern_type": "infrastructure_without_implementation",
            "confidence": 0.8,
            "evidence": [
                "Custom HTTP client implementation detected",
                "Building REST client from scratch",
                "No SDK usage found"
            ]
        }

    def test_generator_initialization(self, generator):
        """Test that generator initializes properly"""
        assert generator is not None
        assert hasattr(generator, 'generate_educational_response')

    def test_brief_detail_level(self, generator, sample_pattern_data):
        """Test brief detail level content generation"""
        response = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.BRIEF
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.pattern_type == sample_pattern_data['pattern_type']
        assert response.confidence == sample_pattern_data['confidence']
        assert response.detail_level == DetailLevel.BRIEF
        
        # Brief content should be concise
        assert len(response.why_problematic) > 0
        assert len(response.why_problematic) < 1000  # Brief should be under 1000 chars

    def test_standard_detail_level(self, generator, sample_pattern_data):
        """Test standard detail level content generation"""
        response = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.detail_level == DetailLevel.STANDARD
        assert len(response.immediate_actions) > 0
        assert len(response.remediation_steps) > 0
        
        # Standard content should be more detailed than brief
        assert len(response.why_problematic) > 100  # Should have substantial content

    def test_comprehensive_detail_level(self, generator, sample_pattern_data):
        """Test comprehensive detail level content generation"""
        response = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.COMPREHENSIVE
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.detail_level == DetailLevel.COMPREHENSIVE
        assert len(response.learning_resources) > 0
        assert len(response.best_practices) > 0
        
        # Comprehensive should have the most detail
        assert len(response.remediation_steps) >= 3  # Multiple steps
        assert len(response.why_problematic) > 200  # Detailed explanation

    def test_documentation_neglect_pattern(self, generator):
        """Test content generation for documentation_neglect pattern"""
        response = generator.generate_educational_response(
            pattern_type="documentation_neglect",
            confidence=0.7,
            evidence=["No research phase found", "Custom solution without checking docs"],
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.pattern_type == "documentation_neglect"
        # Should emphasize documentation importance
        assert 'documentation' in response.why_problematic.lower() or 'research' in response.why_problematic.lower()

    def test_complexity_escalation_pattern(self, generator):
        """Test content generation for complexity_escalation pattern"""
        response = generator.generate_educational_response(
            pattern_type="complexity_escalation",
            confidence=0.9,
            evidence=["Unnecessary abstract factory pattern", "Over-engineering detected"],
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.pattern_type == "complexity_escalation"
        assert len(response.immediate_actions) >= 1
        assert len(response.remediation_steps) >= 1

    def test_infrastructure_pattern_high_confidence(self, generator):
        """Test content generation for high confidence infrastructure pattern"""
        response = generator.generate_educational_response(
            pattern_type="infrastructure_without_implementation",
            confidence=0.95,
            evidence=[
                "Custom HTTP implementation",
                "Building from scratch instead of using SDK",
                "Reinventing standard functionality"
            ],
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.confidence == 0.95
        assert len(response.immediate_actions) >= 1
        # Should address the high confidence pattern
        assert 'custom' in response.why_problematic.lower() or 'sdk' in response.why_problematic.lower()

    def test_content_consistency(self, generator, sample_pattern_data):
        """Test that content generation is consistent across multiple calls"""
        response1 = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.STANDARD
        )
        
        response2 = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.STANDARD
        )
        
        # Should generate consistent structure
        assert response1.pattern_type == response2.pattern_type
        assert response1.confidence == response2.confidence
        # Content should be similar (allowing for some variation)
        assert len(response1.why_problematic) > 0
        assert len(response2.why_problematic) > 0

    def test_coaching_tone(self, generator, sample_pattern_data):
        """Test that content maintains appropriate coaching tone"""
        response = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.STANDARD
        )
        
        # Check for coaching language patterns
        text_content = (response.why_problematic + ' '.join(response.immediate_actions)).lower()
        
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
        """Test that content appropriately responds to different confidence levels"""
        high_confidence_response = generator.generate_educational_response(
            pattern_type="infrastructure_without_implementation",
            confidence=0.95,
            evidence=["Critical architecture anti-pattern"],
            detail_level=DetailLevel.STANDARD
        )
        
        low_confidence_response = generator.generate_educational_response(
            pattern_type="documentation_neglect",
            confidence=0.6,
            evidence=["Minor documentation issue"],
            detail_level=DetailLevel.STANDARD
        )
        
        # High confidence should have more certain language
        high_text = high_confidence_response.why_problematic.lower()
        low_text = low_confidence_response.why_problematic.lower()
        
        # Both should have appropriate responses
        assert len(high_text) > 0
        assert len(low_text) > 0
        assert high_confidence_response.confidence == 0.95
        assert low_confidence_response.confidence == 0.6

    def test_learning_resources_inclusion(self, generator, sample_pattern_data):
        """Test inclusion of learning resources in comprehensive mode"""
        response = generator.generate_educational_response(
            pattern_type=sample_pattern_data['pattern_type'],
            confidence=sample_pattern_data['confidence'],
            evidence=sample_pattern_data['evidence'],
            detail_level=DetailLevel.COMPREHENSIVE
        )
        
        assert hasattr(response, 'learning_resources')
        assert isinstance(response.learning_resources, list)
        assert len(response.learning_resources) > 0

    def test_unknown_pattern_handling(self, generator):
        """Test handling of unknown pattern types"""
        # Test with unknown pattern type
        with pytest.raises(ValueError, match="Unknown pattern type"):
            generator.generate_educational_response(
                pattern_type="unknown_pattern_type",
                confidence=0.5,
                evidence=["Some evidence"],
                detail_level=DetailLevel.STANDARD
            )

    def test_empty_evidence_handling(self, generator):
        """Test handling of empty evidence list"""
        response = generator.generate_educational_response(
            pattern_type="documentation_neglect",
            confidence=0.5,
            evidence=[],  # Empty evidence list
            detail_level=DetailLevel.STANDARD
        )
        
        assert isinstance(response, EducationalResponse)
        assert response.pattern_type == "documentation_neglect"
        # Should provide constructive feedback even with empty evidence
        assert len(response.why_problematic) > 0