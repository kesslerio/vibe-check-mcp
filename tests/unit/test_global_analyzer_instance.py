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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.analyze_issue import get_github_analyzer


class TestGlobalAnalyzerInstance:
    """Test global analyzer instance management"""
    
    def test_get_github_analyzer_singleton(self):
        """Test that get_github_analyzer returns singleton instance"""
        with patch('vibe_check.tools.analyze_issue.GitHubIssueAnalyzer') as mock_analyzer_class:
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
        """Test get_github_analyzer with specific token"""
        with patch('vibe_check.tools.analyze_issue.GitHubIssueAnalyzer') as mock_analyzer_class:
            mock_instance = MagicMock()
            mock_analyzer_class.return_value = mock_instance
            
            # Call with specific token
            analyzer = get_github_analyzer("custom_token")
            
            # Should create new instance with token
            mock_analyzer_class.assert_called_once_with("custom_token")
            assert analyzer is mock_instance
    
    def test_get_github_analyzer_token_override(self):
        """Test that providing token creates new instance"""
        with patch('vibe_check.tools.analyze_issue.GitHubIssueAnalyzer') as mock_analyzer_class:
            # Create different mock instances
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            mock_analyzer_class.side_effect = [mock_instance1, mock_instance2]
            
            # First call without token
            analyzer1 = get_github_analyzer()
            # Second call with token
            analyzer2 = get_github_analyzer("token123")
            
            # Should be different instances
            assert analyzer1 is not analyzer2
            # Should call constructor twice with different parameters
            assert mock_analyzer_class.call_count == 2
            calls = mock_analyzer_class.call_args_list
            assert calls[0][0] == ()  # No token
            assert calls[1][0] == ("token123",)  # With token


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])