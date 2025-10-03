"""
Integration Tests for End-to-End Workflow

Tests the complete workflow from issue analysis to result delivery:
- Full vibe check workflow
- Integration between all components
- Real-world scenario testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.analyze_issue import analyze_issue
from vibe_check.core.educational_content import DetailLevel


class TestEndToEndWorkflow:
    """Integration tests for complete end-to-end workflow"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow_basic_mode(self):
        """Test complete workflow in basic (quick) mode"""

        mock_basic_result = {
            "status": "basic_analysis_complete",
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "issue_info": {
                "number": 42,
                "title": "Test Issue",
                "author": "tester",
                "created_at": "2024-01-01T00:00:00Z",
                "repository": "test/good-repo",
                "url": "https://example.com/issues/42",
                "labels": [],
            },
            "patterns_detected": [],
            "confidence_summary": {
                "total_patterns_detected": 0,
                "average_confidence": 0.0,
                "highest_confidence": 0.0,
                "patterns_by_confidence": [],
            },
            "recommended_actions": [
                "Keep up the excellent work!",
                "Consider adding tests for robustness",
            ],
            "analysis_metadata": {
                "detail_level": "brief",
                "external_claude_available": False,
            },
        }

        with patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer") as mock_get_analyzer:
            mock_analyzer = MagicMock()
            mock_analyzer.claude_cli_enabled = False
            mock_analyzer.analyze_issue_basic = AsyncMock(return_value=mock_basic_result)
            mock_get_analyzer.return_value = mock_analyzer

            result = await analyze_issue(
                issue_number=42,
                repository="test/good-repo",
                analysis_mode="quick",
                detail_level=DetailLevel.BRIEF,
                post_comment=False,
            )

            mock_get_analyzer.assert_called_once()
            mock_analyzer.analyze_issue_basic.assert_awaited_once_with(
                issue_number=42,
                repository="test/good-repo",
                detail_level="brief",
            )

            assert result["status"] == "basic_analysis_complete"
            assert result["issue_info"]["repository"] == "test/good-repo"
            assert result["recommended_actions"] == mock_basic_result["recommended_actions"]
            assert result["analysis_metadata"]["detail_level"] == "brief"

            enhanced = result["enhanced_analysis"]
            assert enhanced["analysis_mode"] == "basic"
            assert enhanced["claude_cli_enabled"] is False
            assert enhanced["backward_compatible"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow_comprehensive_mode(self):
        """Test complete workflow in comprehensive mode"""

        mock_comprehensive_result = {
            "status": "comprehensive_analysis_complete",
            "analysis_timestamp": "2024-01-02T00:00:00Z",
            "issue_info": {
                "number": 123,
                "title": "Complex Issue",
                "author": "architect",
                "created_at": "2024-01-02T00:00:00Z",
                "repository": "test/complex-project",
                "url": "https://example.com/issues/123",
                "labels": ["integration"],
            },
            "comprehensive_analysis": {
                "success": True,
                "claude_output": "Comprehensive reasoning",
                "execution_time_seconds": 2.5,
            },
            "enhanced_features": {
                "claude_cli_integration": True,
                "sophisticated_reasoning": True,
            },
        }

        with patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer") as mock_get_analyzer:
            mock_analyzer = MagicMock()
            mock_analyzer.claude_cli_enabled = True
            mock_analyzer.analyze_issue_comprehensive = AsyncMock(
                return_value=mock_comprehensive_result
            )
            mock_get_analyzer.return_value = mock_analyzer

            result = await analyze_issue(
                issue_number=123,
                repository="test/complex-project",
                analysis_mode="comprehensive",
                detail_level="comprehensive",
                post_comment=True,
            )

            mock_analyzer.analyze_issue_comprehensive.assert_awaited_once_with(
                issue_number=123,
                repository="test/complex-project",
                detail_level="comprehensive",
            )

            assert result["status"] == "comprehensive_analysis_complete"
            assert result["issue_info"]["number"] == 123
            assert result["enhanced_analysis"]["analysis_mode"] == "comprehensive"
            assert result["enhanced_analysis"]["claude_cli_enabled"] is True

            comment_posting = result.get("comment_posting")
            assert comment_posting is not None
            assert comment_posting["requested"] is True
            assert comment_posting["status"] == "not_implemented"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_error_handling_and_recovery(self):
        """Test workflow error handling and graceful degradation"""

        with patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer") as mock_get_analyzer:
            mock_analyzer = MagicMock()
            mock_analyzer.claude_cli_enabled = True
            mock_analyzer.analyze_issue_hybrid = AsyncMock(
                side_effect=Exception("Hybrid analysis failed")
            )
            mock_get_analyzer.return_value = mock_analyzer

            result = await analyze_issue(issue_number=42)

            assert result["status"] == "enhanced_analysis_error"
            assert "Hybrid analysis failed" in result["error"]
            assert result["analysis_mode"] == "hybrid"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_with_mixed_confidence_patterns(self):
        """Test workflow with patterns of varying confidence levels"""

        mock_basic_result = {
            "status": "basic_analysis_complete",
            "analysis_timestamp": "2024-03-01T00:00:00Z",
            "issue_info": {
                "number": 42,
                "title": "Pattern Mix",
                "author": "tester",
                "created_at": "2024-03-01T00:00:00Z",
                "repository": "test/repo",
                "url": "https://example.com/issues/42",
                "labels": [],
            },
            "patterns_detected": [
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "confidence": 0.6,
                    "detected": True,
                    "evidence": ["custom implementation", "API"],
                    "threshold": 0.7,
                    "educational_content": {},
                },
                {
                    "pattern_type": "documentation_neglect",
                    "confidence": 0.3,
                    "detected": False,
                    "evidence": ["missing details"],
                    "threshold": 0.7,
                    "educational_content": {},
                },
            ],
            "confidence_summary": {
                "total_patterns_detected": 2,
                "average_confidence": 0.45,
                "highest_confidence": 0.6,
                "patterns_by_confidence": [],
            },
            "recommended_actions": [
                "Do more research on existing solutions",
                "Create a small proof of concept",
                "Document findings and assumptions",
            ],
            "analysis_metadata": {
                "detail_level": "standard",
                "external_claude_available": False,
            },
        }

        with patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer") as mock_get_analyzer:
            mock_analyzer = MagicMock()
            mock_analyzer.claude_cli_enabled = False
            mock_analyzer.analyze_issue_basic = AsyncMock(return_value=mock_basic_result)
            mock_get_analyzer.return_value = mock_analyzer

            result = await analyze_issue(issue_number=42, analysis_mode="quick")

            mock_analyzer.analyze_issue_basic.assert_awaited_once()
            assert result["status"] == "basic_analysis_complete"

            patterns = result["patterns_detected"]
            assert len(patterns) == 2

            infra_pattern = next(
                p
                for p in patterns
                if p["pattern_type"] == "infrastructure_without_implementation"
            )
            assert infra_pattern["detected"] is True
            assert infra_pattern["confidence"] == 0.6

            doc_pattern = next(
                p
                for p in patterns
                if p["pattern_type"] == "documentation_neglect"
            )
            assert doc_pattern["detected"] is False
            assert doc_pattern["confidence"] == 0.3

            summary = result["confidence_summary"]
            assert summary["total_patterns_detected"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
