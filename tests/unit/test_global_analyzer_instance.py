"""
Unit Tests for Global Analyzer Instance Management

Tests the global analyzer instance functionality:
- Singleton pattern implementation
- Token management
- Instance reuse and isolation
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.analyze_issue import get_github_analyzer
import vibe_check.tools.analyze_issue as analyze_issue_module
import vibe_check.tools.issue_analysis.api as issue_analysis_api


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton cache before each test"""
    analyze_issue_module._enhanced_github_analyzer = None
    issue_analysis_api._enhanced_github_analyzer = None
    yield
    analyze_issue_module._enhanced_github_analyzer = None
    issue_analysis_api._enhanced_github_analyzer = None


class TestGlobalAnalyzerInstance:
    """Test global analyzer instance management"""

    def test_get_github_analyzer_singleton(self):
        """Test that get_github_analyzer returns singleton instance"""
        with patch(
            "vibe_check.tools.issue_analysis.api.EnhancedGitHubIssueAnalyzer"
        ) as mock_analyzer_class:
            mock_instance = MagicMock()
            mock_analyzer_class.return_value = mock_instance

            # First call
            analyzer1 = get_github_analyzer()
            # Second call
            analyzer2 = get_github_analyzer()

            # Should return same instance
            assert analyzer1 is analyzer2
            # Should only create instance once
            mock_analyzer_class.assert_called_once()

    def test_get_github_analyzer_with_token(self):
        """Test get_github_analyzer with specific token on first call"""
        with patch(
            "vibe_check.tools.issue_analysis.api.EnhancedGitHubIssueAnalyzer"
        ) as mock_analyzer_class:
            mock_instance = MagicMock()
            mock_analyzer_class.return_value = mock_instance

            # Call with specific token
            analyzer = get_github_analyzer("custom_token")

            # Should create new instance with token
            mock_analyzer_class.assert_called_once_with("custom_token", False)
            assert analyzer is mock_instance

    def test_get_github_analyzer_token_override(self):
        """Test that providing token on subsequent calls is ignored due to caching"""
        with patch(
            "vibe_check.tools.issue_analysis.api.EnhancedGitHubIssueAnalyzer"
        ) as mock_analyzer_class:
            mock_instance = MagicMock()
            mock_analyzer_class.return_value = mock_instance

            # First call without token
            analyzer1 = get_github_analyzer()
            # Second call with token
            analyzer2 = get_github_analyzer("token123")

            # Should be the same instance due to singleton caching
            assert analyzer1 is analyzer2
            # Should only call constructor once
            mock_analyzer_class.assert_called_once_with(None, False)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
