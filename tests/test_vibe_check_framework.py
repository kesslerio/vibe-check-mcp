"""
Comprehensive Tests for Vibe Check Framework (Issue #43)

Tests the enhanced vibe check framework components introduced in PR #42:
- Vibe level determination logic
- Claude CLI integration (with mocking)
- Clear-Thought tool orchestration
- GitHub integration and comment posting
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import os
import tempfile
import subprocess
from github import GithubException

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.tools.vibe_check_framework import (
    VibeCheckFramework,
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult,
    get_vibe_check_framework
)
from vibe_check.core.pattern_detector import DetectionResult
from vibe_check.core.educational_content import DetailLevel


class TestVibeCheckFramework:
    """Test comprehensive vibe check framework functionality"""
    
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
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.85,
                evidence=["custom HTTP server", "instead of SDK"],
                threshold=0.6,
                educational_content=""
            ),
            DetectionResult(
                pattern_type="over_engineering",
                detected=False,
                confidence=0.3,
                evidence=[],
                threshold=0.6,
                educational_content=""
            )
        ]
    
    @pytest.fixture
    def vibe_framework(self, mock_github_token):
        """Create vibe check framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework(mock_github_token)
            framework.github_client = mock_github.return_value
            return framework
    
    def test_framework_initialization(self, mock_github_token):
        """Test proper framework initialization"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework(mock_github_token)
            
            # Verify GitHub client initialization
            mock_github.assert_called_once_with(mock_github_token)
            assert framework.github_client is not None
            assert framework.pattern_detector is not None
    
    def test_framework_initialization_without_token(self):
        """Test framework initialization without GitHub token"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = VibeCheckFramework()
            
            # Should use default GitHub() constructor
            mock_github.assert_called_once_with()
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_availability_check_success(self, mock_run, vibe_framework):
        """Test Claude CLI availability check when Claude is available"""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = vibe_framework._check_claude_availability()
        
        assert result is True
        mock_run.assert_called_once_with(
            ['claude', '--version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_availability_check_failure(self, mock_run, vibe_framework):
        """Test Claude CLI availability check when Claude is not available"""
        mock_run.side_effect = FileNotFoundError("Claude not found")
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_availability_check_timeout(self, mock_run, vibe_framework):
        """Test Claude CLI availability check with timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired('claude', 5)
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
    
    def test_fetch_issue_data_success(self, vibe_framework, sample_issue_data):
        """Test successful GitHub issue data fetching"""
        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = sample_issue_data["number"]
        mock_issue.title = sample_issue_data["title"]
        mock_issue.body = sample_issue_data["body"]
        mock_issue.user.login = sample_issue_data["author"]
        mock_issue.created_at.isoformat.return_value = sample_issue_data["created_at"]
        mock_issue.state = sample_issue_data["state"]
        mock_issue.labels = [MagicMock(name=label) for label in sample_issue_data["labels"]]
        mock_issue.html_url = sample_issue_data["url"]
        
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        vibe_framework.github_client.get_repo.return_value = mock_repo
        
        result = vibe_framework._fetch_issue_data(42, "test/repo")
        
        # Verify API calls
        vibe_framework.github_client.get_repo.assert_called_once_with("test/repo")
        mock_repo.get_issue.assert_called_once_with(42)
        
        # Verify returned data structure
        assert result["number"] == 42
        assert result["title"] == sample_issue_data["title"]
        assert result["body"] == sample_issue_data["body"]
        assert result["author"] == sample_issue_data["author"]
        assert result["repository"] == "test/repo"
    
    def test_fetch_issue_data_default_repository(self, vibe_framework):
        """Test issue fetching with default repository"""
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test Body"
        mock_issue.user.login = "testuser"
        mock_issue.created_at.isoformat.return_value = "2025-01-01T00:00:00Z"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.html_url = "https://github.com/kesslerio/vibe-check-mcp/issues/42"
        
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        vibe_framework.github_client.get_repo.return_value = mock_repo
        
        result = vibe_framework._fetch_issue_data(42, None)
        
        # Should use default repository
        vibe_framework.github_client.get_repo.assert_called_once_with("kesslerio/vibe-check-mcp")
        assert result["repository"] == "kesslerio/vibe-check-mcp"
    
    def test_fetch_issue_data_invalid_repository(self, vibe_framework):
        """Test issue fetching with invalid repository format"""
        with pytest.raises(ValueError, match="Repository must be in format 'owner/repo'"):
            vibe_framework._fetch_issue_data(42, "invalid-repo-format")
    
    def test_fetch_issue_data_not_found(self, vibe_framework):
        """Test issue fetching when issue doesn't exist"""
        vibe_framework.github_client.get_repo.side_effect = GithubException(404, {"message": "Not Found"})
        
        with pytest.raises(GithubException):
            vibe_framework._fetch_issue_data(999, "test/repo")
    
    def test_detect_basic_patterns(self, vibe_framework, sample_issue_data, sample_detection_results):
        """Test basic pattern detection"""
        # Mock pattern detector
        vibe_framework.pattern_detector.analyze_text_for_patterns.return_value = sample_detection_results
        
        result = vibe_framework._detect_basic_patterns(sample_issue_data, DetailLevel.STANDARD)
        
        # Verify pattern detector call
        vibe_framework.pattern_detector.analyze_text_for_patterns.assert_called_once_with(
            content=sample_issue_data["body"],
            context=f"Title: {sample_issue_data['title']}",
            focus_patterns=None,
            detail_level=DetailLevel.STANDARD
        )
        
        assert result == sample_detection_results
    
    def test_detect_third_party_services(self, vibe_framework):
        """Test third-party service detection"""
        text = "We need to integrate with cognee and openai apis using docker"
        
        services = vibe_framework._detect_third_party_services(text)
        
        expected_services = ["cognee", "openai", "api", "docker"]
        for service in expected_services:
            assert service in services
    
    def test_detect_infrastructure_keywords(self, vibe_framework):
        """Test infrastructure keyword detection"""
        text = "We need to build the server architecture and database setup"
        
        keywords = vibe_framework._detect_infrastructure_keywords(text)
        
        expected_keywords = ["architecture", "server", "database", "setup"]
        for keyword in expected_keywords:
            assert keyword in keywords
    
    def test_detect_complexity_indicators(self, vibe_framework):
        """Test complexity indicator detection"""
        text = "This requires a sophisticated enterprise framework system"
        
        indicators = vibe_framework._detect_complexity_indicators(text)
        
        expected_indicators = ["sophisticated", "enterprise", "framework", "system"]
        for indicator in expected_indicators:
            assert indicator in indicators
    
    def test_needs_systematic_analysis_multiple_patterns(self, vibe_framework, sample_issue_data):
        """Test systematic analysis need with multiple patterns"""
        patterns = [
            DetectionResult("pattern1", True, 0.7, [], 0.6, ""),
            DetectionResult("pattern2", True, 0.6, [], 0.6, ""),
            DetectionResult("pattern3", True, 0.5, [], 0.6, "")
        ]
        
        result = vibe_framework._needs_systematic_analysis(sample_issue_data, patterns)
        
        assert result is True
    
    def test_needs_systematic_analysis_high_confidence(self, vibe_framework, sample_issue_data):
        """Test systematic analysis need with high confidence patterns"""
        patterns = [
            DetectionResult("high_confidence_pattern", True, 0.9, [], 0.6, "")
        ]
        
        result = vibe_framework._needs_systematic_analysis(sample_issue_data, patterns)
        
        assert result is True
    
    def test_needs_systematic_analysis_complexity_indicators(self, vibe_framework):
        """Test systematic analysis need with complexity indicators"""
        issue_data = {
            "body": "This requires complex sophisticated enterprise advanced framework"
        }
        patterns = []
        
        result = vibe_framework._needs_systematic_analysis(issue_data, patterns)
        
        assert result is True
    
    def test_needs_systematic_analysis_simple_case(self, vibe_framework, sample_issue_data):
        """Test systematic analysis not needed for simple cases"""
        patterns = [
            DetectionResult("simple_pattern", False, 0.2, [], 0.6, "")
        ]
        
        result = vibe_framework._needs_systematic_analysis(sample_issue_data, patterns)
        
        assert result is False
    
    def test_determine_vibe_level_bad_vibes(self, vibe_framework, sample_issue_data):
        """Test vibe level determination for bad vibes"""
        patterns = [
            DetectionResult("infrastructure_without_implementation", True, 0.9, [], 0.6, "")
        ]
        
        result = vibe_framework._determine_vibe_level(sample_issue_data, patterns, None)
        
        assert result == VibeLevel.BAD_VIBES
    
    def test_determine_vibe_level_needs_poc(self, vibe_framework):
        """Test vibe level determination for needs POC"""
        issue_data = {
            "body": "integrate with cognee service for data processing"
        }
        patterns = []
        
        result = vibe_framework._determine_vibe_level(issue_data, patterns, None)
        
        assert result == VibeLevel.NEEDS_POC
    
    def test_determine_vibe_level_complex_vibes(self, vibe_framework):
        """Test vibe level determination for complex vibes"""
        issue_data = {
            "body": "complex sophisticated enterprise advanced framework system architecture"
        }
        patterns = []
        
        result = vibe_framework._determine_vibe_level(issue_data, patterns, None)
        
        assert result == VibeLevel.COMPLEX_VIBES
    
    def test_determine_vibe_level_needs_research(self, vibe_framework):
        """Test vibe level determination for needs research"""
        issue_data = {
            "body": "integrate with openai service"
        }
        patterns = []
        
        result = vibe_framework._determine_vibe_level(issue_data, patterns, None)
        
        assert result == VibeLevel.NEEDS_RESEARCH
    
    def test_determine_vibe_level_good_vibes(self, vibe_framework):
        """Test vibe level determination for good vibes"""
        issue_data = {
            "body": "simple documentation update with research completed"
        }
        patterns = []
        
        result = vibe_framework._determine_vibe_level(issue_data, patterns, None)
        
        assert result == VibeLevel.GOOD_VIBES
    
    def test_generate_friendly_summary(self, vibe_framework, sample_issue_data):
        """Test friendly summary generation for different vibe levels"""
        patterns = []
        
        for vibe_level in VibeLevel:
            summary = vibe_framework._generate_friendly_summary(vibe_level, patterns, sample_issue_data)
            
            # Verify summary is friendly and non-empty
            assert isinstance(summary, str)
            assert len(summary) > 0
            
            # Verify appropriate emojis for each level
            if vibe_level == VibeLevel.GOOD_VIBES:
                assert "✅" in summary
            elif vibe_level == VibeLevel.NEEDS_RESEARCH:
                assert "🔍" in summary
            elif vibe_level == VibeLevel.NEEDS_POC:
                assert "🧪" in summary
            elif vibe_level == VibeLevel.COMPLEX_VIBES:
                assert "⚖️" in summary
            elif vibe_level == VibeLevel.BAD_VIBES:
                assert "🚨" in summary
    
    def test_generate_overall_vibe(self, vibe_framework):
        """Test overall vibe generation"""
        for vibe_level in VibeLevel:
            overall_vibe = vibe_framework._generate_overall_vibe(vibe_level)
            
            assert isinstance(overall_vibe, str)
            assert len(overall_vibe) > 0
            assert "Vibes" in overall_vibe
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    @patch('os.unlink')
    def test_run_claude_analysis_success(self, mock_unlink, mock_run, mock_tempfile, vibe_framework, sample_issue_data, sample_detection_results):
        """Test successful Claude analysis"""
        # Setup mocks
        mock_file = MagicMock()
        mock_file.name = "/tmp/prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Claude analysis result with insights",
            stderr=""
        )
        
        vibe_framework.claude_available = True
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_detection_results)
        
        # Verify temporary file handling
        mock_tempfile.assert_called_once()
        mock_unlink.assert_called_once_with("/tmp/prompt_test.md")
        
        # Verify Claude call
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'claude'
        assert '-p' in call_args
        
        assert result == "Claude analysis result with insights"
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_run_claude_analysis_failure(self, mock_run, mock_tempfile, vibe_framework, sample_issue_data, sample_detection_results):
        """Test Claude analysis failure handling"""
        mock_file = MagicMock()
        mock_file.name = "/tmp/prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Claude error"
        )
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_detection_results)
        
        assert result is None
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_run_claude_analysis_exception(self, mock_run, mock_tempfile, vibe_framework, sample_issue_data, sample_detection_results):
        """Test Claude analysis exception handling"""
        mock_run.side_effect = Exception("Subprocess error")
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_detection_results)
        
        assert result is None
    
    def test_create_sophisticated_vibe_prompt(self, vibe_framework, sample_issue_data, sample_detection_results):
        """Test sophisticated vibe prompt creation"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(sample_issue_data, sample_detection_results)
        
        # Verify prompt contains key elements
        assert sample_issue_data["title"] in prompt
        assert sample_issue_data["body"] in prompt
        assert sample_issue_data["author"] in prompt
        assert sample_issue_data["repository"] in prompt
        
        # Verify coaching framework sections
        assert "🎯 Issue Vibe Check Request" in prompt
        assert "🧠 Pattern Detection Results" in prompt
        assert "🔍 Vibe Check Framework" in prompt
        assert "💡 Friendly Recommendations" in prompt
        
        # Verify pattern information
        assert "infrastructure_without_implementation" in prompt
    
    def test_clear_thought_analysis_recommendations(self, vibe_framework, sample_issue_data, sample_detection_results):
        """Test Clear-Thought analysis recommendations"""
        result = vibe_framework._run_clear_thought_analysis(sample_issue_data, sample_detection_results)
        
        # Should return recommendations structure
        assert isinstance(result, dict)
        assert "analysis_type" in result
        assert "integration_pattern" in result
        assert "recommended_tools" in result
        
        # Should recommend tools for infrastructure patterns
        recommended_tools = result["recommended_tools"]
        assert len(recommended_tools) > 0
        
        # Check for specific tool recommendations
        tool_names = [tool["tool"] for tool in recommended_tools]
        assert any("mentalmodel" in tool for tool in tool_names)
    
    def test_clear_thought_analysis_not_needed(self, vibe_framework):
        """Test Clear-Thought analysis when not needed"""
        simple_issue_data = {
            "body": "simple documentation update"
        }
        simple_patterns = []
        
        result = vibe_framework._run_clear_thought_analysis(simple_issue_data, simple_patterns)
        
        assert result["analysis_type"] == "clear_thought_not_needed"
    
    def test_post_github_comment_success(self, vibe_framework, sample_issue_data):
        """Test successful GitHub comment posting"""
        # Create mock vibe result
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.GOOD_VIBES,
            overall_vibe="✅ Good Vibes",
            friendly_summary="This looks great!",
            coaching_recommendations=["Keep up the good work!", "Add tests"],
            technical_analysis={"detected_patterns": []}
        )
        
        # Mock GitHub API
        mock_issue = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        vibe_framework.github_client.get_repo.return_value = mock_repo
        
        vibe_framework._post_github_comment(42, "test/repo", vibe_result)
        
        # Verify API calls
        vibe_framework.github_client.get_repo.assert_called_once_with("test/repo")
        mock_repo.get_issue.assert_called_once_with(42)
        mock_issue.create_comment.assert_called_once()
        
        # Verify comment format
        comment_body = mock_issue.create_comment.call_args[0][0]
        assert "🎯 Comprehensive Vibe Check" in comment_body
        assert "✅ Good Vibes" in comment_body
        assert "This looks great!" in comment_body
    
    def test_post_github_comment_failure(self, vibe_framework):
        """Test GitHub comment posting failure handling"""
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.GOOD_VIBES,
            overall_vibe="✅ Good Vibes",
            friendly_summary="Test summary",
            coaching_recommendations=[],
            technical_analysis={}
        )
        
        # Mock GitHub API failure
        vibe_framework.github_client.get_repo.side_effect = Exception("API Error")
        
        # Should not raise exception
        vibe_framework._post_github_comment(42, "test/repo", vibe_result)
    
    def test_format_github_comment(self, vibe_framework):
        """Test GitHub comment formatting"""
        vibe_result = VibeCheckResult(
            vibe_level=VibeLevel.NEEDS_RESEARCH,
            overall_vibe="🔍 Research Vibes",
            friendly_summary="Let's do some homework first!",
            coaching_recommendations=["Check docs", "Research existing solutions"],
            technical_analysis={
                "detected_patterns": [{"type": "test_pattern"}]
            },
            claude_reasoning="Claude analysis available",
            clear_thought_analysis={"type": "systematic"}
        )
        
        comment = vibe_framework._format_github_comment(vibe_result)
        
        # Verify comment structure
        assert "🎯 Comprehensive Vibe Check" in comment
        assert "🔍 Research Vibes" in comment
        assert "Let's do some homework first!" in comment
        assert "Check docs" in comment
        assert "Research existing solutions" in comment
        assert "✅ Available" in comment  # Claude analysis
        assert "✅ Applied" in comment    # Clear-Thought analysis
    
    @patch.object(VibeCheckFramework, '_fetch_issue_data')
    @patch.object(VibeCheckFramework, '_detect_basic_patterns')
    @patch.object(VibeCheckFramework, '_run_claude_analysis')
    @patch.object(VibeCheckFramework, '_run_clear_thought_analysis')
    @patch.object(VibeCheckFramework, '_generate_vibe_check_result')
    @patch.object(VibeCheckFramework, '_post_github_comment')
    def test_check_issue_vibes_comprehensive_mode(self, mock_post_comment, mock_generate_result, 
                                                  mock_clear_thought, mock_claude, mock_patterns, 
                                                  mock_fetch, vibe_framework, sample_issue_data, sample_detection_results):
        """Test comprehensive vibe check workflow"""
        # Setup mocks
        mock_fetch.return_value = sample_issue_data
        mock_patterns.return_value = sample_detection_results
        mock_claude.return_value = "Claude analysis"
        mock_clear_thought.return_value = {"recommendations": ["test"]}
        
        expected_result = VibeCheckResult(
            vibe_level=VibeLevel.GOOD_VIBES,
            overall_vibe="✅ Good Vibes",
            friendly_summary="Test summary",
            coaching_recommendations=[],
            technical_analysis={}
        )
        mock_generate_result.return_value = expected_result
        
        vibe_framework.claude_available = True
        
        result = vibe_framework.check_issue_vibes(
            issue_number=42,
            repository="test/repo",
            mode=VibeCheckMode.COMPREHENSIVE,
            detail_level=DetailLevel.STANDARD,
            post_comment=True
        )
        
        # Verify workflow execution
        mock_fetch.assert_called_once_with(42, "test/repo")
        mock_patterns.assert_called_once_with(sample_issue_data, DetailLevel.STANDARD)
        mock_claude.assert_called_once_with(sample_issue_data, sample_detection_results)
        mock_clear_thought.assert_called_once()
        mock_generate_result.assert_called_once()
        mock_post_comment.assert_called_once_with(42, "test/repo", expected_result)
        
        assert result == expected_result
    
    @patch.object(VibeCheckFramework, '_fetch_issue_data')
    @patch.object(VibeCheckFramework, '_detect_basic_patterns')
    @patch.object(VibeCheckFramework, '_generate_vibe_check_result')
    def test_check_issue_vibes_quick_mode(self, mock_generate_result, mock_patterns, 
                                          mock_fetch, vibe_framework, sample_issue_data, sample_detection_results):
        """Test quick vibe check workflow"""
        # Setup mocks
        mock_fetch.return_value = sample_issue_data
        mock_patterns.return_value = sample_detection_results
        
        expected_result = VibeCheckResult(
            vibe_level=VibeLevel.GOOD_VIBES,
            overall_vibe="✅ Good Vibes",
            friendly_summary="Test summary",
            coaching_recommendations=[],
            technical_analysis={}
        )
        mock_generate_result.return_value = expected_result
        
        result = vibe_framework.check_issue_vibes(
            issue_number=42,
            repository="test/repo",
            mode=VibeCheckMode.QUICK,
            detail_level=DetailLevel.BRIEF,
            post_comment=False
        )
        
        # Verify workflow execution (Claude and Clear-Thought should be skipped)
        mock_fetch.assert_called_once_with(42, "test/repo")
        mock_patterns.assert_called_once_with(sample_issue_data, DetailLevel.BRIEF)
        mock_generate_result.assert_called_once()
        
        assert result == expected_result
    
    def test_check_issue_vibes_error_handling(self, vibe_framework):
        """Test vibe check error handling"""
        # Mock fetch to raise exception
        with patch.object(vibe_framework, '_fetch_issue_data', side_effect=Exception("Test error")):
            result = vibe_framework.check_issue_vibes(42, "test/repo")
            
            # Should return error result
            assert result.vibe_level == VibeLevel.BAD_VIBES
            assert result.overall_vibe == "🚨 Analysis Error"
            assert "Test error" in result.friendly_summary
            assert "Try again with a simpler analysis mode" in result.coaching_recommendations
            assert "error" in result.technical_analysis


class TestVibeCheckGlobalFramework:
    """Test global framework instance management"""
    
    def test_get_vibe_check_framework_singleton(self):
        """Test global framework instance is singleton"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            framework1 = get_vibe_check_framework()
            framework2 = get_vibe_check_framework()
            
            # Should return same instance
            assert framework1 is framework2
    
    def test_get_vibe_check_framework_with_token(self):
        """Test global framework instance with token"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            framework = get_vibe_check_framework("test_token")
            
            # Should initialize with token
            mock_github.assert_called_with("test_token")
            assert framework is not None


class TestVibeCheckIntegration:
    """Integration tests for vibe check workflow"""
    
    @pytest.mark.integration
    def test_end_to_end_vibe_check_workflow(self):
        """Test complete end-to-end vibe check workflow with mocked dependencies"""
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup comprehensive mocks
            mock_issue = MagicMock()
            mock_issue.number = 42
            mock_issue.title = "Feature: Custom HTTP server"
            mock_issue.body = "Build custom server instead of using SDK"
            mock_issue.user.login = "testuser"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T00:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/42"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Initialize framework
            framework = VibeCheckFramework("test_token")
            
            # Mock pattern detection to return infrastructure anti-pattern
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = [
                    DetectionResult(
                        pattern_type="infrastructure_without_implementation",
                        detected=True,
                        confidence=0.9,
                        evidence=["custom server", "instead of SDK"],
                        threshold=0.6,
                        educational_content=""
                    )
                ]
                
                # Mock Claude as unavailable to test fallback
                with patch.object(framework, '_check_claude_availability', return_value=False):
                    result = framework.check_issue_vibes(
                        issue_number=42,
                        repository="test/repo",
                        mode=VibeCheckMode.COMPREHENSIVE,
                        detail_level=DetailLevel.STANDARD,
                        post_comment=False
                    )
                    
                    # Verify result structure and content
                    assert isinstance(result, VibeCheckResult)
                    assert result.vibe_level == VibeLevel.BAD_VIBES
                    assert "🚨" in result.overall_vibe
                    assert len(result.coaching_recommendations) > 0
                    assert "detected_patterns" in result.technical_analysis
                    
                    # Verify technical analysis contains pattern information
                    patterns = result.technical_analysis["detected_patterns"]
                    assert len(patterns) > 0
                    assert patterns[0]["type"] == "infrastructure_without_implementation"
                    assert patterns[0]["detected"] is True
                    assert patterns[0]["confidence"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])