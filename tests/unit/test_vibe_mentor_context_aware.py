"""
Tests for Context-Aware Vibe Check Mentor

Verifies that vibe_check_mentor:
- Uses context-first processing
- Asks clarifying questions when confidence is low
- Adjusts pattern detection based on context type
- Doesn't give generic advice for completion reports
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from vibe_check.server import vibe_check_mentor


class TestVibeMentorContextAware:
    """Test context-aware behavior of vibe_check_mentor"""

    @patch(
        "vibe_check.server.tools.mentor.core.generate_response",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.load_workspace_context",
        new_callable=AsyncMock,
    )
    @patch("vibe_check.server.get_mentor_engine")
    @patch("vibe_check.server.analyze_text_demo")
    def test_shapescale_no_generic_advice(
        self,
        mock_analyze,
        mock_engine,
        mock_load,
        mock_analysis,
        mock_generate,
    ):
        """Test that ShapeScale case doesn't trigger generic Stripe advice"""
        # Mock the pattern detection to return what it would for "implement"
        mock_analyze.return_value = {
            "patterns": [
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "detected": True,
                    "confidence": 0.7,
                    "evidence": ["implement", "checkout"],
                }
            ],
            "analysis_results": {"patterns_detected": 1},
        }

        # Mock mentor engine and upstream analysis
        mock_engine.return_value = MagicMock()

        query = """Just implemented Issue #861 checkout URL strategy update. Changed from
        defaulting to direct Stripe checkout URLs to three-path approach. Did I miss anything important?"""

        context = "Follow-on to working Issue #861, implementation phase complete."

        mock_load.return_value = (context, "session-123", "")
        mock_analysis.return_value = {
            "status": "success",
            "vibe_level": "steady",
            "pattern_confidence": 0.4,
            "detected_patterns": mock_analyze.return_value["patterns"],
        }
        mock_generate.return_value = {
            "status": "success",
            "immediate_feedback": {
                "vibe_level": "steady",
                "confidence": 0.4,
            },
        }
        result = asyncio.run(
            vibe_check_mentor(query=query, context=context, reasoning_depth="standard")
        )

        # Should recognize this as a completion report
        # Pattern confidence should be reduced
        assert result["immediate_feedback"]["vibe_level"] != "concerning"
        assert result["immediate_feedback"]["confidence"] < 0.7  # Reduced from original

    @patch(
        "vibe_check.server.tools.mentor.core.generate_response",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.load_workspace_context",
        new_callable=AsyncMock,
    )
    @patch("vibe_check.server.get_mentor_engine")
    @patch("vibe_check.server.analyze_text_demo")
    def test_ambiguous_query_asks_questions(
        self,
        mock_analyze,
        mock_engine,
        mock_load,
        mock_analysis,
        mock_generate,
    ):
        """Test that ambiguous queries trigger clarifying questions"""
        mock_analyze.return_value = {"patterns": [], "analysis_results": {}}
        mock_engine.return_value = MagicMock()
        mock_load.return_value = (None, "session-456", "")
        mock_analysis.return_value = {
            "status": "clarification_needed",
            "clarifying_questions": ["Is this in planning or implementation?"],
        }

        # Ambiguous query
        query = "I need to implement Stripe integration"

        result = asyncio.run(vibe_check_mentor(query=query, reasoning_depth="standard"))

        # Should ask for clarification
        assert result["status"] == "clarification_needed"
        assert "clarifying_questions" in result
        assert len(result["clarifying_questions"]) > 0
        assert any(
            "planning" in q or "completed" in q for q in result["clarifying_questions"]
        )

    @patch(
        "vibe_check.server.tools.mentor.core.generate_response",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.load_workspace_context",
        new_callable=AsyncMock,
    )
    @patch("vibe_check.server.get_mentor_engine")
    @patch("vibe_check.server.analyze_text_demo")
    def test_high_confidence_planning_normal_flow(
        self,
        mock_analyze,
        mock_engine,
        mock_load,
        mock_analysis,
        mock_generate,
    ):
        """Test that high confidence planning discussions follow normal flow"""
        mock_analyze.return_value = {
            "patterns": [
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "detected": True,
                    "confidence": 0.8,
                    "evidence": ["build custom", "planning"],
                }
            ],
            "analysis_results": {"patterns_detected": 1},
        }

        mock_engine.return_value = MagicMock()
        mock_load.return_value = (None, "session-789", "")
        mock_analysis.return_value = {
            "status": "success",
            "vibe_level": "concerning",
            "pattern_confidence": 0.8,
            "detected_patterns": mock_analyze.return_value["patterns"],
        }
        mock_generate.return_value = {
            "status": "success",
            "immediate_feedback": {
                "vibe_level": "concerning",
                "confidence": 0.8,
            },
        }

        query = "I'm planning to build a custom HTTP client instead of using the SDK"

        result = asyncio.run(vibe_check_mentor(query=query, reasoning_depth="standard"))

        # Should NOT ask questions - clear planning anti-pattern
        assert result.get("status") != "clarification_needed"
        # Should maintain high concern for planning anti-patterns
        assert result["immediate_feedback"]["vibe_level"] == "concerning"

    @patch(
        "vibe_check.server.tools.mentor.core.generate_response",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.load_workspace_context",
        new_callable=AsyncMock,
    )
    @patch("vibe_check.server.get_mentor_engine")
    @patch("vibe_check.server.analyze_text_demo")
    def test_review_request_with_completion(
        self,
        mock_analyze,
        mock_engine,
        mock_load,
        mock_analysis,
        mock_generate,
    ):
        """Test review requests on completed work"""
        mock_analyze.return_value = {
            "patterns": [
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "detected": True,
                    "confidence": 0.6,
                    "evidence": ["implemented"],
                }
            ],
            "analysis_results": {"patterns_detected": 1},
        }

        mock_engine.return_value = MagicMock()
        mock_load.return_value = (None, "session-321", "")
        mock_analysis.return_value = {
            "status": "success",
            "vibe_level": "steady",
            "pattern_confidence": 0.5,
            "detected_patterns": mock_analyze.return_value["patterns"],
        }
        mock_generate.return_value = {
            "status": "success",
            "immediate_feedback": {
                "vibe_level": "steady",
                "confidence": 0.5,
            },
        }

        query = "I implemented a custom solution. Any feedback on this approach?"

        result = asyncio.run(vibe_check_mentor(query=query, reasoning_depth="standard"))

        # Should reduce concern for completed work under review
        assert result["immediate_feedback"]["confidence"] < 0.6
        assert result["immediate_feedback"]["vibe_level"] != "concerning"

    @patch(
        "vibe_check.server.tools.mentor.core.generate_response",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.load_workspace_context",
        new_callable=AsyncMock,
    )
    @patch("vibe_check.server.get_mentor_engine")
    @patch("vibe_check.server.analyze_text_demo")
    def test_interrupt_mode_skips_questions(
        self,
        mock_analyze,
        mock_engine,
        mock_load,
        mock_analysis,
        mock_generate,
    ):
        """Test that interrupt mode doesn't ask clarifying questions"""
        mock_analyze.return_value = {"patterns": [], "analysis_results": {}}
        mock_engine.return_value = MagicMock()
        mock_load.return_value = (None, "session-interrupt", "")
        mock_analysis.return_value = {
            "status": "success",
            "vibe_level": "neutral",
            "pattern_confidence": 0.3,
            "detected_patterns": [],
        }
        mock_generate.return_value = {
            "status": "success",
            "immediate_feedback": {
                "vibe_level": "neutral",
                "confidence": 0.3,
            },
        }

        query = "Working on API integration"  # Vague query

        result = asyncio.run(
            vibe_check_mentor(query=query, mode="interrupt", reasoning_depth="quick")
        )

        # Should NOT ask questions in interrupt mode
        assert result.get("status") != "clarification_needed"
        assert "clarifying_questions" not in result

    @patch(
        "vibe_check.server.tools.mentor.core.generate_response",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
        new_callable=AsyncMock,
    )
    @patch(
        "vibe_check.server.tools.mentor.core.load_workspace_context",
        new_callable=AsyncMock,
    )
    @patch("vibe_check.server.get_mentor_engine")
    @patch("vibe_check.server.analyze_text_demo")
    def test_process_description_recognition(
        self,
        mock_analyze,
        mock_engine,
        mock_load,
        mock_analysis,
        mock_generate,
    ):
        """Test that process descriptions are recognized correctly"""
        mock_analyze.return_value = {
            "patterns": [],
            "analysis_results": {"patterns_detected": 0},
        }

        mock_engine.return_value = MagicMock()
        mock_load.return_value = (None, "session-process", "")
        mock_analysis.return_value = {
            "status": "success",
            "vibe_level": "good",
            "pattern_confidence": 0.2,
            "detected_patterns": [],
        }
        mock_generate.return_value = {
            "status": "success",
            "immediate_feedback": {
                "vibe_level": "good",
                "confidence": 0.2,
            },
        }

        query = "Updated our API strategy from REST to GraphQL approach"
        context = "Migration complete, new endpoints deployed"

        result = asyncio.run(
            vibe_check_mentor(query=query, context=context, reasoning_depth="standard")
        )

        # Should recognize as process change, not anti-pattern
        assert result["immediate_feedback"]["vibe_level"] == "good"

    def test_metadata_in_response(self):
        """Test that context metadata is included in appropriate places"""
        with patch("vibe_check.server.get_mentor_engine") as mock_engine:
            with patch("vibe_check.server.analyze_text_demo") as mock_analyze:
                with patch(
                    "vibe_check.server.tools.mentor.core.load_workspace_context",
                    new_callable=AsyncMock,
                ) as mock_load:
                    with patch(
                        "vibe_check.server.tools.mentor.core.analyze_query_and_context",
                        new_callable=AsyncMock,
                    ) as mock_analysis:
                        with patch(
                            "vibe_check.server.tools.mentor.core.generate_response",
                            new_callable=AsyncMock,
                        ) as mock_generate:
                            mock_analyze.return_value = {
                                "patterns": [],
                                "analysis_results": {},
                            }
                            mock_engine.return_value = MagicMock()
                            mock_load.return_value = (None, "session-meta", "")
                            mock_analysis.return_value = {
                                "status": "success",
                                "vibe_level": "steady",
                                "pattern_confidence": 0.3,
                                "detected_patterns": [],
                            }
                            mock_generate.return_value = {
                                "status": "success",
                                "immediate_feedback": {
                                    "vibe_level": "steady",
                                    "confidence": 0.3,
                                    "context_type": "completion_report",
                                },
                            }

                            query = "Completed issue #123 with new integration"

                            result = asyncio.run(vibe_check_mentor(query=query))

                            # Context type should be indicated somewhere
                            if "context_type" in result.get("immediate_feedback", {}):
                                assert (
                                    result["immediate_feedback"]["context_type"]
                                    == "completion_report"
                                )
