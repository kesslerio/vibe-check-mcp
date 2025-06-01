"""
Comprehensive Integration Tests for Enhanced Analyze Issue Tool (Issue #43)

Tests the enhanced analyze_issue.py MCP tool:
- Dual-mode analysis (quick vs comprehensive)
- Parameter validation and error handling
- Response format consistency
- MCP tool interface compliance
- GitHub API integration
"""

import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os
from github import GithubException

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
        analyzer.github_client.get_repo.return_value = mock_repo
        
        result = analyzer._fetch_issue_data(42, "test/repo")
        
        # Verify API calls
        analyzer.github_client.get_repo.assert_called_once_with("test/repo")
        mock_repo.get_issue.assert_called_once_with(42)
        
        # Verify returned data structure
        assert result["number"] == 42
        assert result["title"] == sample_issue_data["title"]
        assert result["body"] == sample_issue_data["body"]
        assert result["author"] == sample_issue_data["author"]
        assert result["repository"] == "test/repo"
    
    def test_fetch_issue_data_default_repository(self, analyzer):
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
        analyzer.github_client.get_repo.return_value = mock_repo
        
        result = analyzer._fetch_issue_data(42, None)
        
        # Should use default repository
        analyzer.github_client.get_repo.assert_called_once_with("kesslerio/vibe-check-mcp")
        assert result["repository"] == "kesslerio/vibe-check-mcp"
    
    def test_fetch_issue_data_invalid_repository(self, analyzer):
        """Test issue fetching with invalid repository format"""
        with pytest.raises(ValueError, match="Repository must be in format 'owner/repo'"):
            analyzer._fetch_issue_data(42, "invalid-repo-format")
    
    def test_fetch_issue_data_not_found(self, analyzer):
        """Test issue fetching when issue doesn't exist"""
        analyzer.github_client.get_repo.side_effect = GithubException(404, {"message": "Not Found"})
        
        with pytest.raises(GithubException):
            analyzer._fetch_issue_data(999, "test/repo")
    
    def test_analyze_issue_input_validation(self, analyzer):
        """Test input validation for analyze_issue method"""
        # Test negative issue number
        result = analyzer.analyze_issue(-1, "test/repo")
        assert result["status"] == "analysis_error"
        assert "must be positive" in result["error"]
        
        # Test zero issue number
        result = analyzer.analyze_issue(0, "test/repo")
        assert result["status"] == "analysis_error"
        assert "must be positive" in result["error"]
    
    def test_analyze_issue_invalid_detail_level(self, analyzer, sample_issue_data):
        """Test analyze_issue with invalid detail level"""
        # Mock successful issue fetch
        mock_issue = self._create_mock_issue(sample_issue_data)
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        analyzer.github_client.get_repo.return_value = mock_repo
        
        # Mock pattern detection
        with patch.object(analyzer.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
            mock_patterns.return_value = []
            
            result = analyzer.analyze_issue(42, "test/repo", detail_level="invalid_level")
            
            # Should complete successfully with default detail level
            assert result["status"] == "analysis_complete"
            assert result["analysis_metadata"]["detail_level"] == "standard"
    
    def test_analyze_issue_invalid_focus_patterns(self, analyzer, sample_issue_data):
        """Test analyze_issue with invalid focus patterns"""
        # Mock successful issue fetch
        mock_issue = self._create_mock_issue(sample_issue_data)
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        analyzer.github_client.get_repo.return_value = mock_repo
        
        # Mock pattern detector to return valid patterns
        with patch.object(analyzer.pattern_detector, 'get_pattern_types') as mock_get_types:
            mock_get_types.return_value = ["infrastructure_without_implementation", "over_engineering"]
            
            with patch.object(analyzer.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = []
                
                result = analyzer.analyze_issue(
                    42, "test/repo", 
                    focus_patterns="invalid_pattern,infrastructure_without_implementation"
                )
                
                # Should complete successfully, ignoring invalid patterns
                assert result["status"] == "analysis_complete"
                # Should have called pattern detection with valid patterns only
                mock_patterns.assert_called_once()
                call_args = mock_patterns.call_args[1]
                assert call_args["focus_patterns"] == ["infrastructure_without_implementation"]
    
    def test_analyze_issue_github_api_error(self, analyzer):
        """Test analyze_issue GitHub API error handling"""
        analyzer.github_client.get_repo.side_effect = GithubException(404, {"message": "Repository not found"})
        
        result = analyzer.analyze_issue(42, "nonexistent/repo")
        
        assert result["status"] == "github_api_error"
        assert "Repository not found" in result["error"]
        assert result["issue_number"] == 42
        assert result["repository"] == "nonexistent/repo"
    
    def test_analyze_issue_general_exception(self, analyzer):
        """Test analyze_issue general exception handling"""
        analyzer.github_client.get_repo.side_effect = Exception("Unexpected error")
        
        result = analyzer.analyze_issue(42, "test/repo")
        
        assert result["status"] == "analysis_error"
        assert "Unexpected error" in result["error"]
        assert result["issue_number"] == 42
        assert result["repository"] == "test/repo"
    
    def test_generate_analysis_response_with_patterns(self, analyzer, sample_issue_data):
        """Test analysis response generation with detected patterns"""
        patterns = [
            DetectionResult(
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.85,
                evidence=["custom server", "instead of SDK"],
                educational_content={
                    "pattern_name": "Infrastructure Without Implementation",
                    "immediate_actions": ["Start with basic API calls", "Use official SDK"]
                },
                threshold=0.6
            ),
            DetectionResult(
                pattern_type="over_engineering",
                detected=True,
                confidence=0.75,
                evidence=["complex architecture"],
                educational_content={
                    "pattern_name": "Over Engineering",
                    "immediate_actions": ["Simplify approach", "Question complexity"]
                },
                threshold=0.6
            )
        ]
        
        result = analyzer._generate_analysis_response(sample_issue_data, patterns, DetailLevel.STANDARD)
        
        # Verify response structure
        assert result["status"] == "analysis_complete"
        assert "analysis_timestamp" in result
        assert "issue_info" in result
        assert "patterns_detected" in result
        assert "confidence_summary" in result
        assert "recommended_actions" in result
        assert "analysis_metadata" in result
        
        # Verify confidence summary
        confidence = result["confidence_summary"]
        assert confidence["total_patterns_detected"] == 2
        assert confidence["average_confidence"] == 0.8
        assert confidence["highest_confidence"] == 0.85
        assert len(confidence["patterns_by_confidence"]) == 2
        
        # Verify patterns are sorted by confidence
        patterns_by_conf = confidence["patterns_by_confidence"]
        assert patterns_by_conf[0]["confidence"] == 0.85
        assert patterns_by_conf[1]["confidence"] == 0.75
        assert patterns_by_conf[0]["severity"] == "HIGH"
        assert patterns_by_conf[1]["severity"] == "MEDIUM"
        
        # Verify recommended actions
        actions = result["recommended_actions"]
        assert len(actions) > 0
        assert any("CRITICAL" in action or "HIGH PRIORITY" in action for action in actions)
        assert any("Start with basic API calls" in action for action in actions)
    
    def test_generate_analysis_response_no_patterns(self, analyzer, sample_issue_data):
        """Test analysis response generation with no detected patterns"""
        result = analyzer._generate_analysis_response(sample_issue_data, [], DetailLevel.BRIEF)
        
        # Verify response structure
        assert result["status"] == "analysis_complete"
        assert result["confidence_summary"]["total_patterns_detected"] == 0
        assert result["confidence_summary"]["average_confidence"] == 0.0
        assert result["patterns_detected"] == []
        
        # Verify positive recommendations
        actions = result["recommended_actions"]
        assert any("No anti-patterns detected" in action for action in actions)
        assert any("Continue with standard engineering practices" in action for action in actions)
    
    def test_generate_recommended_actions_priority_levels(self, analyzer):
        """Test recommended actions generation with different priority levels"""
        patterns = [
            DetectionResult("critical_pattern", True, 0.9, [], 0.6, educational_content={"pattern_name": "Critical"}),
            DetectionResult("high_pattern", True, 0.7, [], 0.6, educational_content={"pattern_name": "High"}),
            DetectionResult("medium_pattern", True, 0.5, [], 0.6, educational_content={"pattern_name": "Medium"})
        ]
        
        actions = analyzer._generate_recommended_actions(patterns, DetailLevel.STANDARD)
        
        # Verify priority levels in actions
        assert any("🚨 CRITICAL" in action for action in actions)
        assert any("⚠️ HIGH PRIORITY" in action for action in actions)
        assert any("💡 CONSIDER" in action for action in actions)
    
    def test_get_supported_patterns(self, analyzer):
        """Test getting supported pattern types"""
        with patch.object(analyzer.pattern_detector, 'get_pattern_types') as mock_get_types:
            mock_get_types.return_value = ["pattern1", "pattern2", "pattern3"]
            
            patterns = analyzer.get_supported_patterns()
            
            assert patterns == ["pattern1", "pattern2", "pattern3"]
            mock_get_types.assert_called_once()
    
    def test_get_validation_summary(self, analyzer):
        """Test getting validation summary"""
        with patch.object(analyzer.pattern_detector, 'get_validation_summary') as mock_summary:
            mock_summary.return_value = {"accuracy": "87.5%", "false_positives": "0%"}
            
            summary = analyzer.get_validation_summary()
            
            assert summary["accuracy"] == "87.5%"
            mock_summary.assert_called_once()
    
    def _create_mock_issue(self, issue_data):
        """Helper method to create mock GitHub issue"""
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
                "Prove functionality before building architecture"
            ],
            technical_analysis={
                "detected_patterns": [
                    {
                        "type": "infrastructure_without_implementation",
                        "confidence": 0.85,
                        "detected": True,
                        "evidence": ["custom server", "instead of SDK"]
                    }
                ],
                "integration_analysis": {
                    "third_party_services": ["api"],
                    "infrastructure_keywords": ["server"],
                    "complexity_indicators": []
                },
                "analysis_metadata": {
                    "claude_analysis_available": False,
                    "clear_thought_analysis_available": False,
                    "detail_level": "standard"
                }
            },
            claude_reasoning=None,
            clear_thought_analysis=None
        )
    
    @patch('vibe_check.tools.analyze_issue.get_vibe_check_framework')
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
            post_comment=False
        )
        
        # Verify framework call
        mock_framework.check_issue_vibes.assert_called_once_with(
            issue_number=42,
            repository="test/repo",
            mode=VibeCheckMode.QUICK,
            detail_level=DetailLevel.BRIEF,
            post_comment=False
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
    
    @patch('vibe_check.tools.analyze_issue.get_vibe_check_framework')
    def test_analyze_issue_comprehensive_mode(self, mock_get_framework, mock_vibe_check_result):
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
            post_comment=True
        )
        
        # Verify framework call
        mock_framework.check_issue_vibes.assert_called_once_with(
            issue_number=123,
            repository="owner/repo",
            mode=VibeCheckMode.COMPREHENSIVE,
            detail_level=DetailLevel.COMPREHENSIVE,
            post_comment=True
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
    
    @patch('vibe_check.tools.analyze_issue.get_vibe_check_framework')
    def test_analyze_issue_default_parameters(self, mock_get_framework, mock_vibe_check_result):
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
            post_comment=False
        )
        
        # Verify default repository in response
        assert result["issue_info"]["repository"] == "kesslerio/vibe-check-mcp"
        assert result["issue_info"]["analysis_mode"] == "quick"
        assert result["issue_info"]["detail_level"] == "standard"
    
    @patch('vibe_check.tools.analyze_issue.get_vibe_check_framework')
    def test_analyze_issue_invalid_detail_level(self, mock_get_framework, mock_vibe_check_result):
        """Test analyze_issue with invalid detail level"""
        mock_framework = MagicMock()
        mock_framework.check_issue_vibes.return_value = mock_vibe_check_result
        mock_get_framework.return_value = mock_framework
        
        result = analyze_issue(
            issue_number=42,
            detail_level="invalid_level"
        )
        
        # Should use standard as default
        mock_framework.check_issue_vibes.assert_called_once()
        call_args = mock_framework.check_issue_vibes.call_args[1]
        assert call_args["detail_level"] == DetailLevel.STANDARD
    
    @patch('vibe_check.tools.analyze_issue.get_vibe_check_framework')
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
        with patch('vibe_check.tools.analyze_issue.get_vibe_check_framework') as mock_get_framework:
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = VibeCheckResult(
                vibe_level=VibeLevel.GOOD_VIBES,
                overall_vibe="✅ Good Vibes",
                friendly_summary="Test",
                coaching_recommendations=[],
                technical_analysis={}
            )
            mock_get_framework.return_value = mock_framework
            
            # Test comprehensive mode with auto-enabled comment posting
            result = analyze_issue(
                issue_number=42,
                analysis_mode="comprehensive"
                # post_comment not specified - should be auto-enabled
            )
            
            # Verify call was made (post_comment handled by framework logic)
            mock_framework.check_issue_vibes.assert_called_once()


class TestGlobalAnalyzerInstance:
    """Test global analyzer instance management"""
    
    def test_get_github_analyzer_singleton(self):
        """Test global analyzer instance is singleton"""
        with patch('vibe_check.tools.analyze_issue.Github'):
            analyzer1 = get_github_analyzer()
            analyzer2 = get_github_analyzer()
            
            # Should return same instance
            assert analyzer1 is analyzer2
            assert isinstance(analyzer1, GitHubIssueAnalyzer)
    
    def test_get_github_analyzer_with_token(self):
        """Test global analyzer instance with token"""
        with patch('vibe_check.tools.analyze_issue.Github') as mock_github:
            analyzer = get_github_analyzer("test_token")
            
            # Should initialize with token
            mock_github.assert_called_with("test_token")
            assert analyzer is not None


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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])