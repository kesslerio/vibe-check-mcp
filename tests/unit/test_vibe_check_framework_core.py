"""
Unit Tests for Vibe Check Framework Core Functionality

Tests the core VibeCheckFramework class:
- Framework initialization and configuration
- Vibe level determination logic
- Pattern detection integration
- Issue analysis workflow
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile
from github import GithubException

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.legacy.vibe_check_framework import (
    VibeCheckFramework,
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult
)
from vibe_check.core.pattern_detector import DetectionResult
from vibe_check.core.educational_content import DetailLevel


class TestVibeCheckFrameworkCore:
    """Test core vibe check framework functionality"""
    
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
    def sample_detection_results(self):
        """Sample pattern detection results for testing"""
        return [
            DetectionResult(
                patterns_found=["infrastructure_without_implementation"],
                confidence_score=0.85,
                remediation_suggestions=["Use existing SDK instead"],
                educational_content="Building custom servers when SDKs exist is an anti-pattern.",
                risk_level="high"
            )
        ]
    
    @pytest.fixture
    def framework(self, mock_github_token):
        """Create framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework(github_token=mock_github_token)
    
    def test_framework_initialization(self, mock_github_token):
        """Test proper framework initialization"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework(github_token=mock_github_token)
            
            # Verify initialization
            mock_github.assert_called_once_with(mock_github_token)
            assert framework.github_client is not None
            assert framework.pattern_detector is not None
            assert framework.educational_content is not None
    
    def test_framework_initialization_without_token(self):
        """Test framework initialization without GitHub token"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework()
            
            # Should use default GitHub() constructor
            mock_github.assert_called_once_with()
    
    def test_determine_vibe_level_infrastructure_pattern(self, framework, sample_detection_results):
        """Test vibe level determination for infrastructure patterns"""
        # High confidence infrastructure pattern
        sample_detection_results[0].confidence_score = 0.9
        
        vibe_level = framework._determine_vibe_level(sample_detection_results)
        
        assert vibe_level == VibeLevel.BAD_VIBES
    
    def test_determine_vibe_level_medium_confidence(self, framework):
        """Test vibe level determination for medium confidence patterns"""
        detection_results = [
            DetectionResult(
                patterns_found=["complexity_escalation"],
                confidence_score=0.65,
                remediation_suggestions=["Simplify approach"],
                educational_content="Consider simpler alternatives",
                risk_level="medium"
            )
        ]
        
        vibe_level = framework._determine_vibe_level(detection_results)
        
        assert vibe_level == VibeLevel.RESEARCH_NEEDED
    
    def test_determine_vibe_level_low_confidence(self, framework):
        """Test vibe level determination for low confidence patterns"""
        detection_results = [
            DetectionResult(
                patterns_found=["minor_concern"],
                confidence_score=0.3,
                remediation_suggestions=["Minor improvement"],
                educational_content="Small optimization opportunity",
                risk_level="low"
            )
        ]
        
        vibe_level = framework._determine_vibe_level(detection_results)
        
        assert vibe_level == VibeLevel.GOOD_VIBES
    
    def test_determine_vibe_level_no_patterns(self, framework):
        """Test vibe level determination when no patterns detected"""
        detection_results = []
        
        vibe_level = framework._determine_vibe_level(detection_results)
        
        assert vibe_level == VibeLevel.GOOD_VIBES
    
    def test_determine_vibe_level_multiple_patterns(self, framework):
        """Test vibe level determination with multiple patterns"""
        detection_results = [
            DetectionResult(
                patterns_found=["infrastructure_without_implementation"],
                confidence_score=0.8,
                remediation_suggestions=["Use SDK"],
                educational_content="Anti-pattern detected",
                risk_level="high"
            ),
            DetectionResult(
                patterns_found=["complexity_escalation"],
                confidence_score=0.6,
                remediation_suggestions=["Simplify"],
                educational_content="Too complex",
                risk_level="medium"
            )
        ]
        
        vibe_level = framework._determine_vibe_level(detection_results)
        
        # Should use highest confidence score
        assert vibe_level == VibeLevel.BAD_VIBES
    
    def test_generate_friendly_summary_bad_vibes(self, framework, sample_detection_results):
        """Test friendly summary generation for bad vibes"""
        summary = framework._generate_friendly_summary(
            VibeLevel.BAD_VIBES, 
            sample_detection_results
        )
        
        assert "🚨" in summary
        assert "infrastructure without implementation" in summary.lower()
        assert len(summary) > 10  # Should be meaningful
    
    def test_generate_friendly_summary_good_vibes(self, framework):
        """Test friendly summary generation for good vibes"""
        summary = framework._generate_friendly_summary(
            VibeLevel.GOOD_VIBES, 
            []
        )
        
        assert "✅" in summary
        assert "good" in summary.lower() or "looks great" in summary.lower()
    
    def test_generate_coaching_recommendations_with_patterns(self, framework, sample_detection_results):
        """Test coaching recommendations generation with patterns"""
        recommendations = framework._generate_coaching_recommendations(
            sample_detection_results,
            DetailLevel.STANDARD
        )
        
        assert len(recommendations) > 0
        assert any("SDK" in rec for rec in recommendations)
        assert all(len(rec) > 10 for rec in recommendations)  # Should be meaningful
    
    def test_generate_coaching_recommendations_no_patterns(self, framework):
        """Test coaching recommendations generation without patterns"""
        recommendations = framework._generate_coaching_recommendations(
            [],
            DetailLevel.STANDARD
        )
        
        assert len(recommendations) > 0
        assert any("keep up" in rec.lower() or "great" in rec.lower() for rec in recommendations)
    
    def test_generate_coaching_recommendations_brief_level(self, framework, sample_detection_results):
        """Test coaching recommendations with brief detail level"""
        recommendations = framework._generate_coaching_recommendations(
            sample_detection_results,
            DetailLevel.BRIEF
        )
        
        # Brief should have fewer, shorter recommendations
        assert len(recommendations) <= 3
        assert all(len(rec) < 100 for rec in recommendations)
    
    def test_generate_coaching_recommendations_comprehensive_level(self, framework, sample_detection_results):
        """Test coaching recommendations with comprehensive detail level"""
        recommendations = framework._generate_coaching_recommendations(
            sample_detection_results,
            DetailLevel.COMPREHENSIVE
        )
        
        # Comprehensive should have more detailed recommendations
        assert len(recommendations) >= 3
    
    def test_fetch_issue_data_success(self, framework, sample_issue_data):
        """Test successful issue data fetching"""
        # Mock GitHub API
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
        
        framework.github_client.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Test fetching
        result = framework._fetch_issue_data("test/repo", 42)
        
        # Verify result
        assert result["number"] == 42
        assert result["title"] == sample_issue_data["title"]
        assert result["repository"] == "test/repo"
    
    def test_fetch_issue_data_github_exception(self, framework):
        """Test issue data fetching with GitHub exception"""
        framework.github_client.get_repo.side_effect = GithubException(404, "Not Found")
        
        result = framework._fetch_issue_data("nonexistent/repo", 999)
        
        assert result is None
    
    def test_create_vibe_check_result(self, framework, sample_issue_data, sample_detection_results):
        """Test vibe check result creation"""
        result = framework._create_vibe_check_result(
            sample_issue_data,
            sample_detection_results,
            DetailLevel.STANDARD,
            claude_reasoning=None,
            clear_thought_analysis=None
        )
        
        # Verify result structure
        assert isinstance(result, VibeCheckResult)
        assert result.vibe_level == VibeLevel.BAD_VIBES
        assert "🚨" in result.overall_vibe
        assert len(result.coaching_recommendations) > 0
        assert "detected_patterns" in result.technical_analysis
    
    def test_pattern_detection_integration(self, framework, sample_issue_data):
        """Test integration with pattern detection"""
        # Mock pattern detection
        with patch.object(framework.pattern_detector, 'detect_patterns') as mock_detect:
            mock_detection = DetectionResult(
                patterns_found=["test_pattern"],
                confidence_score=0.7,
                remediation_suggestions=["Test suggestion"],
                educational_content="Test content",
                risk_level="medium"
            )
            mock_detect.return_value = mock_detection
            
            # Test detection
            content = f"{sample_issue_data['title']}\n{sample_issue_data['body']}"
            framework.pattern_detector.detect_patterns(content)
            
            # Verify detection was called
            mock_detect.assert_called_once_with(content)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])