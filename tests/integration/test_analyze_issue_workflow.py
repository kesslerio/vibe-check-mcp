"""
Integration Tests for Analyze Issue Workflow

Tests the complete end-to-end analyze_issue workflow:
- Full workflow execution
- Legacy to enhanced tool transition
- Integration with vibe check framework
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.analyze_issue import GitHubIssueAnalyzer, analyze_issue
from vibe_check.tools.legacy.vibe_check_framework import (
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult,
)
from vibe_check.core.educational_content import DetailLevel


class TestAnalyzeIssueIntegrationWorkflow:
    """Integration tests for complete analyze_issue workflow"""



    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_legacy_analyzer_to_enhanced_tool_transition(self):
        """Test transition from legacy analyzer to enhanced MCP tool"""
        with patch("vibe_check.tools.analyze_issue.Github") as mock_github:
            # Test that legacy analyzer still works
            analyzer = GitHubIssueAnalyzer("test_token")

            # Mock GitHub API
            mock_issue = MagicMock()
            mock_issue.number = 42
            mock_issue.title = "Test Issue"
            mock_issue.body = "Test content for pattern detection"
            mock_issue.user.login = "testuser"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T00:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/42"

            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            analyzer.github_client.get_repo.return_value = mock_repo

            # Mock pattern detection
            with patch.object(
                analyzer.pattern_detector, "analyze_text_for_patterns"
            ) as mock_patterns:
                mock_patterns.return_value = []

                # Test legacy analyzer
                legacy_result = analyzer.analyze_issue(42, "test/repo")

                # Verify legacy response format
                assert legacy_result["status"] == "basic_analysis_complete"
                assert "issue_info" in legacy_result
                assert "patterns_detected" in legacy_result
                assert "analysis_metadata" in legacy_result

                # Test enhanced MCP tool
                with patch(
                    "vibe_check.tools.analyze_issue.get_vibe_check_framework"
                ) as mock_get_framework:
                    mock_framework = MagicMock()
                    mock_framework.check_issue_vibes.return_value = VibeCheckResult(
                        vibe_level=VibeLevel.GOOD_VIBES,
                        overall_vibe="✅ Good Vibes",
                        friendly_summary="Legacy transition test",
                        coaching_recommendations=[],
                        technical_analysis={},
                    )
                    mock_get_framework.return_value = mock_framework

                    enhanced_result = await analyze_issue(42, "test/repo", analysis_mode="basic")

                    # Verify enhanced response format
                    assert enhanced_result["status"] == "basic_analysis_complete"



    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_error_handling_and_recovery(self):
        """Test error handling and recovery in the integration workflow"""
        with patch("vibe_check.tools.analyze_issue.EnhancedGitHubIssueAnalyzer.analyze_issue_hybrid", side_effect=Exception("Hybrid analysis failed")):
            result = await analyze_issue(issue_number=42)

            # Should handle error gracefully
            assert result["status"] == "enhanced_analysis_error"
            assert "Hybrid analysis failed" in result["error"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_with_different_configurations(self):
        """Test workflow with different configuration combinations"""
        # Test configuration combinations
        test_configs = [
            {
                "mode": "basic",
                "detail": "brief",
                "comment": False,
            },
            {
                "mode": "comprehensive",
                "detail": "comprehensive",
                "comment": True,
            },
        ]

        for config in test_configs:
            with patch("vibe_check.tools.analyze_issue.EnhancedGitHubIssueAnalyzer.analyze_issue_basic") as mock_basic, \
                 patch("vibe_check.tools.analyze_issue.EnhancedGitHubIssueAnalyzer.analyze_issue_comprehensive") as mock_comprehensive, \
                 patch("vibe_check.tools.analyze_issue.EnhancedGitHubIssueAnalyzer.analyze_issue_hybrid") as mock_hybrid:

                mock_basic.return_value = {"status": "basic_analysis_complete"}
                mock_comprehensive.return_value = {"status": "comprehensive_analysis_complete"}
                mock_hybrid.return_value = {"status": "hybrid_analysis_complete"}

                # Test configuration
                result = await analyze_issue(
                    issue_number=42,
                    analysis_mode=config["mode"],
                    detail_level=config["detail"],
                    post_comment=config["comment"],
                )

                # Verify configuration was applied
                assert result["enhanced_analysis"]["analysis_mode"] == config["mode"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
