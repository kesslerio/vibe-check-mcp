"""
Integration Tests for End-to-End Workflow

Tests the complete workflow from issue analysis to result delivery:
- Full vibe check workflow
- Integration between all components
- Real-world scenario testing
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.analyze_issue import analyze_issue
from vibe_check.tools.legacy.vibe_check_framework import (
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult,
)
from vibe_check.core.educational_content import DetailLevel
from vibe_check.core.pattern_detector import DetectionResult


class TestEndToEndWorkflow:
    """Integration tests for complete end-to-end workflow"""

    @pytest.mark.integration
    def test_complete_vibe_check_workflow_quick_mode(self):
        """Test complete workflow in quick mode"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            # Setup comprehensive mock result
            vibe_result = VibeCheckResult(
                vibe_level=VibeLevel.GOOD_VIBES,
                overall_vibe="✅ Good Vibes",
                friendly_summary="This looks great! No anti-patterns detected.",
                coaching_recommendations=[
                    "Keep up the excellent work!",
                    "Consider adding tests for robustness",
                ],
                technical_analysis={
                    "detected_patterns": [],
                    "integration_analysis": {
                        "third_party_services": [],
                        "infrastructure_keywords": [],
                        "complexity_indicators": [],
                    },
                    "analysis_metadata": {
                        "claude_analysis_available": False,
                        "clear_thought_analysis_available": False,
                        "detail_level": "brief",
                    },
                },
                claude_reasoning=None,
                clear_thought_analysis=None,
            )

            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = vibe_result
            mock_get_framework.return_value = mock_framework

            # Execute workflow
            result = analyze_issue(
                issue_number=42,
                repository="test/good-repo",
                analysis_mode="quick",
                detail_level="brief",
                post_comment=False,
            )

            # Verify workflow execution
            mock_framework.check_issue_vibes.assert_called_once_with(
                issue_number=42,
                repository="test/good-repo",
                mode=VibeCheckMode.QUICK,
                detail_level=DetailLevel.BRIEF,
                post_comment=False,
            )

            # Verify complete response structure
            assert result["status"] == "vibe_check_complete"
            assert "analysis_timestamp" in result

            # Verify vibe check results
            vibe_check = result["vibe_check"]
            assert vibe_check["overall_vibe"] == "✅ Good Vibes"
            assert vibe_check["vibe_level"] == "good_vibes"
            assert "No anti-patterns detected" in vibe_check["friendly_summary"]
            assert len(vibe_check["coaching_recommendations"]) == 2

            # Verify technical analysis
            tech_analysis = result["technical_analysis"]
            assert len(tech_analysis["detected_patterns"]) == 0
            assert tech_analysis["analysis_metadata"]["detail_level"] == "brief"

            # Verify enhanced features
            features = result["enhanced_features"]
            assert features["claude_reasoning"] == False
            assert features["clear_thought_analysis"] == False
            assert features["educational_coaching"] == True
            assert features["friendly_language"] == True

    @pytest.mark.integration
    def test_complete_vibe_check_workflow_comprehensive_mode(self):
        """Test complete workflow in comprehensive mode"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            # Setup comprehensive mock result with advanced features
            vibe_result = VibeCheckResult(
                vibe_level=VibeLevel.BAD_VIBES,
                overall_vibe="🚨 Bad Vibes",
                friendly_summary="We found some concerning patterns that could lead to project delays and technical debt.",
                coaching_recommendations=[
                    "Start with official API documentation research",
                    "Build a minimal proof-of-concept first",
                    "Validate assumptions with real data",
                    "Consider using existing SDK instead of custom implementation",
                ],
                technical_analysis={
                    "detected_patterns": [
                        {
                            "type": "infrastructure_without_implementation",
                            "confidence": 0.9,
                            "detected": True,
                            "evidence": [
                                "custom server",
                                "instead of SDK",
                                "API integration",
                            ],
                        },
                        {
                            "type": "complexity_escalation",
                            "confidence": 0.7,
                            "detected": True,
                            "evidence": [
                                "sophisticated architecture",
                                "multiple services",
                            ],
                        },
                    ],
                    "integration_analysis": {
                        "third_party_services": ["api", "server", "integration"],
                        "infrastructure_keywords": [
                            "custom",
                            "architecture",
                            "implementation",
                        ],
                        "complexity_indicators": [
                            "sophisticated",
                            "multiple",
                            "complex",
                        ],
                    },
                    "analysis_metadata": {
                        "claude_analysis_available": True,
                        "clear_thought_analysis_available": True,
                        "detail_level": "comprehensive",
                    },
                },
                claude_reasoning="Based on the issue description, this appears to be a classic case of 'infrastructure without implementation'. The team is proposing to build custom infrastructure before validating that existing solutions won't work. This approach often leads to technical debt and project delays.",
                clear_thought_analysis={
                    "recommended_tools": [
                        {
                            "tool": "mcp__clear-thought-server__mentalmodel",
                            "reasoning": "First principles analysis needed to validate infrastructure requirements",
                        },
                        {
                            "tool": "mcp__clear-thought-server__decisionframework",
                            "reasoning": "Decision framework to evaluate build vs buy options",
                        },
                    ],
                    "systematic_analysis": "The proposed solution jumps to custom implementation without exploring existing options.",
                },
            )

            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = vibe_result
            mock_get_framework.return_value = mock_framework

            # Execute comprehensive workflow
            result = analyze_issue(
                issue_number=123,
                repository="test/complex-project",
                analysis_mode="comprehensive",
                detail_level="comprehensive",
                post_comment=True,
            )

            # Verify comprehensive workflow execution
            mock_framework.check_issue_vibes.assert_called_once_with(
                issue_number=123,
                repository="test/complex-project",
                mode=VibeCheckMode.COMPREHENSIVE,
                detail_level=DetailLevel.COMPREHENSIVE,
                post_comment=True,
            )

            # Verify complete response structure
            assert result["status"] == "vibe_check_complete"

            # Verify vibe check results
            vibe_check = result["vibe_check"]
            assert vibe_check["overall_vibe"] == "🚨 Bad Vibes"
            assert vibe_check["vibe_level"] == "bad_vibes"
            assert "concerning patterns" in vibe_check["friendly_summary"]
            assert len(vibe_check["coaching_recommendations"]) == 4

            # Verify technical analysis with multiple patterns
            tech_analysis = result["technical_analysis"]
            assert len(tech_analysis["detected_patterns"]) == 2

            patterns = tech_analysis["detected_patterns"]
            infrastructure_pattern = next(
                p
                for p in patterns
                if p["type"] == "infrastructure_without_implementation"
            )
            assert infrastructure_pattern["confidence"] == 0.9
            assert "custom server" in infrastructure_pattern["evidence"]

            complexity_pattern = next(
                p for p in patterns if p["type"] == "complexity_escalation"
            )
            assert complexity_pattern["confidence"] == 0.7

            # Verify integration analysis
            integration_analysis = tech_analysis["integration_analysis"]
            assert "api" in integration_analysis["third_party_services"]
            assert "custom" in integration_analysis["infrastructure_keywords"]
            assert "sophisticated" in integration_analysis["complexity_indicators"]

            # Verify enhanced features with Claude and Clear-Thought
            features = result["enhanced_features"]
            assert features["claude_reasoning"] == True
            assert features["clear_thought_analysis"] == True
            assert features["comprehensive_validation"] == True

            # Verify Claude reasoning content
            assert (
                "infrastructure without implementation"
                in result["vibe_check"]["claude_reasoning"]
            )
            assert "technical debt" in result["vibe_check"]["claude_reasoning"]

            # Verify Clear-Thought analysis
            clear_thought = result["vibe_check"]["clear_thought_analysis"]
            assert "recommended_tools" in clear_thought
            assert len(clear_thought["recommended_tools"]) == 2
            assert "mcp__clear-thought-server__mentalmodel" in str(clear_thought)

            # Verify issue info
            issue_info = result["issue_info"]
            assert issue_info["number"] == 123
            assert issue_info["repository"] == "test/complex-project"
            assert issue_info["analysis_mode"] == "comprehensive"
            assert issue_info["detail_level"] == "comprehensive"
            assert issue_info["comment_posted"] == True

    @pytest.mark.integration
    def test_workflow_error_handling_and_recovery(self):
        """Test workflow error handling and graceful degradation"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            # Test framework initialization failure
            mock_get_framework.side_effect = Exception(
                "Framework initialization failed"
            )

            result = analyze_issue(issue_number=42)

            # Should handle error gracefully
            assert result["status"] == "vibe_check_error"
            assert "Framework initialization failed" in result["error"]
            assert "friendly_error" in result
            assert "🚨 Oops!" in result["friendly_error"]
            assert result["issue_number"] == 42

    @pytest.mark.integration
    def test_workflow_with_mixed_confidence_patterns(self):
        """Test workflow with patterns of varying confidence levels"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            # Setup result with mixed confidence patterns
            vibe_result = VibeCheckResult(
                vibe_level=VibeLevel.RESEARCH_NEEDED,
                overall_vibe="🤔 Research Needed",
                friendly_summary="Some patterns detected, but we need more information to be sure.",
                coaching_recommendations=[
                    "Do more research on existing solutions",
                    "Create a small proof of concept",
                    "Document findings and assumptions",
                ],
                technical_analysis={
                    "detected_patterns": [
                        {
                            "type": "infrastructure_without_implementation",
                            "confidence": 0.6,  # Medium confidence
                            "detected": True,
                            "evidence": ["custom implementation", "API"],
                        },
                        {
                            "type": "documentation_neglect",
                            "confidence": 0.3,  # Low confidence
                            "detected": False,
                            "evidence": ["missing details"],
                        },
                    ],
                    "integration_analysis": {
                        "third_party_services": ["api"],
                        "infrastructure_keywords": ["custom"],
                        "complexity_indicators": [],
                    },
                },
            )

            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = vibe_result
            mock_get_framework.return_value = mock_framework

            result = analyze_issue(issue_number=42, analysis_mode="quick")

            # Verify mixed confidence handling
            assert result["status"] == "vibe_check_complete"
            assert result["vibe_check"]["vibe_level"] == "research_needed"
            assert "more information" in result["vibe_check"]["friendly_summary"]

            # Verify pattern handling
            patterns = result["technical_analysis"]["detected_patterns"]
            assert len(patterns) == 2

            # High confidence pattern should be detected
            infra_pattern = next(
                p
                for p in patterns
                if p["type"] == "infrastructure_without_implementation"
            )
            assert infra_pattern["detected"] == True
            assert infra_pattern["confidence"] == 0.6

            # Low confidence pattern should not be detected
            doc_pattern = next(
                p for p in patterns if p["type"] == "documentation_neglect"
            )
            assert doc_pattern["detected"] == False
            assert doc_pattern["confidence"] == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
