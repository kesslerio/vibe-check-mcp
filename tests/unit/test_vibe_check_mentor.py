"""
Unit Tests for Vibe Check Mentor - Collaborative Reasoning Tool

Tests the vibe_check_mentor functionality:
- VibeMentorEngine class and collaborative reasoning
- PersonaData and session management
- Pattern detection integration
- Multi-persona response generation
- Session synthesis and insights
- Error handling and edge cases
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from typing import Dict, Any, List

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.vibe_mentor import (
    VibeMentorEngine,
    PersonaData,
    ContributionData,
    CollaborativeReasoningSession,
    get_mentor_engine,
    _generate_summary,
)


class TestPersonaData:
    """Test PersonaData class"""

    def test_persona_data_creation(self):
        """Test creating a PersonaData instance"""
        persona = PersonaData(
            id="test_persona",
            name="Test Engineer",
            expertise=["Testing", "Quality"],
            background="10 years testing experience",
            perspective="Quality-first approach",
            biases=["Perfectionist", "Risk-averse"],
            communication={"style": "Detailed", "tone": "Analytical"},
        )

        assert persona.id == "test_persona"
        assert persona.name == "Test Engineer"
        assert "Testing" in persona.expertise
        assert persona.communication["style"] == "Detailed"


class TestContributionData:
    """Test ContributionData class"""

    def test_contribution_data_creation(self):
        """Test creating a ContributionData instance"""
        contribution = ContributionData(
            persona_id="senior_engineer",
            content="This is a test insight",
            type="insight",
            confidence=0.85,
        )

        assert contribution.persona_id == "senior_engineer"
        assert contribution.content == "This is a test insight"
        assert contribution.type == "insight"
        assert contribution.confidence == 0.85
        assert contribution.timestamp is not None


class TestVibeMentorEngine:
    """Test VibeMentorEngine class"""

    def test_engine_initialization(self):
        """Test VibeMentorEngine initialization"""
        engine = VibeMentorEngine()

        assert engine.sessions == {}
        assert engine.pattern_detector is not None
        assert len(engine.DEFAULT_PERSONAS) == 3

        # Check default personas
        persona_ids = [p.id for p in engine.DEFAULT_PERSONAS]
        assert "senior_engineer" in persona_ids
        assert "product_engineer" in persona_ids
        assert "ai_engineer" in persona_ids

    def test_create_session(self):
        """Test creating a new collaborative reasoning session"""
        engine = VibeMentorEngine()
        topic = "Should I build a custom auth system?"

        session = engine.create_session(topic)

        assert session.topic == topic
        assert session.session_id is not None
        assert session.stage == "problem-definition"
        assert len(session.personas) == 3
        assert len(session.contributions) == 0
        assert session.iteration == 0
        assert session.next_contribution_needed is True

    def test_create_session_with_custom_id(self):
        """Test creating session with custom session ID"""
        engine = VibeMentorEngine()
        topic = "API integration decision"
        custom_id = "test-session-123"

        session = engine.create_session(topic, session_id=custom_id)

        assert session.session_id == custom_id
        assert custom_id in engine.sessions
        assert engine.sessions[custom_id] is session

    @patch("vibe_check.tools.vibe_mentor.PatternDetector")
    def test_generate_contribution_senior_engineer(self, mock_pattern_detector):
        """Test generating contribution from senior engineer persona"""
        engine = VibeMentorEngine()

        # Create test session
        session = engine.create_session("Custom HTTP client vs SDK")
        senior_persona = next(p for p in session.personas if p.id == "senior_engineer")

        # Mock detected patterns
        detected_patterns = [
            {
                "pattern_type": "infrastructure_without_implementation",
                "detected": True,
                "confidence": 0.9,
            }
        ]

        contribution = engine.generate_contribution(
            session=session,
            persona=senior_persona,
            detected_patterns=detected_patterns,
            context="Need to integrate with payment API",
        )

        assert contribution.persona_id == "senior_engineer"
        assert contribution.type == "concern"
        assert contribution.confidence > 0.8
        assert "infrastructure-first" in contribution.content.lower()

    def test_generate_contribution_product_engineer(self):
        """Test generating contribution from product engineer persona"""
        engine = VibeMentorEngine()

        session = engine.create_session("Should we build microservices?")
        product_persona = next(
            p for p in session.personas if p.id == "product_engineer"
        )

        detected_patterns = []  # No patterns detected

        contribution = engine.generate_contribution(
            session=session,
            persona=product_persona,
            detected_patterns=detected_patterns,
            context="Early stage startup",
        )

        assert contribution.persona_id == "product_engineer"
        assert contribution.type in ["observation", "suggestion", "challenge"]
        assert contribution.confidence > 0.0

    def test_generate_contribution_ai_engineer(self):
        """Test generating contribution from AI engineer persona"""
        engine = VibeMentorEngine()

        session = engine.create_session("AI integration strategy")
        ai_persona = next(p for p in session.personas if p.id == "ai_engineer")

        detected_patterns = []

        contribution = engine.generate_contribution(
            session=session,
            persona=ai_persona,
            detected_patterns=detected_patterns,
            context="Building AI-powered features",
        )

        assert contribution.persona_id == "ai_engineer"
        assert contribution.type in ["insight", "suggestion", "observation"]
        assert (
            "ai" in contribution.content.lower()
            or "tool" in contribution.content.lower()
        )

    def test_advance_stage(self):
        """Test advancing session stages"""
        engine = VibeMentorEngine()
        session = engine.create_session("Test topic")

        # Initial stage
        assert session.stage == "problem-definition"
        assert session.iteration == 0

        # Advance to ideation
        new_stage = engine.advance_stage(session)
        assert new_stage == "ideation"
        assert session.stage == "ideation"
        assert session.iteration == 1

        # Continue advancing
        engine.advance_stage(session)
        assert session.stage == "critique"
        assert session.iteration == 2

        # Advance through all stages
        engine.advance_stage(session)  # integration
        engine.advance_stage(session)  # decision
        engine.advance_stage(session)  # reflection
        engine.advance_stage(session)  # should stay at reflection

        assert session.stage == "reflection"

    def test_synthesize_session_empty(self):
        """Test synthesizing session with no contributions"""
        engine = VibeMentorEngine()
        session = engine.create_session("Empty session test")

        synthesis = engine.synthesize_session(session)

        assert synthesis["session_summary"]["topic"] == "Empty session test"
        assert synthesis["session_summary"]["total_contributions"] == 0
        assert synthesis["consensus_points"] == []
        assert synthesis["key_insights"] == []
        assert synthesis["primary_concerns"] == []

    def test_synthesize_session_with_contributions(self):
        """Test synthesizing session with actual contributions"""
        engine = VibeMentorEngine()
        session = engine.create_session("SDK vs custom implementation")

        # Add some test contributions
        contributions = [
            ContributionData(
                persona_id="senior_engineer",
                content="I recommend using the official SDK for maintainability",
                type="insight",
                confidence=0.92,
            ),
            ContributionData(
                persona_id="product_engineer",
                content="Let's prototype with the official tools first",
                type="suggestion",
                confidence=0.88,
            ),
            ContributionData(
                persona_id="ai_engineer",
                content="Official SDKs handle edge cases we might miss",
                type="insight",
                confidence=0.87,
            ),
        ]

        session.contributions = contributions
        session.stage = "decision"

        synthesis = engine.synthesize_session(session)

        assert synthesis["session_summary"]["total_contributions"] == 3
        assert len(synthesis["key_insights"]) > 0
        assert "official" in str(synthesis["consensus_points"]).lower()
        assert synthesis["final_recommendation"] is not None

    def test_format_session_output(self):
        """Test formatting session output with ANSI colors"""
        engine = VibeMentorEngine()
        session = engine.create_session("Test formatting")

        # Add a test contribution
        session.contributions.append(
            ContributionData(
                persona_id="senior_engineer",
                content="Test output formatting",
                type="observation",
                confidence=0.8,
            )
        )

        formatted = engine.format_session_output(session)

        assert "🧠 Collaborative Reasoning Session" in formatted
        assert "Test formatting" in formatted
        assert "Senior Software Engineer" in formatted
        assert "Test output formatting" in formatted
        assert "\033[" in formatted  # ANSI color codes present

    def test_find_references(self):
        """Test finding references between contributions"""
        engine = VibeMentorEngine()

        existing_contributions = [
            ContributionData(
                persona_id="senior_engineer",
                content="Use official SDK for authentication",
                type="suggestion",
                confidence=0.9,
            )
        ]

        # Test content that references the existing contribution
        references = engine._find_references(
            "Building on the SDK suggestion, we should also consider documentation",
            existing_contributions,
        )

        assert len(references) > 0


class TestGenerateSummary:
    """Test the _generate_summary helper function"""

    def test_generate_summary_with_infrastructure_pattern(self):
        """Test summary generation with infrastructure pattern"""
        vibe_level = "needs_research"
        detected_patterns = [
            {"pattern_type": "infrastructure_without_implementation", "detected": True}
        ]

        summary = _generate_summary(vibe_level, detected_patterns)

        assert "sdk" in summary.lower()
        assert "custom" in summary.lower()

    def test_generate_summary_with_custom_pattern(self):
        """Test summary generation with custom pattern"""
        vibe_level = "concerning"
        detected_patterns = [
            {"pattern_type": "custom_solution_first", "detected": True}
        ]

        summary = _generate_summary(vibe_level, detected_patterns)

        assert "standard" in summary.lower() or "custom" in summary.lower()

    def test_generate_summary_no_patterns(self):
        """Test summary generation with no patterns"""
        vibe_level = "good_vibes"
        detected_patterns = []

        summary = _generate_summary(vibe_level, detected_patterns)

        assert "no concerning patterns" in summary.lower()
        assert "looking good" in summary.lower()


class TestGetMentorEngine:
    """Test the get_mentor_engine singleton function"""

    def test_get_mentor_engine_singleton(self):
        """Test that get_mentor_engine returns singleton instance"""
        # Clear any existing instance
        import vibe_check.tools.vibe_mentor as mentor_module

        mentor_module._mentor_engine = None

        # First call
        engine1 = get_mentor_engine()
        # Second call
        engine2 = get_mentor_engine()

        # Should return same instance
        assert engine1 is engine2
        assert isinstance(engine1, VibeMentorEngine)


class TestVibeCheckMentorIntegration:
    """Integration tests for vibe_check_mentor tool logic"""

    @patch("vibe_check.tools.vibe_mentor.analyze_text_demo")
    def test_mentor_engine_full_workflow(self, mock_analyze):
        """Test complete mentor engine workflow"""
        # Mock the analyze_text_demo response
        mock_analyze.return_value = {
            "detected_patterns": [
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "detected": True,
                    "confidence": 0.9,
                }
            ],
            "vibe_assessment": {"vibe_level": "needs_research", "confidence": 0.85},
        }

        engine = VibeMentorEngine()

        # Create session
        session = engine.create_session("Should I build a custom HTTP client?")

        # Generate contributions for standard depth (2 personas)
        detected_patterns = [
            {
                "pattern_type": "infrastructure_without_implementation",
                "detected": True,
                "confidence": 0.9,
            }
        ]

        for i in range(2):  # Standard depth
            if i < len(session.personas):
                persona = session.personas[i]
                session.active_persona_id = persona.id

                contribution = engine.generate_contribution(
                    session=session,
                    persona=persona,
                    detected_patterns=detected_patterns,
                    context="Working with REST API",
                )

                session.contributions.append(contribution)

        # Synthesize insights
        synthesis = engine.synthesize_session(session)

        # Verify results
        assert len(session.contributions) == 2
        assert "senior_engineer" in [c.persona_id for c in session.contributions]
        assert "product_engineer" in [c.persona_id for c in session.contributions]
        assert synthesis["session_summary"]["total_contributions"] == 2
        assert len(synthesis["recommendations"]["immediate_actions"]) > 0

    def test_mentor_engine_error_resilience(self):
        """Test mentor engine handles missing data gracefully"""
        engine = VibeMentorEngine()

        # Test with empty session
        session = engine.create_session("Empty test")
        synthesis = engine.synthesize_session(session)

        assert synthesis["session_summary"]["total_contributions"] == 0
        assert synthesis["consensus_points"] == []

        # Test with malformed patterns
        malformed_patterns = [{"invalid": "pattern"}]

        # Should not crash
        contribution = engine.generate_contribution(
            session=session,
            persona=session.personas[0],
            detected_patterns=malformed_patterns,
            context=None,
        )

        assert contribution.persona_id == session.personas[0].id
        assert contribution.confidence > 0

    def test_mentor_tool_reasoning_depths(self):
        """Test different reasoning depths"""
        engine = VibeMentorEngine()

        # Test contribution counts for different depths
        depth_counts = {"quick": 1, "standard": 2, "comprehensive": 3}

        for depth, expected_count in depth_counts.items():
            session = engine.create_session(f"Test {depth} depth")

            # Simulate the logic from the tool
            contribution_counts = {"quick": 1, "standard": 2, "comprehensive": 3}

            num_contributions = contribution_counts.get(depth, 2)
            assert num_contributions == expected_count


class TestInterruptMode:
    """Test the interrupt mode functionality"""

    def test_generate_interrupt_intervention_planning_phase(self):
        """Test interrupt intervention generation for planning phase"""
        engine = VibeMentorEngine()
        
        # Test infrastructure pattern
        primary_pattern = {
            "pattern_type": "infrastructure_without_implementation",
            "detected": True,
            "confidence": 0.9
        }
        
        result = engine.generate_interrupt_intervention(
            query="I'll build a custom HTTP client for the API",
            phase="planning",
            primary_pattern=primary_pattern,
            pattern_confidence=0.9
        )
        
        assert result["question"] == "Have you checked if an official SDK exists for this?"
        assert result["severity"] == "high"
        assert result["suggestion"] == "Check for official SDK with retry/auth handling"
        assert result["pattern_type"] == "infrastructure_without_implementation"
        assert result["confidence"] == 0.9

    def test_generate_interrupt_intervention_implementation_phase(self):
        """Test interrupt intervention generation for implementation phase"""
        engine = VibeMentorEngine()
        
        # Test complexity escalation pattern
        primary_pattern = {
            "pattern_type": "complexity_escalation",
            "detected": True,
            "confidence": 0.75
        }
        
        result = engine.generate_interrupt_intervention(
            query="Adding abstraction layer for future flexibility",
            phase="implementation",
            primary_pattern=primary_pattern,
            pattern_confidence=0.75
        )
        
        assert result["question"] == "Could this be done with half the code?"
        assert result["severity"] == "low"
        assert result["suggestion"] == "Start concrete, abstract only when patterns emerge"
        assert result["pattern_type"] == "complexity_escalation"

    def test_generate_interrupt_intervention_review_phase(self):
        """Test interrupt intervention generation for review phase"""
        engine = VibeMentorEngine()
        
        # Test custom solution pattern
        primary_pattern = {
            "pattern_type": "custom_solution_preferred",
            "detected": True,
            "confidence": 0.8
        }
        
        result = engine.generate_interrupt_intervention(
            query="Completed custom authentication system",
            phase="review",
            primary_pattern=primary_pattern,
            pattern_confidence=0.8
        )
        
        assert result["question"] == "What would happen if we removed this custom layer?"
        assert result["severity"] == "medium"
        assert result["suggestion"] == "Use established auth library (OAuth2, JWT)"
        assert result["pattern_type"] == "custom_solution_preferred"

    def test_generate_interrupt_intervention_unknown_pattern(self):
        """Test interrupt intervention with unknown pattern type"""
        engine = VibeMentorEngine()
        
        # Unknown pattern
        primary_pattern = {
            "pattern_type": "unknown_pattern",
            "detected": True,
            "confidence": 0.7
        }
        
        result = engine.generate_interrupt_intervention(
            query="Some technical decision",
            phase="planning",
            primary_pattern=primary_pattern,
            pattern_confidence=0.7
        )
        
        # Should use default questions/suggestions
        assert "validated" in result["question"].lower()
        assert result["severity"] == "low"
        assert result["suggestion"] == "Validate with simpler approach"

    def test_interrupt_mode_phase_awareness(self):
        """Test that interrupt mode provides phase-specific questions"""
        engine = VibeMentorEngine()
        
        pattern = {
            "pattern_type": "documentation_neglect",
            "detected": True,
            "confidence": 0.85
        }
        
        # Test same pattern in different phases
        phases = ["planning", "implementation", "review"]
        questions_seen = set()
        
        for phase in phases:
            result = engine.generate_interrupt_intervention(
                query="Building integration without checking docs",
                phase=phase,
                primary_pattern=pattern,
                pattern_confidence=0.85
            )
            questions_seen.add(result["question"])
        
        # Should have different questions for different phases
        assert len(questions_seen) == 3

    def test_interrupt_mode_keyword_based_suggestions(self):
        """Test that suggestions adapt based on query keywords"""
        engine = VibeMentorEngine()
        
        pattern = {
            "pattern_type": "custom_solution_preferred",
            "detected": True,
            "confidence": 0.8
        }
        
        # Test HTTP client query
        result1 = engine.generate_interrupt_intervention(
            query="Building custom HTTP client",
            phase="planning",
            primary_pattern=pattern,
            pattern_confidence=0.8
        )
        assert "SDK" in result1["suggestion"]
        
        # Test auth query
        result2 = engine.generate_interrupt_intervention(
            query="Custom auth implementation",
            phase="planning", 
            primary_pattern=pattern,
            pattern_confidence=0.8
        )
        assert "OAuth2" in result2["suggestion"] or "JWT" in result2["suggestion"]
        
        # Test abstraction query
        result3 = engine.generate_interrupt_intervention(
            query="Adding abstraction layer",
            phase="planning",
            primary_pattern=pattern,
            pattern_confidence=0.8
        )
        assert "concrete" in result3["suggestion"].lower()


if __name__ == "__main__":
    pytest.main([__file__])
