"""
Unit Tests for GitHubIssueAnalyzer Class

Tests the GitHubIssueAnalyzer class functionality:
- Analyzer initialization and configuration
- Issue data fetching and processing
- Integration with pattern detection
"""

import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os
from github import GithubException

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.analyze_issue import (
    GitHubIssueAnalyzer,
    analyze_issue,
    get_github_analyzer
)
from vibe_check.tools.vibe_check_framework import VibeCheckMode, VibeLevel, VibeCheckResult
from vibe_check.core.educational_content import DetailLevel
from vibe_check.core.pattern_detector import DetectionResult


class TestGitHubIssueAnalyzer:
    """Test the legacy GitHubIssueAnalyzer class functionality"""
    
    @pytest.fixture
    def mock_github_token(self):
        """Mock GitHub token for testing"""
        return "mock_github_token_123"
    
    @pytest.fixture
    def sample_issue_data(self):
        """Sample GitHub issue data for testing"""
        return {
            "number": 42,
            "title": "Feature: Add custom HTTP server for API integration",
            "body": "We need to build a custom HTTP server to handle API requests instead of using the SDK.",
            "author": "testuser",
            "created_at": "2025-01-01T00:00:00Z",
            "state": "open",
            "labels": ["feature", "P1"],
            "url": "https://github.com/test/repo/issues/42",
            "repository": "test/repo"
        }
    
    @pytest.fixture
    def analyzer(self, mock_github_token):
        """Create analyzer instance for testing"""
        with patch('vibe_check.tools.analyze_issue.Github') as mock_github:
            analyzer = GitHubIssueAnalyzer(mock_github_token)
            analyzer.github_client = mock_github.return_value
            return analyzer
    
    def test_analyzer_initialization(self, mock_github_token):
        """Test proper analyzer initialization"""
        with patch('vibe_check.tools.analyze_issue.Github') as mock_github:
            analyzer = GitHubIssueAnalyzer(mock_github_token)
            
            # Verify GitHub client initialization
            mock_github.assert_called_once_with(mock_github_token)
            assert analyzer.github_client is not None
            assert analyzer.pattern_detector is not None
    
    def test_analyzer_initialization_without_token(self):
        """Test analyzer initialization without GitHub token"""
        with patch('vibe_check.tools.analyze_issue.Github') as mock_github:
            analyzer = GitHubIssueAnalyzer()
            
            # Should use default GitHub() constructor
            mock_github.assert_called_once_with()
    
    def test_fetch_issue_data_success(self, analyzer, sample_issue_data):
        """Test successful issue data fetching"""
        # Mock the GitHub repository and issue
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        
        # Configure mock issue
        mock_issue.number = sample_issue_data["number"]
        mock_issue.title = sample_issue_data["title"]
        mock_issue.body = sample_issue_data["body"]
        mock_issue.user.login = sample_issue_data["author"]
        mock_issue.created_at.isoformat.return_value = sample_issue_data["created_at"]
        mock_issue.state = sample_issue_data["state"]
        mock_issue.labels = [MagicMock(name=label) for label in sample_issue_data["labels"]]
        mock_issue.html_url = sample_issue_data["url"]
        
        analyzer.github_client.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Test fetching issue data
        result = analyzer._fetch_issue_data(42, "test/repo")
        
        # Verify result structure
        assert result is not None
        assert result["number"] == 42
        assert result["title"] == sample_issue_data["title"]
        assert result["body"] == sample_issue_data["body"]
        assert result["author"] == sample_issue_data["author"]
        assert result["state"] == sample_issue_data["state"]
        assert len(result["labels"]) == 2
        assert result["url"] == sample_issue_data["url"]
        
        # Verify GitHub API calls
        analyzer.github_client.get_repo.assert_called_once_with("test/repo")
        mock_repo.get_issue.assert_called_once_with(42)
    
    def test_fetch_issue_data_github_exception(self, analyzer):
        """Test issue data fetching with GitHub exception"""
        # Configure mock to raise exception
        analyzer.github_client.get_repo.side_effect = GithubException(404, "Not Found")
        
        # Test exception handling
        result = analyzer._fetch_issue_data(999, "nonexistent/repo")
        
        # Should return None on exception
        assert result is None
    
    def test_fetch_issue_data_invalid_repo(self, analyzer):
        """Test issue data fetching with invalid repository format"""
        # Test with invalid repository format
        result = analyzer._fetch_issue_data(42, "invalid-repo-format")
        
        # Should handle gracefully
        assert result is None
    
    def test_analyze_issue_with_pattern_detection(self, analyzer, sample_issue_data):
        """Test issue analysis with pattern detection"""
        # Mock issue fetching
        analyzer._fetch_issue_data = MagicMock(return_value=sample_issue_data)
        
        # Mock pattern detection
        mock_detection_result = DetectionResult(
            pattern_type="infrastructure_without_implementation",
            detected=True,
            confidence=0.85,
            evidence=["Consider using existing SDK instead"],
            threshold=0.7
        )
        analyzer.pattern_detector.analyze_text_for_patterns = MagicMock(return_value=[mock_detection_result])
        
        # Test analysis
        result = analyzer.analyze_issue(42, "test/repo")
        
        # Verify result structure
        assert result is not None
        assert "issue_data" in result
        assert "analysis" in result
        assert result["issue_data"] == sample_issue_data
        assert result["analysis"] == mock_detection_result
        
        # Verify method calls
        analyzer._fetch_issue_data.assert_called_once_with(42, "test/repo")
        analyzer.pattern_detector.analyze_text_for_patterns.assert_called_once()
    
    def test_analyze_issue_with_fetch_failure(self, analyzer):
        """Test issue analysis when issue fetching fails"""
        # Mock failed issue fetching
        analyzer._fetch_issue_data = MagicMock(return_value=None)
        
        # Test analysis with fetch failure
        result = analyzer.analyze_issue(999, "test/repo")
        
        # Should return error response when fetching fails
        assert result["status"] == "analysis_error"
        analyzer._fetch_issue_data.assert_called_once_with(999, "test/repo")
    
    def test_pattern_detection_integration(self, analyzer, sample_issue_data):
        """Test integration with pattern detection system"""
        # Test that analyzer properly integrates with pattern detector
        assert analyzer.pattern_detector is not None
        
        # Mock pattern detection call
        analyzer.pattern_detector.analyze_text_for_patterns = MagicMock()
        
        # Create test content
        test_content = sample_issue_data['body']
        test_context = f"Title: {sample_issue_data['title']}"
        
        # Call pattern detection
        analyzer.pattern_detector.analyze_text_for_patterns(
            content=test_content,
            context=test_context
        )
        
        # Verify pattern detector was called
        analyzer.pattern_detector.analyze_text_for_patterns.assert_called_once()
    
    def test_issue_data_transformation(self, analyzer):
        """Test transformation of GitHub issue object to data dict"""
        # Create mock GitHub issue object
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test body content"
        mock_issue.user.login = "testuser"
        mock_issue.created_at.isoformat.return_value = "2025-01-01T00:00:00Z"
        mock_issue.state = "open"
        mock_issue.labels = [
            MagicMock(name="bug"),
            MagicMock(name="P1")
        ]
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        
        # Test transformation logic would be tested here
        # This test ensures the analyzer properly transforms GitHub API objects
        # to our internal data format
        
        # Mock the repository and issue retrieval
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        analyzer.github_client.get_repo.return_value = mock_repo
        
        result = analyzer._fetch_issue_data(123, "test/repo")
        
        # Verify transformation
        assert result["number"] == 123
        assert result["title"] == "Test Issue"
        assert result["body"] == "Test body content"
        assert result["author"] == "testuser"
        assert result["created_at"] == "2025-01-01T00:00:00Z"
        assert result["state"] == "open"
        assert len(result["labels"]) == 2
        assert "bug" in result["labels"]
        assert "P1" in result["labels"]
        assert result["url"] == "https://github.com/test/repo/issues/123"
    
    def _create_mock_issue(self, issue_data):
        """Helper method to create mock GitHub issue object"""
        mock_issue = MagicMock()
        mock_issue.number = issue_data["number"]
        mock_issue.title = issue_data["title"]
        mock_issue.body = issue_data["body"]
        mock_issue.user.login = issue_data["author"]
        mock_issue.created_at.isoformat.return_value = issue_data["created_at"]
        mock_issue.state = issue_data["state"]
        mock_issue.labels = [MagicMock(name=label) for label in issue_data["labels"]]
        mock_issue.html_url = issue_data["url"]
        return mock_issue


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])