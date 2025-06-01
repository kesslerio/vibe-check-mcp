"""
Comprehensive Tests for Vibe Coaching Framework (Issue #43)

Tests the vibe coaching framework components:
- Coaching recommendation generation
- Pattern-specific coaching content
- Learning level and tone adaptations
- Real-world example formatting
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.core.vibe_coaching import (
    VibeCoachingFramework,
    LearningLevel,
    CoachingTone,
    CoachingRecommendation,
    get_vibe_coaching_framework
)
from vibe_check.core.educational_content import DetailLevel
from vibe_check.core.pattern_detector import DetectionResult


class TestVibeCoachingFramework:
    """Test comprehensive vibe coaching framework functionality"""
    
    @pytest.fixture
    def coaching_framework(self):
        """Create coaching framework instance for testing"""
        return VibeCoachingFramework()
    
    @pytest.fixture
    def sample_detection_results(self):
        """Sample pattern detection results for testing"""
        return [
            DetectionResult(
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.85,
                evidence=["custom HTTP server", "instead of SDK"],
                threshold=0.6,
                educational_content=""
            ),
            DetectionResult(
                pattern_type="symptom_driven_development",
                detected=True,
                confidence=0.75,
                evidence=["fixing symptoms", "not root cause"],
                threshold=0.6,
                educational_content=""
            ),
            DetectionResult(
                pattern_type="over_engineering",
                detected=False,
                confidence=0.3,
                evidence=[],
                threshold=0.6,
                educational_content=""
            )
        ]
    
    @pytest.fixture
    def sample_issue_context(self):
        """Sample issue context for testing"""
        return {
            "vibe_level": "bad_vibes",
            "pattern_count": 2,
            "has_claude_analysis": True,
            "has_clear_thought": False
        }
    
    def test_framework_initialization(self, coaching_framework):
        """Test proper coaching framework initialization"""
        assert coaching_framework is not None
        assert coaching_framework.coaching_patterns is not None
        assert isinstance(coaching_framework.coaching_patterns, dict)
    
    def test_generate_coaching_recommendations_good_vibes(self, coaching_framework, sample_issue_context):
        """Test coaching recommendations for good vibes"""
        sample_issue_context["vibe_level"] = "good_vibes"
        
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="good_vibes",
            detected_patterns=[],
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Check for good vibes specific content
        vibe_recommendation = next((r for r in recommendations if "Ready to Roll" in r.title), None)
        assert vibe_recommendation is not None
        assert "great vibes" in vibe_recommendation.description.lower() or "solid and well-thought-out" in vibe_recommendation.description.lower()
        assert len(vibe_recommendation.action_items) > 0
        assert len(vibe_recommendation.learning_resources) > 0
        assert len(vibe_recommendation.prevention_checklist) > 0
    
    def test_generate_coaching_recommendations_needs_research(self, coaching_framework, sample_issue_context):
        """Test coaching recommendations for needs research"""
        sample_issue_context["vibe_level"] = "needs_research"
        
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="needs_research",
            detected_patterns=[],
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.BEGINNER,
            tone=CoachingTone.SUPPORTIVE
        )
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Check for research specific content
        research_recommendation = next((r for r in recommendations if "Homework" in r.title), None)
        assert research_recommendation is not None
        assert "research" in research_recommendation.description.lower()
        assert "documentation" in " ".join(research_recommendation.action_items).lower()
        assert research_recommendation.real_world_example is not None
        assert "authentication" in research_recommendation.real_world_example.lower()
    
    def test_generate_coaching_recommendations_needs_poc(self, coaching_framework, sample_issue_context):
        """Test coaching recommendations for needs POC"""
        sample_issue_context["vibe_level"] = "needs_poc"
        
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="needs_poc",
            detected_patterns=[],
            issue_context=sample_issue_context,
            detail_level=DetailLevel.COMPREHENSIVE,
            learning_level=LearningLevel.ADVANCED,
            tone=CoachingTone.DIRECT
        )
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Check for POC specific content
        poc_recommendation = next((r for r in recommendations if "Magic" in r.title), None)
        assert poc_recommendation is not None
        assert "proof-of-concept" in poc_recommendation.description.lower() or "core functionality works" in poc_recommendation.description.lower()
        assert "real data" in " ".join(poc_recommendation.action_items).lower()
        assert poc_recommendation.real_world_example is not None
        assert poc_recommendation.common_mistakes is not None
        assert len(poc_recommendation.common_mistakes) > 0
    
    def test_generate_coaching_recommendations_complex_vibes(self, coaching_framework, sample_issue_context):
        """Test coaching recommendations for complex vibes"""
        sample_issue_context["vibe_level"] = "complex_vibes"
        
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="complex_vibes",
            detected_patterns=[],
            issue_context=sample_issue_context,
            detail_level=DetailLevel.BRIEF,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Check for complexity specific content
        complexity_recommendation = next((r for r in recommendations if "Simplify" in r.title), None)
        assert complexity_recommendation is not None
        assert "simpler" in complexity_recommendation.description.lower()
        assert "complexity" in " ".join(complexity_recommendation.action_items).lower()
        assert complexity_recommendation.real_world_example is not None
        assert "microservices" in complexity_recommendation.real_world_example.lower()
    
    def test_generate_coaching_recommendations_bad_vibes(self, coaching_framework, sample_issue_context):
        """Test coaching recommendations for bad vibes"""
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="bad_vibes",
            detected_patterns=[],
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.BEGINNER,
            tone=CoachingTone.SUPPORTIVE
        )
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Check for bad vibes specific content
        reset_recommendation = next((r for r in recommendations if "Reset" in r.title), None)
        assert reset_recommendation is not None
        assert "infrastructure" in reset_recommendation.description.lower()
        assert "STOP" in " ".join(reset_recommendation.action_items)
        assert reset_recommendation.real_world_example is not None
        assert "Cognee" in reset_recommendation.real_world_example
        assert reset_recommendation.common_mistakes is not None
    
    def test_generate_pattern_specific_coaching(self, coaching_framework, sample_detection_results, sample_issue_context):
        """Test pattern-specific coaching generation"""
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="bad_vibes",
            detected_patterns=sample_detection_results,
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should include pattern-specific recommendations
        pattern_titles = [r.title for r in recommendations]
        
        # Check for infrastructure pattern coaching
        infrastructure_coaching = next((r for r in recommendations if "Foundation" in r.title), None)
        assert infrastructure_coaching is not None
        assert "infrastructure" in infrastructure_coaching.description.lower()
        assert "basic functionality" in infrastructure_coaching.description.lower()
        
        # Check for symptom-driven development coaching
        symptom_coaching = next((r for r in recommendations if "Root Cause" in r.title), None)
        assert symptom_coaching is not None
        assert "root cause" in symptom_coaching.description.lower()
        assert "why" in " ".join(symptom_coaching.action_items).lower()
    
    def test_pattern_coaching_confidence_threshold(self, coaching_framework, sample_issue_context):
        """Test that only high-confidence patterns generate coaching"""
        low_confidence_patterns = [
            DetectionResult(
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.5,  # Below threshold
                evidence=["weak evidence"],
                threshold=0.6,
                educational_content=""
            )
        ]
        
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="good_vibes",
            detected_patterns=low_confidence_patterns,
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should not include low-confidence pattern coaching
        pattern_titles = [r.title for r in recommendations]
        assert not any("Foundation" in title for title in pattern_titles)
    
    def test_general_learning_recommendations(self, coaching_framework, sample_detection_results, sample_issue_context):
        """Test general learning recommendation generation"""
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="good_vibes",
            detected_patterns=sample_detection_results,
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should include learning opportunity recommendations
        learning_recommendation = next((r for r in recommendations if "Learning Opportunity" in r.title), None)
        assert learning_recommendation is not None
        assert "learning" in learning_recommendation.description.lower()
        assert "document" in " ".join(learning_recommendation.action_items).lower()
        
        # Should include collaboration recommendations
        collaboration_recommendation = next((r for r in recommendations if "Collaboration" in r.title), None)
        assert collaboration_recommendation is not None
        assert "feedback" in collaboration_recommendation.description.lower()
        assert "pair" in " ".join(collaboration_recommendation.action_items).lower()
    
    def test_coaching_tone_adaptations(self, coaching_framework, sample_issue_context):
        """Test coaching tone adaptations"""
        base_recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="needs_research",
            detected_patterns=[],
            issue_context=sample_issue_context,
            tone=CoachingTone.ENCOURAGING
        )
        
        direct_recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="needs_research",
            detected_patterns=[],
            issue_context=sample_issue_context,
            tone=CoachingTone.DIRECT
        )
        
        supportive_recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="needs_research",
            detected_patterns=[],
            issue_context=sample_issue_context,
            tone=CoachingTone.SUPPORTIVE
        )
        
        # Should have same number of recommendations
        assert len(base_recommendations) == len(direct_recommendations) == len(supportive_recommendations)
        
        # Descriptions should be different based on tone
        base_desc = base_recommendations[0].description
        direct_desc = direct_recommendations[0].description
        supportive_desc = supportive_recommendations[0].description
        
        # Direct should be more assertive
        assert "You should" in direct_desc or "Do" in direct_desc
        
        # Supportive should be more empathetic
        assert "I understand" in supportive_desc or "Together" in supportive_desc
    
    def test_make_more_direct(self, coaching_framework):
        """Test direct tone text transformation"""
        original_text = "This might be causing issues. Consider looking into it. Let's try a different approach."
        
        direct_text = coaching_framework._make_more_direct(original_text)
        
        # Should replace softening language
        assert "might be" not in direct_text
        assert "Consider" not in direct_text
        assert "Let's" not in direct_text
        assert "is" in direct_text
        assert "Do" in direct_text
        assert "You should" in direct_text
    
    def test_make_more_supportive(self, coaching_framework):
        """Test supportive tone text transformation"""
        original_text = "This is causing problems. Let's fix this issue."
        
        supportive_text = coaching_framework._make_more_supportive(original_text)
        
        # Should add supportive language
        assert "I understand" in supportive_text
        assert "Together" in supportive_text
        assert "I see that" in supportive_text
    
    def test_load_coaching_patterns(self, coaching_framework):
        """Test coaching patterns loading"""
        patterns = coaching_framework._load_coaching_patterns()
        
        # Should contain expected pattern types
        assert "encouragement_phrases" in patterns
        assert "learning_focus_areas" in patterns
        
        # Should have appropriate content
        assert isinstance(patterns["encouragement_phrases"], list)
        assert len(patterns["encouragement_phrases"]) > 0
        assert isinstance(patterns["learning_focus_areas"], list)
        assert len(patterns["learning_focus_areas"]) > 0
        
        # Check for specific encouraging phrases
        encouragements = patterns["encouragement_phrases"]
        assert any("Great" in phrase for phrase in encouragements)
        assert any("question" in phrase for phrase in encouragements)
    
    def test_invalid_vibe_level_handling(self, coaching_framework, sample_issue_context):
        """Test handling of invalid vibe levels"""
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="invalid_vibe_level",
            detected_patterns=[],
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should still return general recommendations (learning and collaboration)
        assert len(recommendations) >= 2
        
        # Should include general learning recommendations
        titles = [r.title for r in recommendations]
        assert any("Learning" in title for title in titles)
        assert any("Collaboration" in title for title in titles)
    
    def test_invalid_pattern_type_handling(self, coaching_framework, sample_issue_context):
        """Test handling of unknown pattern types"""
        unknown_patterns = [
            DetectionResult(
                pattern_type="unknown_pattern_type",
                detected=True,
                confidence=0.8,
                evidence=["some evidence"],
                threshold=0.6,
                educational_content=""
            )
        ]
        
        recommendations = coaching_framework.generate_coaching_recommendations(
            vibe_level="good_vibes",
            detected_patterns=unknown_patterns,
            issue_context=sample_issue_context,
            detail_level=DetailLevel.STANDARD,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should not crash and should still provide general recommendations
        assert len(recommendations) > 0
        
        # Should not include unknown pattern coaching
        pattern_titles = [r.title for r in recommendations]
        assert not any("unknown" in title.lower() for title in pattern_titles)


class TestCoachingRecommendation:
    """Test CoachingRecommendation dataclass functionality"""
    
    def test_coaching_recommendation_creation(self):
        """Test CoachingRecommendation creation with all fields"""
        recommendation = CoachingRecommendation(
            title="Test Coaching",
            description="Test description",
            action_items=["Action 1", "Action 2"],
            learning_resources=["Resource 1", "Resource 2"],
            prevention_checklist=["Check 1", "Check 2"],
            real_world_example="Example text",
            common_mistakes=["Mistake 1", "Mistake 2"]
        )
        
        assert recommendation.title == "Test Coaching"
        assert recommendation.description == "Test description"
        assert len(recommendation.action_items) == 2
        assert len(recommendation.learning_resources) == 2
        assert len(recommendation.prevention_checklist) == 2
        assert recommendation.real_world_example == "Example text"
        assert len(recommendation.common_mistakes) == 2
    
    def test_coaching_recommendation_optional_fields(self):
        """Test CoachingRecommendation with optional fields as None"""
        recommendation = CoachingRecommendation(
            title="Test Coaching",
            description="Test description",
            action_items=["Action 1"],
            learning_resources=["Resource 1"],
            prevention_checklist=["Check 1"]
        )
        
        assert recommendation.real_world_example is None
        assert recommendation.common_mistakes is None


class TestVibeCoachingEnums:
    """Test vibe coaching enum classes"""
    
    def test_learning_level_enum(self):
        """Test LearningLevel enum values"""
        assert LearningLevel.BEGINNER.value == "beginner"
        assert LearningLevel.INTERMEDIATE.value == "intermediate"
        assert LearningLevel.ADVANCED.value == "advanced"
        
        # Test all values are accessible
        levels = list(LearningLevel)
        assert len(levels) == 3
    
    def test_coaching_tone_enum(self):
        """Test CoachingTone enum values"""
        assert CoachingTone.ENCOURAGING.value == "encouraging"
        assert CoachingTone.DIRECT.value == "direct"
        assert CoachingTone.SUPPORTIVE.value == "supportive"
        
        # Test all values are accessible
        tones = list(CoachingTone)
        assert len(tones) == 3


class TestVibeCoachingGlobalFramework:
    """Test global coaching framework instance management"""
    
    def test_get_vibe_coaching_framework_singleton(self):
        """Test global coaching framework instance is singleton"""
        framework1 = get_vibe_coaching_framework()
        framework2 = get_vibe_coaching_framework()
        
        # Should return same instance
        assert framework1 is framework2
        assert isinstance(framework1, VibeCoachingFramework)
    
    def test_get_vibe_coaching_framework_instance_type(self):
        """Test global framework instance type"""
        framework = get_vibe_coaching_framework()
        
        assert isinstance(framework, VibeCoachingFramework)
        assert hasattr(framework, 'generate_coaching_recommendations')
        assert hasattr(framework, 'coaching_patterns')


class TestVibeCoachingIntegration:
    """Integration tests for vibe coaching functionality"""
    
    @pytest.mark.integration
    def test_comprehensive_coaching_workflow(self):
        """Test complete coaching recommendation workflow"""
        framework = VibeCoachingFramework()
        
        # Create comprehensive test scenario
        complex_patterns = [
            DetectionResult(
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.9,
                evidence=["custom server", "skip SDK"],
                threshold=0.6,
                educational_content=""
            ),
            DetectionResult(
                pattern_type="symptom_driven_development",
                detected=True,
                confidence=0.8,
                evidence=["symptom fix", "no root cause"],
                threshold=0.6,
                educational_content=""
            ),
            DetectionResult(
                pattern_type="over_engineering",
                detected=True,
                confidence=0.7,
                evidence=["complex architecture", "simple problem"],
                threshold=0.6,
                educational_content=""
            )
        ]
        
        issue_context = {
            "vibe_level": "bad_vibes",
            "pattern_count": 3,
            "has_claude_analysis": True,
            "has_clear_thought": True
        }
        
        recommendations = framework.generate_coaching_recommendations(
            vibe_level="bad_vibes",
            detected_patterns=complex_patterns,
            issue_context=issue_context,
            detail_level=DetailLevel.COMPREHENSIVE,
            learning_level=LearningLevel.INTERMEDIATE,
            tone=CoachingTone.ENCOURAGING
        )
        
        # Should generate comprehensive recommendations
        assert len(recommendations) >= 5  # Vibe + 3 patterns + general recommendations
        
        # Verify specific coaching types are included
        titles = [r.title for r in recommendations]
        assert any("Reset" in title for title in titles)  # Bad vibes coaching
        assert any("Foundation" in title for title in titles)  # Infrastructure coaching
        assert any("Root Cause" in title for title in titles)  # Symptom-driven coaching
        assert any("Simplicity" in title for title in titles)  # Over-engineering coaching
        assert any("Learning" in title for title in titles)  # General learning
        assert any("Collaboration" in title for title in titles)  # General collaboration
        
        # Verify each recommendation has required structure
        for recommendation in recommendations:
            assert isinstance(recommendation, CoachingRecommendation)
            assert len(recommendation.title) > 0
            assert len(recommendation.description) > 0
            assert len(recommendation.action_items) > 0
            assert len(recommendation.learning_resources) > 0
            assert len(recommendation.prevention_checklist) > 0
    
    @pytest.mark.integration
    def test_coaching_adaptation_across_learning_levels(self):
        """Test coaching adaptation for different learning levels"""
        framework = VibeCoachingFramework()
        
        pattern = DetectionResult(
            pattern_type="infrastructure_without_implementation",
            detected=True,
            confidence=0.8,
            evidence=["custom implementation"],
            threshold=0.6,
            educational_content=""
        )
        
        issue_context = {"vibe_level": "bad_vibes", "pattern_count": 1}
        
        # Test recommendations for each learning level
        for learning_level in LearningLevel:
            recommendations = framework.generate_coaching_recommendations(
                vibe_level="bad_vibes",
                detected_patterns=[pattern],
                issue_context=issue_context,
                detail_level=DetailLevel.STANDARD,
                learning_level=learning_level,
                tone=CoachingTone.ENCOURAGING
            )
            
            # Should generate recommendations for all levels
            assert len(recommendations) > 0
            
            # Should maintain consistent recommendation structure
            for recommendation in recommendations:
                assert isinstance(recommendation, CoachingRecommendation)
                assert len(recommendation.action_items) > 0
                assert len(recommendation.learning_resources) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])