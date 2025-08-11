"""
Unit Tests for Vibe Check Framework GitHub Integration

Tests the GitHub integration components:
- Issue comment posting
- GitHub API integration
- Error handling for GitHub operations
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from github import GithubException

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.legacy.vibe_check_framework import (
    VibeCheckFramework,
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult
)
from vibe_check.core.educational_content import DetailLevel


class TestVibeCheckFrameworkGitHubIntegration:
    """Test GitHub integration functionality"""
    
    @pytest.fixture
    def framework(self):
        """Create framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework()
    
    def test_post_vibe_check_comment_success(self, framework):
        """Test successful vibe check comment posting"""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        
        framework.github_client.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Mock vibe check result
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.GOOD_VIBES,
            overall_vibe="✅ Good Vibes",
            friendly_summary="This looks great!",
            coaching_recommendations=["Keep up the good work"],
            technical_analysis={"test": "data"}
        )
        
        # Test comment posting
        success = framework._post_vibe_check_comment(
            "test/repo", 42, vibe_result
        )
        
        # Verify success
        assert success is True
        framework.github_client.get_repo.assert_called_once_with("test/repo")
        mock_repo.get_issue.assert_called_once_with(42)
        mock_issue.create_comment.assert_called_once()
        
        # Verify comment content
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "✅ Good Vibes" in comment_text
        assert "This looks great!" in comment_text
        assert "Keep up the good work" in comment_text
    
    def test_post_vibe_check_comment_github_exception(self, framework):
        """Test vibe check comment posting with GitHub exception"""
        # Mock GitHub API to raise exception
        framework.github_client.get_repo.side_effect = GithubException(404, "Not Found")
        
        # Mock vibe check result
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.BAD_VIBES,
            overall_vibe="🚨 Bad Vibes",
            friendly_summary="Issues detected",
            coaching_recommendations=["Fix the issues"],
            technical_analysis={"test": "data"}
        )
        
        # Test comment posting failure
        success = framework._post_vibe_check_comment(
            "nonexistent/repo", 999, vibe_result
        )
        
        # Should handle failure gracefully
        assert success is False
    
    def test_post_vibe_check_comment_format_bad_vibes(self, framework):
        """Test comment formatting for bad vibes"""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        
        framework.github_client.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Mock bad vibes result
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.BAD_VIBES,
            overall_vibe="🚨 Bad Vibes",
            friendly_summary="Anti-patterns detected",
            coaching_recommendations=[
                "Use existing SDK instead", 
                "Start with proof of concept"
            ],
            technical_analysis={
                "detected_patterns": [
                    {
                        "type": "infrastructure_without_implementation",
                        "confidence": 0.85
                    }
                ]
            }
        )
        
        framework._post_vibe_check_comment("test/repo", 42, vibe_result)
        
        # Verify comment structure for bad vibes
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "🚨 Bad Vibes" in comment_text
        assert "Anti-patterns detected" in comment_text
        assert "Use existing SDK instead" in comment_text
        assert "Start with proof of concept" in comment_text
        assert "infrastructure_without_implementation" in comment_text
    
    def test_post_vibe_check_comment_format_comprehensive(self, framework):
        """Test comment formatting for comprehensive analysis"""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        
        framework.github_client.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Mock comprehensive result
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.NEEDS_POC,
            overall_vibe="🧪 POC Vibes",
            friendly_summary="Needs proof of concept",
            coaching_recommendations=["Build POC first"],
            technical_analysis={"test": "data"},
            claude_reasoning="Claude suggests building POC",
            clear_thought_analysis={"recommended_approach": "POC"}
        )
        
        framework._post_vibe_check_comment("test/repo", 42, vibe_result)
        
        # Verify comprehensive comment content
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "🧪 POC Vibes" in comment_text
        assert "Claude suggests building POC" in comment_text
        assert "recommended_approach" in comment_text
    
    def test_format_vibe_check_comment_structure(self, framework):
        """Test the structure of formatted vibe check comments"""
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.RESEARCH_NEEDED,
            overall_vibe="🤔 Research Needed",
            friendly_summary="More investigation required",
            coaching_recommendations=["Research existing solutions"],
            technical_analysis={"patterns": ["complexity_escalation"]}
        )
        
        comment = framework._format_vibe_check_comment(vibe_result)
        
        # Verify comment structure
        assert comment.startswith("## 🤔 Research Needed")
        assert "More investigation required" in comment
        assert "Research existing solutions" in comment
        assert "complexity_escalation" in comment
        
        # Verify it's properly formatted markdown
        assert "###" in comment  # Should have subsections
        assert "- " in comment   # Should have bullet points
    
    def test_github_api_error_handling(self, framework):
        """Test various GitHub API error scenarios"""
        error_scenarios = [
            (403, "Forbidden"),
            (404, "Not Found"), 
            (422, "Unprocessable Entity"),
            (500, "Internal Server Error")
        ]
        
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.GOOD_VIBES,
            overall_vibe="✅ Good Vibes",
            friendly_summary="Test",
            coaching_recommendations=[],
            technical_analysis={}
        )
        
        for status_code, message in error_scenarios:
            framework.github_client.get_repo.side_effect = GithubException(
                status_code, message
            )
            
            success = framework._post_vibe_check_comment(
                "test/repo", 42, vibe_result
            )
            
            # Should handle all errors gracefully
            assert success is False
    
    def test_github_client_initialization_with_token(self):
        """Test GitHub client initialization with token"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework(github_token="test_token")
            
            mock_github.assert_called_once_with("test_token")
    
    def test_github_client_initialization_without_token(self):
        """Test GitHub client initialization without token"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework()
            
            mock_github.assert_called_once_with()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])