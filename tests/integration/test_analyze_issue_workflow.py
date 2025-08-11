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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.analyze_issue import (
    GitHubIssueAnalyzer,
    analyze_issue
)
from vibe_check.tools.legacy.vibe_check_framework import VibeCheckMode, VibeLevel, VibeCheckResult
from vibe_check.core.educational_content import DetailLevel


class TestAnalyzeIssueIntegrationWorkflow:
    """Integration tests for complete analyze_issue workflow"""
    
    @pytest.mark.integration
    def test_end_to_end_analyze_issue_workflow(self):
        """Test complete end-to-end analyze_issue workflow"""
        with patch('vibe_check.tools.analyze_issue.get_vibe_check_framework') as mock_get_framework:
            # Setup comprehensive mock vibe check result
            vibe_result = VibeCheckResult(
                vibe_level=VibeLevel.NEEDS_POC,
                overall_vibe="🧪 POC Vibes",
                friendly_summary="Let's prove this works with real data first!",
                coaching_recommendations=[
                    "Create a minimal proof-of-concept",
                    "Test with real API data",
                    "Document what works and what doesn't"
                ],
                technical_analysis={
                    "detected_patterns": [
                        {
                            "type": "infrastructure_without_implementation",
                            "confidence": 0.7,
                            "detected": True,
                            "evidence": ["custom integration", "no POC mentioned"]
                        }
                    ],
                    "integration_analysis": {
                        "third_party_services": ["api", "integration"],
                        "infrastructure_keywords": ["server", "architecture"],
                        "complexity_indicators": ["sophisticated"]
                    },
                    "analysis_metadata": {
                        "claude_analysis_available": True,
                        "clear_thought_analysis_available": True,
                        "detail_level": "standard"
                    }
                },
                claude_reasoning="Claude suggests starting with basic API integration",
                clear_thought_analysis={
                    "recommended_tools": [
                        {
                            "tool": "mcp__clear-thought-server__mentalmodel",
                            "reasoning": "First principles analysis needed"
                        }
                    ]
                }
            )
            
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = vibe_result
            mock_get_framework.return_value = mock_framework
            
            # Run comprehensive analyze_issue
            result = analyze_issue(
                issue_number=123,
                repository="test/integration-repo",
                analysis_mode="comprehensive",
                detail_level="comprehensive",
                post_comment=True
            )
            
            # Verify comprehensive workflow execution
            mock_framework.check_issue_vibes.assert_called_once_with(
                issue_number=123,
                repository="test/integration-repo",
                mode=VibeCheckMode.COMPREHENSIVE,
                detail_level=DetailLevel.COMPREHENSIVE,
                post_comment=True
            )
            
            # Verify complete response structure
            assert result["status"] == "vibe_check_complete"
            assert "analysis_timestamp" in result
            
            # Verify vibe check results
            vibe_check = result["vibe_check"]
            assert vibe_check["overall_vibe"] == "🧪 POC Vibes"
            assert vibe_check["vibe_level"] == "needs_poc"
            assert "prove this works" in vibe_check["friendly_summary"]
            assert len(vibe_check["coaching_recommendations"]) == 3
            
            # Verify issue information
            issue_info = result["issue_info"]
            assert issue_info["number"] == 123
            assert issue_info["repository"] == "test/integration-repo"
            assert issue_info["analysis_mode"] == "comprehensive"
            assert issue_info["detail_level"] == "comprehensive"
            assert issue_info["comment_posted"] == True
            
            # Verify technical analysis
            tech_analysis = result["technical_analysis"]
            assert "detected_patterns" in tech_analysis
            assert "integration_analysis" in tech_analysis
            assert "analysis_metadata" in tech_analysis
            
            patterns = tech_analysis["detected_patterns"]
            assert len(patterns) == 1
            assert patterns[0]["type"] == "infrastructure_without_implementation"
            assert patterns[0]["confidence"] == 0.7
            
            # Verify enhanced features
            features = result["enhanced_features"]
            assert features["claude_reasoning"] == True
            assert features["clear_thought_analysis"] == True
            assert features["comprehensive_validation"] == True
            assert features["educational_coaching"] == True
            assert features["friendly_language"] == True
            
            # Verify analysis metadata
            metadata = result["analysis_metadata"]
            assert metadata["framework_version"] == "2.0 - Claude-powered vibe check"
            assert "87.5% accuracy" in metadata["core_engine_validation"]
            assert metadata["analysis_type"] == "comprehensive_vibe_check"
            assert metadata["language_style"] == "friendly_coaching"
    
    @pytest.mark.integration 
    def test_legacy_analyzer_to_enhanced_tool_transition(self):
        """Test transition from legacy analyzer to enhanced MCP tool"""
        with patch('vibe_check.tools.analyze_issue.Github') as mock_github:
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
            with patch.object(analyzer.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = []
                
                # Test legacy analyzer
                legacy_result = analyzer.analyze_issue(42, "test/repo")
                
                # Verify legacy response format
                assert legacy_result["status"] == "analysis_complete"
                assert "issue_info" in legacy_result
                assert "patterns_detected" in legacy_result
                assert "analysis_metadata" in legacy_result
                
                # Test enhanced MCP tool
                with patch('vibe_check.tools.analyze_issue.get_vibe_check_framework') as mock_get_framework:
                    mock_framework = MagicMock()
                    mock_framework.check_issue_vibes.return_value = VibeCheckResult(
                        vibe_level=VibeLevel.GOOD_VIBES,
                        overall_vibe="✅ Good Vibes",
                        friendly_summary="Legacy transition test",
                        coaching_recommendations=[],
                        technical_analysis={}
                    )
                    mock_get_framework.return_value = mock_framework
                    
                    enhanced_result = analyze_issue(42, "test/repo")
                    
                    # Verify enhanced response format
                    assert enhanced_result["status"] == "vibe_check_complete"
                    assert "vibe_check" in enhanced_result
                    assert "enhanced_features" in enhanced_result
                    assert enhanced_result["analysis_metadata"]["framework_version"] == "2.0 - Claude-powered vibe check"
                    
                    # Both should work independently
                    assert legacy_result["status"] != enhanced_result["status"]  # Different response formats
                    assert "vibe_check" not in legacy_result  # Legacy doesn't have vibe check
                    assert "enhanced_features" not in legacy_result  # Legacy doesn't have enhanced features
    
    @pytest.mark.integration
    def test_workflow_error_handling_and_recovery(self):
        """Test error handling and recovery in the integration workflow"""
        with patch('vibe_check.tools.analyze_issue.get_vibe_check_framework') as mock_get_framework:
            # Test framework failure
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.side_effect = Exception("Framework unavailable")
            mock_get_framework.return_value = mock_framework
            
            result = analyze_issue(issue_number=42)
            
            # Should handle error gracefully
            assert result["status"] == "vibe_check_error"
            assert "Framework unavailable" in result["error"]
            assert "friendly_error" in result
            assert "🚨 Oops!" in result["friendly_error"]
    
    @pytest.mark.integration
    def test_workflow_with_different_configurations(self):
        """Test workflow with different configuration combinations"""
        with patch('vibe_check.tools.analyze_issue.get_vibe_check_framework') as mock_get_framework:
            mock_framework = MagicMock()
            
            # Test configuration combinations
            test_configs = [
                {
                    "mode": "quick",
                    "detail": "brief",
                    "comment": False,
                    "expected_vibe": VibeLevel.GOOD_VIBES
                },
                {
                    "mode": "comprehensive", 
                    "detail": "comprehensive",
                    "comment": True,
                    "expected_vibe": VibeLevel.COMPLEX_PROJECT
                }
            ]
            
            for config in test_configs:
                # Setup mock result
                mock_result = VibeCheckResult(
                    vibe_level=config["expected_vibe"],
                    overall_vibe="Test Vibe",
                    friendly_summary="Test summary",
                    coaching_recommendations=["Test recommendation"],
                    technical_analysis={"test": "data"}
                )
                mock_framework.check_issue_vibes.return_value = mock_result
                mock_get_framework.return_value = mock_framework
                
                # Test configuration
                result = analyze_issue(
                    issue_number=42,
                    analysis_mode=config["mode"],
                    detail_level=config["detail"],
                    post_comment=config["comment"]
                )
                
                # Verify configuration was applied
                assert result["issue_info"]["analysis_mode"] == config["mode"]
                assert result["issue_info"]["detail_level"] == config["detail"]
                assert result["issue_info"]["comment_posted"] == config["comment"]
                
                # Verify framework was called correctly
                call_args = mock_framework.check_issue_vibes.call_args[1]
                assert call_args["mode"].value.lower() == config["mode"]
                assert call_args["post_comment"] == config["comment"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])