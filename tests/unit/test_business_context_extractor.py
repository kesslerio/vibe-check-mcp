"""
Tests for Business Context Extractor

Verifies that the system correctly identifies:
- Completion reports vs planning discussions
- Review requests vs implementation proposals
- Confidence levels and clarifying questions
"""

import pytest
from vibe_check.core.business_context_extractor import (
    BusinessContextExtractor,
    ContextType,
    ConfidenceLevel,
)


class TestBusinessContextExtractor:
    """Test business context extraction logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = BusinessContextExtractor()

    def test_shapescale_completion_report(self):
        """Test the exact ShapeScale case that triggered the bug"""
        query = """Just implemented Issue #861 checkout URL strategy update. Changed from 
        defaulting to direct Stripe checkout URLs to three-path approach: 1) Pricing page
        for unknown products, 2) Customer collection page for known products (PREFERRED), 
        3) Direct checkout (documentation only). Added full pre-fill support (email,
        names, company, phone) to customer collection. Updated core_data.json, created 
        comprehensive AE module knowledge, and concise SDR/CS references with RAG query
        instructions. Did I miss anything important?"""

        context = """Follow-on to working Issue #861, implementation phase complete. 
        Updated checkout URL strategy from direct Stripe links to customer journey-based 
        approach. Key features: email prompting requirements, full pre-fill capabilities 
        on customer collection page, better conversion tracking. Domain split: 
        business.shapescale.com (Webflow) vs shapescale.com (PHP/Stripe)."""

        result = self.extractor.extract_context(query, context)

        assert result.primary_type == ContextType.COMPLETION_REPORT
        assert result.confidence >= ConfidenceLevel.HIGH.value
        assert result.is_completion_report is True
        assert result.is_planning_phase is False
        assert len(result.questions_needed) == 0  # High confidence, no questions
        assert "reference_number" in result.metadata
        assert result.metadata["reference_number"] == "861"

    def test_clear_completion_indicators(self):
        """Test various completion indicator patterns"""
        test_cases = [
            (
                "I completed issue #123 with the new API integration",
                ContextType.COMPLETION_REPORT,
            ),
            (
                "Just finished implementing the feature from PR #456",
                ContextType.COMPLETION_REPORT,
            ),
            ("Successfully shipped the checkout update", ContextType.COMPLETION_REPORT),
            (
                "We've already implemented the new authentication system",
                ContextType.COMPLETION_REPORT,
            ),
            (
                "Here's what I built for the payment integration",
                ContextType.COMPLETION_REPORT,
            ),
        ]

        for text, expected_type in test_cases:
            result = self.extractor.extract_context(text)
            assert result.primary_type == expected_type, f"Failed for: {text}"
            assert result.confidence >= ConfidenceLevel.MEDIUM.value

    def test_review_request_indicators(self):
        """Test review request detection"""
        test_cases = [
            (
                "Did I miss anything important in this implementation?",
                ContextType.REVIEW_REQUEST,
            ),
            ("What do you think about this approach?", ContextType.REVIEW_REQUEST),
            ("Any feedback on my PR?", ContextType.REVIEW_REQUEST),
            ("Does this look good to you?", ContextType.REVIEW_REQUEST),
            ("Thoughts on this architecture?", ContextType.REVIEW_REQUEST),
        ]

        for text, expected_type in test_cases:
            result = self.extractor.extract_context(text)
            assert result.primary_type == expected_type, f"Failed for: {text}"

    def test_planning_indicators(self):
        """Test planning phase detection"""
        test_cases = [
            (
                "I'm planning to build a custom HTTP client",
                ContextType.PLANNING_DISCUSSION,
            ),
            (
                "Should I implement my own authentication?",
                ContextType.PLANNING_DISCUSSION,
            ),
            ("We want to create a new API wrapper", ContextType.PLANNING_DISCUSSION),
            ("Thinking about building our own SDK", ContextType.PLANNING_DISCUSSION),
            (
                "How should I approach this integration?",
                ContextType.PLANNING_DISCUSSION,
            ),
        ]

        for text, expected_type in test_cases:
            result = self.extractor.extract_context(text)
            assert result.primary_type == expected_type, f"Failed for: {text}"
            assert result.is_planning_phase is True

    def test_ambiguous_context_generates_questions(self):
        """Test that ambiguous contexts generate clarifying questions"""
        # Ambiguous "implement" without clear completion/planning indicators
        query = "I need to implement Stripe integration for our checkout"

        result = self.extractor.extract_context(query)

        assert result.confidence < ConfidenceLevel.HIGH.value
        assert len(result.questions_needed) > 0
        assert any(
            "planning" in q.lower() or "completed" in q.lower()
            for q in result.questions_needed
        )

    def test_low_confidence_triggers_questions(self):
        """Test that low confidence scenarios generate appropriate questions"""
        # Very vague query
        query = "Working on the API stuff"

        result = self.extractor.extract_context(query)

        assert result.confidence <= ConfidenceLevel.LOW.value
        assert result.needs_clarification is True
        assert len(result.questions_needed) > 0

    def test_metadata_extraction(self):
        """Test metadata extraction from context"""
        query = "Completed issue #42 for the Stripe SDK integration"

        result = self.extractor.extract_context(query)

        assert "reference_number" in result.metadata
        assert result.metadata["reference_number"] == "42"
        assert "technologies" in result.metadata
        assert "sdk" in result.metadata["technologies"]
        assert "integration" in result.metadata["technologies"]
        assert "actions" in result.metadata
        assert any(
            "completed" in action.lower() for action in result.metadata["actions"]
        )

    def test_process_description_detection(self):
        """Test business process description detection"""
        query = (
            "Updated our checkout strategy from direct links to a three-path approach"
        )

        result = self.extractor.extract_context(query)

        assert result.primary_type == ContextType.PROCESS_DESCRIPTION
        assert result.confidence >= ConfidenceLevel.MEDIUM.value

    def test_technology_specific_questions(self):
        """Test technology-specific clarifying questions"""
        query = "Building a new API integration"

        result = self.extractor.extract_context(query)

        # Should ask about official SDK research
        assert any(
            "official" in q.lower() and ("sdk" in q.lower() or "api" in q.lower())
            for q in result.questions_needed
        )

    def test_combined_indicators(self):
        """Test handling of mixed indicators"""
        # Has both completion and planning language
        query = "I completed the prototype but now planning to build the full implementation"

        result = self.extractor.extract_context(query)

        # Should recognize the stronger indicator (completed) but with lower confidence
        assert result.primary_type in [
            ContextType.COMPLETION_REPORT,
            ContextType.PLANNING_DISCUSSION,
        ]
        assert (
            result.confidence < ConfidenceLevel.HIGH.value
        )  # Mixed signals lower confidence

    # NEW TESTS FOR ISSUE #173 FIX - Explicit Phase Parameter

    def test_explicit_planning_phase(self):
        """Test explicit phase='planning' bypasses ambiguity detection"""
        # Ambiguous query that normally would trigger questions
        query = "I implement a new API integration solution"

        # Without explicit phase - should ask clarifying questions or have low confidence
        result_normal = self.extractor.extract_context(query)
        normal_confidence = result_normal.confidence

        # With explicit phase='planning' - should have high confidence
        result_explicit = self.extractor.extract_context(query, phase="planning")
        assert result_explicit.primary_type == ContextType.PLANNING_DISCUSSION
        assert result_explicit.confidence >= ConfidenceLevel.HIGH.value
        assert (
            result_explicit.confidence > normal_confidence
        )  # Should be higher than normal
        assert len(result_explicit.questions_needed) == 0
        assert "explicit_phase: planning" in result_explicit.indicators[0]

    def test_explicit_implementation_phase(self):
        """Test explicit phase='implementation' sets correct context"""
        query = "Working on the API integration"

        result = self.extractor.extract_context(query, phase="implementation")

        assert result.primary_type == ContextType.IMPLEMENTATION_PROPOSAL
        assert result.confidence >= ConfidenceLevel.HIGH.value
        assert len(result.questions_needed) == 0

    def test_explicit_review_phase(self):
        """Test explicit phase='review' sets correct context"""
        query = "Check my implementation approach"

        result = self.extractor.extract_context(query, phase="review")

        assert result.primary_type == ContextType.REVIEW_REQUEST
        assert result.confidence >= ConfidenceLevel.HIGH.value
        assert len(result.questions_needed) == 0

    def test_unknown_explicit_phase_fallback(self):
        """Test unknown explicit phase falls back to normal detection"""
        query = "I'm planning to implement something"

        result = self.extractor.extract_context(query, phase="unknown_phase")

        # Should fall back to normal pattern detection
        assert (
            result.primary_type == ContextType.PLANNING_DISCUSSION
        )  # Normal detection
        # Confidence may be lower than explicit phase

    def test_original_issue_173_scenario(self):
        """Test the exact scenario from Issue #173 that was failing"""
        query = "I'm planning to implement a tier2/3 knowledge index feature for our tier1 content files. Should I extend the existing EnhancedTierAssignment class to include a tier_index field, or create a separate TierIndexGenerator service?"
        context = "This is greenfield planning for new feature. Existing architecture: TierClassificationServiceV3 handles tier classification"

        # With explicit phase - should NOT ask clarifying questions
        result = self.extractor.extract_context(query, context, phase="planning")

        assert result.primary_type == ContextType.PLANNING_DISCUSSION
        assert result.confidence >= ConfidenceLevel.HIGH.value
        assert len(result.questions_needed) == 0
        assert not any(
            "Are you planning to implement this" in q for q in result.questions_needed
        )
        assert "explicit_phase: planning" in result.indicators[0]

    def test_backward_compatibility_no_phase(self):
        """Test that existing code without phase parameter still works"""
        query = "I'm planning to build something"

        # Old way - should still work
        result = self.extractor.extract_context(query)
        assert result.primary_type is not None
        assert isinstance(result.confidence, float)
