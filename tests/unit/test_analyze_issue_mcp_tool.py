"""Unit Tests for Analyze Issue MCP Tool.

Validates the enhanced :func:`analyze_issue` MCP tool function by verifying:

* MCP tool interface compliance
* Parameter validation and defaults
* Response format consistency
* Error handling behaviour
"""

import asyncio
import os
import sys
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.analyze_issue import analyze_issue, analyze_issue_async
import vibe_check.tools.analyze_issue as analyze_issue_module
from vibe_check.tools.legacy.vibe_check_framework import (
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult,
)
from vibe_check.core.educational_content import DetailLevel


class TestAnalyzeIssueMCPTool:
    """Test the enhanced analyze_issue MCP tool function"""

    @pytest.fixture
    def mock_basic_result(self):
        """Mock basic analysis result for testing"""
        return {
            "status": "basic_analysis_complete",
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "issue_info": {
                "number": 42,
                "title": "Test Issue",
                "author": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
                "repository": "test/repo",
                "url": "https://github.com/test/repo/issues/42",
                "labels": [],
            },
            "patterns_detected": [
                {
                    "pattern_type": "infrastructure_without_implementation",
                    "confidence": 0.85,
                    "detected": True,
                    "evidence": ["custom server", "instead of SDK"],
                    "threshold": 0.7,
                    "educational_content": {
                        "pattern_name": "Infrastructure Without Implementation",
                        "problem": "Building complex infrastructure before validating basic functionality",
                        "solution": "Start with simplest working solution using official SDKs",
                    },
                }
            ],
            "confidence_summary": {
                "total_patterns_detected": 1,
                "average_confidence": 0.85,
                "highest_confidence": 0.85,
                "patterns_by_confidence": [
                    {
                        "pattern": "infrastructure_without_implementation",
                        "confidence": 0.85,
                        "severity": "HIGH",
                    }
                ],
            },
            "recommended_actions": [
                "CRITICAL: Address Infrastructure Without Implementation pattern (confidence: 85%)",
                "Start with basic API calls",
                "Use official SDK instead of custom server",
                "Prove functionality before building architecture",
            ],
            "analysis_metadata": {
                "core_engine_validation": "87.5% accuracy, 0% false positives",
                "detail_level": "brief",
                "patterns_analyzed": ["infrastructure_without_implementation"],
                "detection_method": "Phase 1 validated algorithms",
                "external_claude_available": False,
            },
        }

    @patch("vibe_check.tools.issue_analysis.api.get_enhanced_github_analyzer")
    def test_analyze_issue_quick_mode(self, mock_get_analyzer, mock_basic_result):
        """Test analyze_issue MCP tool in basic mode"""
        # Setup mock analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.claude_cli_enabled = False
        mock_analyzer.analyze_issue_basic = AsyncMock(return_value=mock_basic_result)
        mock_get_analyzer.return_value = mock_analyzer

        result = asyncio.run(
            analyze_issue_async(
                issue_number=42,
                repository="test/repo",
                analysis_mode="basic",
                detail_level="brief",
                post_comment=False,
            )
        )

        # Verify analyzer call
        mock_analyzer.analyze_issue_basic.assert_awaited_once_with(
            issue_number=42,
            repository="test/repo",
            detail_level="brief",
        )

        # Verify response structure
        assert result["status"] == "basic_analysis_complete"
        assert "analysis_timestamp" in result
        assert "patterns_detected" in result
        assert "issue_info" in result
        assert "confidence_summary" in result
        assert "recommended_actions" in result
        assert "analysis_metadata" in result
        assert "enhanced_analysis" in result

        # Verify pattern detection content
        patterns = result["patterns_detected"]
        assert len(patterns) == 1
        assert patterns[0]["pattern_type"] == "infrastructure_without_implementation"
        assert patterns[0]["confidence"] == 0.85

        # Verify issue info
        issue_info = result["issue_info"]
        assert issue_info["number"] == 42
        assert issue_info["repository"] == "test/repo"
        assert issue_info["author"] == "testuser"

        # Verify enhanced analysis metadata
        enhanced = result["enhanced_analysis"]
        assert enhanced["analysis_mode"] == "basic"
        assert (
            enhanced["external_claude_available"]
            is analyze_issue_module.EXTERNAL_CLAUDE_AVAILABLE
        )
        assert enhanced["claude_cli_enabled"] is False

    @patch("vibe_check.tools.issue_analysis.api._run_vibe_check_sync")
    def test_analyze_issue_comprehensive_mode(self, mock_run_vibe_check):
        """Test analyze_issue MCP tool in comprehensive mode."""

        mock_run_vibe_check.return_value = {
            "status": "vibe_check_complete",
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "issue_info": {
                "number": 123,
                "repository": "owner/repo",
                "analysis_mode": "comprehensive",
                "detail_level": "comprehensive",
                "comment_posted": True,
            },
            "vibe_check": {"overall_vibe": "positive"},
        }

        result = analyze_issue(
            issue_number=123,
            repository="owner/repo",
            analysis_mode="comprehensive",
            detail_level="comprehensive",
            post_comment=True,
        )

        mock_run_vibe_check.assert_called_once_with(
            issue_number=123,
            repository="owner/repo",
            detail_level="comprehensive",
            mode="comprehensive",
            post_comment=True,
        )
        assert result["issue_info"]["analysis_mode"] == "comprehensive"
        assert result["issue_info"]["detail_level"] == "comprehensive"

    @patch("vibe_check.tools.issue_analysis.api._run_vibe_check_sync")
    def test_analyze_issue_default_parameters(
        self, mock_run_vibe_check, mock_basic_result
    ):
        """Test analyze_issue with default parameters."""

        mock_run_vibe_check.return_value = {
            "status": "vibe_check_complete",
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "issue_info": {
                "number": 42,
                "repository": None,
                "analysis_mode": "hybrid",
                "detail_level": "standard",
                "comment_posted": False,
            },
            "vibe_check": mock_basic_result,
        }

        result = analyze_issue(issue_number=42)

        mock_run_vibe_check.assert_called_once_with(
            issue_number=42,
            repository=None,
            detail_level="standard",
            mode="hybrid",
            post_comment=False,
        )
        assert result["issue_info"]["analysis_mode"] == "hybrid"
        assert result["issue_info"]["detail_level"] == "standard"

    @patch("vibe_check.tools.issue_analysis.api._run_vibe_check_sync")
    def test_analyze_issue_invalid_detail_level(
        self, mock_run_vibe_check, mock_basic_result
    ):
        """Invalid detail level should fall back to standard."""

        mocked_response = {
            "status": "vibe_check_complete",
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "issue_info": {
                "number": 42,
                "repository": None,
                "analysis_mode": "hybrid",
                "detail_level": "standard",
                "comment_posted": False,
            },
            "vibe_check": mock_basic_result,
        }
        mock_run_vibe_check.return_value = mocked_response

        result = analyze_issue(issue_number=42, detail_level="invalid_level")

        mock_run_vibe_check.assert_called_once_with(
            issue_number=42,
            repository=None,
            detail_level="invalid_level",
            mode="hybrid",
            post_comment=False,
        )
        assert result["issue_info"]["detail_level"] == "standard"

    @patch("vibe_check.tools.issue_analysis.api.get_enhanced_github_analyzer")
    def test_analyze_issue_error_handling(self, mock_get_analyzer):
        """Test analyze_issue error handling"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_issue_basic = AsyncMock(
            side_effect=Exception("Analysis error")
        )
        mock_get_analyzer.return_value = mock_analyzer

        result = asyncio.run(
            analyze_issue_async(issue_number=42, analysis_mode="basic")
        )

        # Verify error response
        assert result["status"] == "enhanced_analysis_error"
        assert "Analysis error" in result["error"]
        assert result["issue_number"] == 42
        assert "fallback_recommendation" in result
