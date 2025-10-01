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
    def mock_vibe_check_result(self):
        """Mock vibe check result for testing"""
        return VibeCheckResult(
            vibe_level=VibeLevel.BAD_VIBES,
            overall_vibe="🚨 Bad Vibes",
            friendly_summary="This looks like infrastructure without implementation",
            coaching_recommendations=[
                "Start with basic API calls",
                "Use official SDK instead of custom server",
                "Prove functionality before building architecture",
            ],
            technical_analysis={
                "detected_patterns": [
                    {
                        "type": "infrastructure_without_implementation",
                        "confidence": 0.85,
                        "detected": True,
                        "evidence": ["custom server", "instead of SDK"],
                    }
                ],
                "integration_analysis": {
                    "third_party_services": ["api"],
                    "infrastructure_keywords": ["server"],
                    "complexity_indicators": [],
                },
                "analysis_metadata": {
                    "claude_analysis_available": False,
                    "clear_thought_analysis_available": False,
                    "detail_level": "standard",
                },
            },
            claude_reasoning=None,
            clear_thought_analysis=None,
        )

    @patch("vibe_check.tools.analyze_issue.get_vibe_check_framework")
    def test_analyze_issue_quick_mode(self, mock_get_framework, mock_vibe_check_result):
        """Test analyze_issue MCP tool in quick mode"""
        # Setup mock framework
        mock_framework = MagicMock()
        mock_framework.check_issue_vibes.return_value = mock_vibe_check_result
        mock_get_framework.return_value = mock_framework

        result = analyze_issue(
            issue_number=42,
            repository="test/repo",
            analysis_mode="quick",
            detail_level="brief",
            post_comment=False,
        )

        # Verify framework call
        mock_framework.check_issue_vibes.assert_called_once_with(
            issue_number=42,
            repository="test/repo",
            mode=VibeCheckMode.QUICK,
            detail_level=DetailLevel.BRIEF,
            post_comment=False,
        )

        # Verify response structure
        assert result["status"] == "vibe_check_complete"
        assert "analysis_timestamp" in result
        assert "vibe_check" in result
        assert "issue_info" in result
        assert "technical_analysis" in result
        assert "enhanced_features" in result
        assert "analysis_metadata" in result

        # Verify vibe check content
        vibe_check = result["vibe_check"]
        assert vibe_check["overall_vibe"] == "🚨 Bad Vibes"
        assert vibe_check["vibe_level"] == "bad_vibes"
        assert "infrastructure without implementation" in vibe_check["friendly_summary"]
        assert len(vibe_check["coaching_recommendations"]) == 3

        # Verify issue info
        issue_info = result["issue_info"]
        assert issue_info["number"] == 42
        assert issue_info["repository"] == "test/repo"
        assert issue_info["analysis_mode"] == "quick"
        assert issue_info["detail_level"] == "brief"
        assert issue_info["comment_posted"] == False

        # Verify enhanced features
        features = result["enhanced_features"]
        assert features["claude_reasoning"] == False
        assert features["clear_thought_analysis"] == False
        assert features["comprehensive_validation"] == False
        assert features["educational_coaching"] == True
        assert features["friendly_language"] == True

    @patch("vibe_check.tools.analyze_issue.get_vibe_check_framework")
    def test_analyze_issue_comprehensive_mode(
        self, mock_get_framework, mock_vibe_check_result
    ):
        """Test analyze_issue MCP tool in comprehensive mode"""
        # Setup mock framework with enhanced features
        mock_vibe_check_result.claude_reasoning = "Claude analysis available"
        mock_vibe_check_result.clear_thought_analysis = {"type": "systematic_analysis"}

        mock_framework = MagicMock()
        mock_framework.check_issue_vibes.return_value = mock_vibe_check_result
        mock_get_framework.return_value = mock_framework

        result = analyze_issue(
            issue_number=123,
            repository="owner/repo",
            analysis_mode="comprehensive",
            detail_level="comprehensive",
            post_comment=True,
        )

        # Verify framework call
        mock_framework.check_issue_vibes.assert_called_once_with(
            issue_number=123,
            repository="owner/repo",
            mode=VibeCheckMode.COMPREHENSIVE,
            detail_level=DetailLevel.COMPREHENSIVE,
            post_comment=True,
        )

        # Verify comprehensive features
        features = result["enhanced_features"]
        assert features["claude_reasoning"] == True
        assert features["clear_thought_analysis"] == True
        assert features["comprehensive_validation"] == True

        # Verify issue info
        issue_info = result["issue_info"]
        assert issue_info["analysis_mode"] == "comprehensive"
        assert issue_info["detail_level"] == "comprehensive"
        assert issue_info["comment_posted"] == True

    @patch("vibe_check.tools.analyze_issue.get_vibe_check_framework")
    def test_analyze_issue_default_parameters(
        self, mock_get_framework, mock_vibe_check_result
    ):
        """Test analyze_issue with default parameters"""
        mock_framework = MagicMock()
        mock_framework.check_issue_vibes.return_value = mock_vibe_check_result
        mock_get_framework.return_value = mock_framework

        result = analyze_issue(issue_number=42)

        # Verify defaults
        mock_framework.check_issue_vibes.assert_called_once_with(
            issue_number=42,
            repository=None,
            mode=VibeCheckMode.QUICK,
            detail_level=DetailLevel.STANDARD,
            post_comment=False,
        )

        # Verify default repository in response
        assert result["issue_info"]["repository"] == "kesslerio/vibe-check-mcp"
        assert result["issue_info"]["analysis_mode"] == "quick"
        assert result["issue_info"]["detail_level"] == "standard"

    @patch("vibe_check.tools.analyze_issue.get_vibe_check_framework")
    def test_analyze_issue_invalid_detail_level(
        self, mock_get_framework, mock_vibe_check_result
    ):
        """Test analyze_issue with invalid detail level"""
        mock_framework = MagicMock()
        mock_framework.check_issue_vibes.return_value = mock_vibe_check_result
        mock_get_framework.return_value = mock_framework

        result = analyze_issue(issue_number=42, detail_level="invalid_level")

        # Should use standard as default
        mock_framework.check_issue_vibes.assert_called_once()
        call_args = mock_framework.check_issue_vibes.call_args[1]
        assert call_args["detail_level"] == DetailLevel.STANDARD

    @patch("vibe_check.tools.analyze_issue.get_vibe_check_framework")
    def test_analyze_issue_error_handling(self, mock_get_framework):
        """Test analyze_issue error handling"""
        mock_framework = MagicMock()
        mock_framework.check_issue_vibes.side_effect = Exception("Framework error")
        mock_get_framework.return_value = mock_framework

        result = analyze_issue(issue_number=42)

        # Verify error response
        assert result["status"] == "vibe_check_error"
        assert "Framework error" in result["error"]
        assert result["issue_number"] == 42
        assert "friendly_error" in result
        assert "🚨 Oops!" in result["friendly_error"]

    def test_analyze_issue_parameter_validation_comprehensive_mode(self):
        """Test parameter combinations for comprehensive mode"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = VibeCheckResult(
                vibe_level=VibeLevel.GOOD_VIBES,
                overall_vibe="✅ Good Vibes",
                friendly_summary="Test",
                coaching_recommendations=[],
                technical_analysis={},
                claude_reasoning="Test reasoning",
                clear_thought_analysis={"test": "data"},
            )
            mock_get_framework.return_value = mock_framework

            # Test comprehensive mode defaults
            result = analyze_issue(issue_number=42, analysis_mode="comprehensive")

            # Should auto-enable comment posting in comprehensive mode
            call_args = mock_framework.check_issue_vibes.call_args[1]
            assert call_args["mode"] == VibeCheckMode.COMPREHENSIVE
            assert call_args["detail_level"] == DetailLevel.STANDARD

    def test_analyze_issue_response_structure_validation(self):
        """Test that response structure matches MCP tool requirements"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            mock_result = VibeCheckResult(
                vibe_level=VibeLevel.RESEARCH_NEEDED,
                overall_vibe="🤔 Research Needed",
                friendly_summary="Needs more investigation",
                coaching_recommendations=["Do research first"],
                technical_analysis={"test": "data"},
                claude_reasoning=None,
                clear_thought_analysis=None,
            )

            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = mock_result
            mock_get_framework.return_value = mock_framework

            result = analyze_issue(issue_number=42)

            # Verify all required fields are present
            required_fields = [
                "status",
                "analysis_timestamp",
                "vibe_check",
                "issue_info",
                "technical_analysis",
                "enhanced_features",
                "analysis_metadata",
            ]

            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

            # Verify vibe_check structure
            vibe_check = result["vibe_check"]
            vibe_check_fields = [
                "overall_vibe",
                "vibe_level",
                "friendly_summary",
                "coaching_recommendations",
            ]

            for field in vibe_check_fields:
                assert field in vibe_check, f"Missing vibe_check field: {field}"

            # Verify issue_info structure
            issue_info = result["issue_info"]
            issue_info_fields = [
                "number",
                "repository",
                "analysis_mode",
                "detail_level",
                "comment_posted",
            ]

            for field in issue_info_fields:
                assert field in issue_info, f"Missing issue_info field: {field}"

    def test_analyze_issue_mode_conversion(self):
        """Test proper conversion between string and enum modes"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = VibeCheckResult(
                vibe_level=VibeLevel.GOOD_VIBES,
                overall_vibe="✅ Good Vibes",
                friendly_summary="Test",
                coaching_recommendations=[],
                technical_analysis={},
                claude_reasoning=None,
                clear_thought_analysis=None,
            )
            mock_get_framework.return_value = mock_framework

            # Test string to enum conversion
            test_cases = [
                ("quick", VibeCheckMode.QUICK),
                ("comprehensive", VibeCheckMode.COMPREHENSIVE),
                ("invalid", VibeCheckMode.QUICK),  # Should default to QUICK
            ]

            for string_mode, expected_enum in test_cases:
                analyze_issue(issue_number=42, analysis_mode=string_mode)
                call_args = mock_framework.check_issue_vibes.call_args[1]
                assert call_args["mode"] == expected_enum

    def test_analyze_issue_detail_level_conversion(self):
        """Test proper conversion between string and enum detail levels"""
        with patch(
            "vibe_check.tools.analyze_issue.get_vibe_check_framework"
        ) as mock_get_framework:
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = VibeCheckResult(
                vibe_level=VibeLevel.GOOD_VIBES,
                overall_vibe="✅ Good Vibes",
                friendly_summary="Test",
                coaching_recommendations=[],
                technical_analysis={},
                claude_reasoning=None,
                clear_thought_analysis=None,
            )
            mock_get_framework.return_value = mock_framework

            # Test string to enum conversion
            test_cases = [
                ("brief", DetailLevel.BRIEF),
                ("standard", DetailLevel.STANDARD),
                ("comprehensive", DetailLevel.COMPREHENSIVE),
                ("invalid", DetailLevel.STANDARD),  # Should default to STANDARD
            ]

            for string_level, expected_enum in test_cases:
                analyze_issue(issue_number=42, detail_level=string_level)
                call_args = mock_framework.check_issue_vibes.call_args[1]
                assert call_args["detail_level"] == expected_enum


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
