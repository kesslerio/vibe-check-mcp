"""
Unit Tests for Analyze Issue MCP Tool

Tests the enhanced analyze_issue MCP tool function:
- MCP tool interface compliance
- Parameter validation and defaults
- Response format consistency
- Error handling
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

    @patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer")
    def test_analyze_issue_quick_mode(self, mock_get_analyzer, mock_basic_result):
        """Test analyze_issue MCP tool in basic mode"""
        # Setup mock analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.claude_cli_enabled = False
        mock_analyzer.analyze_issue_basic.return_value = mock_basic_result
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_issue(
            issue_number=42,
            repository="test/repo",
            analysis_mode="basic",
            detail_level="brief",
            post_comment=False,
        )

        # Verify analyzer call
        mock_analyzer.analyze_issue_basic.assert_called_once_with(
            issue_number=42,
            repository="test/repo",
            detail_level="brief",
        )

        # Verify response structure
        assert "analysis_results" in result
        analysis_results = result["analysis_results"]
        assert analysis_results["status"] == "basic_analysis_complete"
        assert "analysis_timestamp" in analysis_results
        assert "patterns_detected" in analysis_results
        assert "issue_info" in analysis_results
        assert "confidence_summary" in analysis_results
        assert "recommended_actions" in analysis_results
        assert "analysis_metadata" in analysis_results
        assert "enhanced_analysis" in result

        # Verify pattern detection content
        patterns = analysis_results["patterns_detected"]
        assert len(patterns) == 1
        assert patterns[0]["pattern_type"] == "infrastructure_without_implementation"
        assert patterns[0]["confidence"] == 0.85

        # Verify issue info
        issue_info = analysis_results["issue_info"]
        assert issue_info["number"] == 42
        assert issue_info["repository"] == "test/repo"
        assert issue_info["author"] == "testuser"

        # Verify enhanced analysis metadata
        enhanced = result["enhanced_analysis"]
        assert enhanced["analysis_mode"] == "basic"
        assert enhanced["external_claude_available"] is False
        assert enhanced["claude_cli_enabled"] is False

    @patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer")
    def test_analyze_issue_comprehensive_mode(self, mock_get_analyzer):
        """Test analyze_issue MCP tool in comprehensive mode"""
        # Setup mock analyzer with comprehensive result
        mock_analyzer = MagicMock()
        mock_analyzer.claude_cli_enabled = True
        mock_analyzer.analyze_issue_comprehensive.return_value = {
            "status": "comprehensive_analysis_complete",
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "issue_info": {
                "number": 123,
                "title": "Test Issue",
                "author": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
                "repository": "owner/repo",
                "url": "https://github.com/owner/repo/issues/123",
                "labels": [],
            },
            "comprehensive_analysis": {
                "success": True,
                "claude_output": "Comprehensive analysis content",
                "execution_time_seconds": 2.5,
                "cost_tracking": {"cost_usd": 0.01},
            },
            "enhanced_features": {
                "claude_cli_integration": True,
                "sophisticated_reasoning": True,
            },
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_issue(
            issue_number=123,
            repository="owner/repo",
            analysis_mode="comprehensive",
            detail_level="comprehensive",
            post_comment=True,
        )

        # Verify analyzer call
        mock_analyzer.analyze_issue_comprehensive.assert_called_once_with(
            issue_number=123,
            repository="owner/repo",
            detail_level="comprehensive",
        )

        # Verify comprehensive response structure
        assert "analysis_results" in result
        analysis_results = result["analysis_results"]
        assert analysis_results["status"] == "comprehensive_analysis_complete"
        assert "comprehensive_analysis" in analysis_results
        assert "enhanced_features" in analysis_results
        assert result["enhanced_analysis"]["analysis_mode"] == "comprehensive"

    @patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer")
    def test_analyze_issue_default_parameters(self, mock_get_analyzer, mock_basic_result):
        """Test analyze_issue with default parameters"""
        mock_analyzer = MagicMock()
        mock_analyzer.claude_cli_enabled = False
        mock_analyzer.analyze_issue_basic.return_value = mock_basic_result
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_issue(issue_number=42)

        # Verify defaults - should call hybrid mode which calls basic analysis
        mock_analyzer.analyze_issue_hybrid.assert_called_once_with(
            issue_number=42,
            repository=None,
            detail_level="standard",
        )

        # Verify enhanced analysis metadata
        assert "analysis_results" in result
        enhanced = result["enhanced_analysis"]
        assert enhanced["analysis_mode"] == "hybrid"

    @patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer")
    def test_analyze_issue_invalid_detail_level(self, mock_get_analyzer, mock_basic_result):
        """Test analyze_issue with invalid detail level"""
        mock_analyzer = MagicMock()
        mock_analyzer.claude_cli_enabled = False
        mock_analyzer.analyze_issue_basic.return_value = mock_basic_result
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_issue(issue_number=42, detail_level="invalid_level")

        # Should use standard as default
        mock_analyzer.analyze_issue_hybrid.assert_called_once()
        call_args = mock_analyzer.analyze_issue_hybrid.call_args[1]
        assert call_args["detail_level"] == "standard"
        assert "analysis_results" in result

    @patch("vibe_check.tools.analyze_issue.get_enhanced_github_analyzer")
    def test_analyze_issue_error_handling(self, mock_get_analyzer):
        """Test analyze_issue error handling"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_issue_hybrid.side_effect = Exception("Analysis error")
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_issue(issue_number=42)

        # Verify error response
        assert result["status"] == "enhanced_analysis_error"
        assert "Analysis error" in result["error"]
        assert result["issue_number"] == 42
        assert "fallback_recommendation" in result
