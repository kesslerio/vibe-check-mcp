"""
End-to-End Workflow Tests for Enhanced Vibe Check Framework (Issue #43)

Tests complete workflows that integrate all components:
- Full vibe check workflow validation
- GitHub API integration with pattern detection
- Claude CLI integration workflows
- Clear-Thought tool orchestration
- Error handling and recovery workflows
- Performance and reliability validation
"""

import pytest
from unittest.mock import patch, MagicMock, call, mock_open
import sys
import os
import json
from datetime import datetime

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.tools.vibe_check_framework import (
    VibeCheckFramework, 
    VibeCheckMode, 
    VibeLevel, 
    VibeCheckResult,
    get_vibe_check_framework
)
from vibe_check.tools.analyze_issue import analyze_issue, get_github_analyzer
from vibe_check.core.vibe_coaching import get_vibe_coaching_framework
from vibe_check.core.pattern_detector import DetectionResult
from vibe_check.core.educational_content import DetailLevel


class TestCompleteVibeCheckWorkflow:
    """Test complete end-to-end vibe check workflows"""
    
    @pytest.mark.integration
    def test_complete_quick_vibe_check_workflow(self):
        """Test complete quick vibe check workflow from start to finish"""
        
        # Mock GitHub API responses
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup GitHub issue mock
            mock_issue = MagicMock()
            mock_issue.number = 42
            mock_issue.title = "Feature: Add simple API endpoint"
            mock_issue.body = "Add a /health endpoint that returns server status"
            mock_issue.user.login = "developer"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = [MagicMock(name="feature"), MagicMock(name="api")]
            mock_issue.html_url = "https://github.com/test/repo/issues/42"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Initialize framework
            framework = VibeCheckFramework("test_token")
            
            # Mock pattern detection (simple issue, no patterns)
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = []
                
                # Mock Claude as not available (quick mode)
                with patch.object(framework, '_check_claude_availability', return_value=False):
                    
                    # Execute complete workflow
                    result = framework.check_issue_vibes(
                        issue_number=42,
                        repository="test/repo",
                        mode=VibeCheckMode.QUICK,
                        detail_level=DetailLevel.STANDARD,
                        post_comment=False
                    )
                    
                    # Validate complete workflow execution
                    assert isinstance(result, VibeCheckResult)
                    assert result.vibe_level == VibeLevel.GOOD_VIBES
                    assert "✅" in result.overall_vibe
                    assert "solid plan" in result.friendly_summary.lower()
                    assert len(result.coaching_recommendations) > 0
                    
                    # Validate technical analysis structure
                    assert "detected_patterns" in result.technical_analysis
                    assert "integration_analysis" in result.technical_analysis
                    assert "analysis_metadata" in result.technical_analysis
                    
                    # Validate no advanced features were used (quick mode)
                    assert result.claude_reasoning is None
                    assert result.clear_thought_analysis is None
                    
                    # Verify GitHub API was called correctly
                    mock_github.assert_called_once_with("test_token")
                    mock_repo.get_issue.assert_called_once_with(42)
                    
                    # Verify pattern detection was executed
                    mock_patterns.assert_called_once()
    
    @pytest.mark.integration
    def test_complete_comprehensive_vibe_check_workflow(self):
        """Test complete comprehensive vibe check workflow with all features"""
        
        # Mock GitHub API responses
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup GitHub issue mock with problematic content
            mock_issue = MagicMock()
            mock_issue.number = 123
            mock_issue.title = "Feature: Enterprise microservices with custom auth"
            mock_issue.body = """We need to build a sophisticated enterprise microservices architecture:
            - Custom authentication system instead of Auth0 
            - Custom HTTP server framework instead of using Express
            - Complex service orchestration
            - Advanced caching layer
            
            This should integrate with multiple APIs including cognee and openai."""
            mock_issue.user.login = "enterprise_architect"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T10:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = [MagicMock(name="feature"), MagicMock(name="enterprise"), MagicMock(name="architecture")]
            mock_issue.html_url = "https://github.com/enterprise/system/issues/123"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_repo.create_comment = MagicMock()  # For GitHub comment posting
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Initialize framework
            framework = VibeCheckFramework("enterprise_token")
            
            # Mock pattern detection (problematic patterns detected)
            problematic_patterns = [
                DetectionResult(
                    pattern_type="infrastructure_without_implementation",
                    detected=True,
                    confidence=0.9,
                    evidence=["custom authentication", "custom HTTP server", "instead of"],
                    educational_content=""
                ),
                DetectionResult(
                    pattern_type="over_engineering",
                    detected=True,
                    confidence=0.8,
                    evidence=["sophisticated", "enterprise", "complex"],
                    educational_content=""
                )
            ]
            
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = problematic_patterns
                
                # Mock Claude as available and working
                with patch.object(framework, '_check_claude_availability', return_value=True):
                    
                    # Mock Claude analysis execution
                    claude_response = """🎯 Overall Vibe Assessment
This feels like infrastructure-without-implementation combined with over-engineering.

🚨 Integration Risk Check  
Building custom authentication and HTTP servers before proving basic integration works.

🔍 Research Phase Coaching
- Have we checked Auth0 and Express documentation?
- Are we building on existing solutions?

⚖️ Complexity Appropriateness Check
This complexity seems disproportionate - have we tried simple solutions?

🧪 Success Criteria Vibe Check
Are we measuring actual user value or technical complexity?

💡 Friendly Recommendations
BAD VIBES (🚨) - This looks like building infrastructure without proving basics work.

🎓 Learning Opportunities
- API-first development principles
- Standing on shoulders of giants

🎯 Next Steps Recommendation
BAD VIBES"""
                    
                    with patch.object(framework, '_run_claude_analysis', return_value=claude_response):
                        
                        # Execute complete comprehensive workflow
                        result = framework.check_issue_vibes(
                            issue_number=123,
                            repository="enterprise/system",
                            mode=VibeCheckMode.COMPREHENSIVE,
                            detail_level=DetailLevel.COMPREHENSIVE,
                            post_comment=True
                        )
                        
                        # Validate comprehensive workflow execution
                        assert isinstance(result, VibeCheckResult)
                        assert result.vibe_level == VibeLevel.BAD_VIBES
                        assert "🚨" in result.overall_vibe
                        assert "infrastructure without" in result.friendly_summary.lower()
                        assert len(result.coaching_recommendations) > 0
                        
                        # Validate advanced features were used
                        assert result.claude_reasoning is not None
                        assert "infrastructure-without-implementation" in result.claude_reasoning
                        assert result.clear_thought_analysis is not None
                        assert "recommended_tools" in result.clear_thought_analysis
                        
                        # Validate technical analysis completeness
                        tech_analysis = result.technical_analysis
                        assert len(tech_analysis["detected_patterns"]) == 2
                        assert tech_analysis["detected_patterns"][0]["type"] == "infrastructure_without_implementation"
                        assert tech_analysis["detected_patterns"][0]["confidence"] == 0.9
                        
                        # Validate integration analysis
                        integration = tech_analysis["integration_analysis"]
                        assert "cognee" in integration["third_party_services"]
                        assert "openai" in integration["third_party_services"]
                        assert "architecture" in integration["infrastructure_keywords"]
                        assert "sophisticated" in integration["complexity_indicators"]
                        
                        # Verify GitHub comment was posted
                        mock_repo.create_comment.assert_called_once()
                        comment_body = mock_repo.create_comment.call_args[0][0]
                        assert "🎯 Comprehensive Vibe Check" in comment_body
                        assert "🚨 Bad Vibes" in comment_body
    
    @pytest.mark.integration  
    def test_complete_mcp_tool_workflow(self):
        """Test complete MCP tool workflow through analyze_issue function"""
        
        # Mock the vibe check framework
        with patch('vibe_check.tools.analyze_issue.get_vibe_check_framework') as mock_get_framework:
            
            # Create comprehensive mock result
            comprehensive_result = VibeCheckResult(
                vibe_level=VibeLevel.NEEDS_RESEARCH,
                overall_vibe="🔍 Research Vibes",
                friendly_summary="Let's do some homework first! Check existing solutions before building custom.",
                coaching_recommendations=[
                    "🔍 Time to Do Some Homework!: Research existing solutions first",
                    "Search for official SDK documentation",
                    "Look for working examples in similar projects",
                    "📚 Learning Opportunity: Document your research findings",
                    "🤝 Collaboration and Feedback: Get early feedback on approach"
                ],
                technical_analysis={
                    "detected_patterns": [
                        {
                            "type": "infrastructure_without_implementation",
                            "confidence": 0.75,
                            "detected": True,
                            "evidence": ["custom solution", "no research mentioned"]
                        }
                    ],
                    "integration_analysis": {
                        "third_party_services": ["api", "sdk"],
                        "infrastructure_keywords": ["server", "integration"],
                        "complexity_indicators": []
                    },
                    "analysis_metadata": {
                        "claude_analysis_available": True,
                        "clear_thought_analysis_available": False,
                        "detail_level": "standard"
                    }
                },
                claude_reasoning="Claude suggests researching existing solutions first",
                clear_thought_analysis=None
            )
            
            mock_framework = MagicMock()
            mock_framework.check_issue_vibes.return_value = comprehensive_result
            mock_get_framework.return_value = mock_framework
            
            # Execute complete MCP tool workflow
            result = analyze_issue(
                issue_number=789,
                repository="team/project", 
                analysis_mode="comprehensive",
                detail_level="standard",
                post_comment=True
            )
            
            # Validate MCP tool response structure
            assert result["status"] == "vibe_check_complete"
            assert "analysis_timestamp" in result
            
            # Validate vibe check section
            vibe_check = result["vibe_check"]
            assert vibe_check["overall_vibe"] == "🔍 Research Vibes"
            assert vibe_check["vibe_level"] == "needs_research"
            assert "homework first" in vibe_check["friendly_summary"]
            assert len(vibe_check["coaching_recommendations"]) == 5
            
            # Validate issue info section
            issue_info = result["issue_info"]
            assert issue_info["number"] == 789
            assert issue_info["repository"] == "team/project"
            assert issue_info["analysis_mode"] == "comprehensive"
            assert issue_info["detail_level"] == "standard"
            assert issue_info["comment_posted"] == True
            
            # Validate technical analysis passthrough
            tech_analysis = result["technical_analysis"]
            assert len(tech_analysis["detected_patterns"]) == 1
            assert tech_analysis["detected_patterns"][0]["confidence"] == 0.75
            
            # Validate enhanced features tracking
            features = result["enhanced_features"]
            assert features["claude_reasoning"] == True
            assert features["clear_thought_analysis"] == False
            assert features["comprehensive_validation"] == True
            assert features["educational_coaching"] == True
            assert features["friendly_language"] == True
            
            # Validate metadata
            metadata = result["analysis_metadata"]
            assert metadata["framework_version"] == "2.0 - Claude-powered vibe check"
            assert "87.5% accuracy" in metadata["core_engine_validation"]
            assert metadata["analysis_type"] == "comprehensive_vibe_check"
            assert metadata["language_style"] == "friendly_coaching"
            
            # Verify framework was called correctly
            mock_framework.check_issue_vibes.assert_called_once_with(
                issue_number=789,
                repository="team/project",
                mode=VibeCheckMode.COMPREHENSIVE,
                detail_level=DetailLevel.STANDARD,
                post_comment=True
            )


class TestErrorHandlingWorkflows:
    """Test complete error handling and recovery workflows"""
    
    @pytest.mark.integration
    def test_github_api_failure_recovery_workflow(self):
        """Test complete workflow when GitHub API fails"""
        
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup GitHub API failure
            mock_github.return_value.get_repo.side_effect = Exception("GitHub API unavailable")
            
            framework = VibeCheckFramework("test_token")
            
            # Execute workflow with GitHub failure
            result = framework.check_issue_vibes(
                issue_number=42,
                repository="test/repo",
                mode=VibeCheckMode.QUICK
            )
            
            # Validate error handling
            assert result.vibe_level == VibeLevel.BAD_VIBES
            assert result.overall_vibe == "🚨 Analysis Error"
            assert "GitHub API unavailable" in result.friendly_summary
            assert "Try again with a simpler analysis mode" in result.coaching_recommendations
            assert "error" in result.technical_analysis
    
    @pytest.mark.integration
    def test_claude_failure_graceful_degradation_workflow(self):
        """Test workflow graceful degradation when Claude fails"""
        
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup successful GitHub API
            mock_issue = MagicMock()
            mock_issue.number = 42
            mock_issue.title = "Test Issue"
            mock_issue.body = "Custom HTTP server implementation"
            mock_issue.user.login = "developer"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/42"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            framework = VibeCheckFramework("test_token")
            
            # Mock pattern detection success
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = [
                    DetectionResult(
                        pattern_type="infrastructure_without_implementation",
                        detected=True,
                        confidence=0.8,
                        evidence=["custom HTTP server"],
                        educational_content=""
                    )
                ]
                
                # Mock Claude as available but failing
                with patch.object(framework, '_check_claude_availability', return_value=True):
                    with patch.object(framework, '_run_claude_analysis', return_value=None):  # Claude fails
                        
                        # Execute workflow with Claude failure
                        result = framework.check_issue_vibes(
                            issue_number=42,
                            repository="test/repo",
                            mode=VibeCheckMode.COMPREHENSIVE
                        )
                        
                        # Validate graceful degradation
                        assert isinstance(result, VibeCheckResult)
                        assert result.vibe_level == VibeLevel.BAD_VIBES  # Pattern still detected
                        assert result.claude_reasoning is None  # Claude failed
                        assert len(result.coaching_recommendations) > 0  # Fallback coaching works
                        assert len(result.technical_analysis["detected_patterns"]) == 1  # Core detection works
    
    @pytest.mark.integration
    def test_pattern_detection_failure_recovery_workflow(self):
        """Test workflow recovery when pattern detection fails"""
        
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup successful GitHub API
            mock_issue = MagicMock()
            mock_issue.number = 42
            mock_issue.title = "Test Issue"
            mock_issue.body = "Simple feature request"
            mock_issue.user.login = "developer"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/42"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            framework = VibeCheckFramework("test_token")
            
            # Mock pattern detection failure
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.side_effect = Exception("Pattern detection service unavailable")
                
                # Execute workflow with pattern detection failure
                result = framework.check_issue_vibes(
                    issue_number=42,
                    repository="test/repo",
                    mode=VibeCheckMode.QUICK
                )
                
                # Validate error handling
                assert result.vibe_level == VibeLevel.BAD_VIBES
                assert result.overall_vibe == "🚨 Analysis Error"
                assert "Pattern detection service unavailable" in result.friendly_summary


class TestPerformanceWorkflows:
    """Test performance characteristics of complete workflows"""
    
    @pytest.mark.integration
    def test_large_issue_content_workflow(self):
        """Test workflow performance with large issue content"""
        
        # Create large issue content (10KB)
        large_content = "This is a complex issue description. " * 500
        
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup large issue mock
            mock_issue = MagicMock()
            mock_issue.number = 999
            mock_issue.title = "Large Complex Feature Request"
            mock_issue.body = large_content
            mock_issue.user.login = "enterprise_user"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = [MagicMock(name="feature"), MagicMock(name="complex")]
            mock_issue.html_url = "https://github.com/test/repo/issues/999"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            framework = VibeCheckFramework("test_token")
            
            # Mock pattern detection for large content
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = []
                
                # Measure workflow execution
                start_time = datetime.utcnow()
                
                result = framework.check_issue_vibes(
                    issue_number=999,
                    repository="test/repo",
                    mode=VibeCheckMode.QUICK
                )
                
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()
                
                # Validate workflow completed successfully
                assert isinstance(result, VibeCheckResult)
                assert result.vibe_level == VibeLevel.GOOD_VIBES  # No patterns detected
                
                # Validate reasonable performance (should complete quickly for quick mode)
                assert execution_time < 5.0  # Should complete within 5 seconds
                
                # Verify large content was processed
                assert len(large_content) > 10000
                mock_patterns.assert_called_once()
                call_args = mock_patterns.call_args[1]
                assert call_args["content"] == large_content
    
    @pytest.mark.integration
    def test_multiple_patterns_workflow_performance(self):
        """Test workflow performance with multiple detected patterns"""
        
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup issue with multiple problematic patterns
            mock_issue = MagicMock()
            mock_issue.number = 888
            mock_issue.title = "Complex enterprise system with multiple issues"
            mock_issue.body = """Custom authentication, custom HTTP server, complex microservices,
            sophisticated caching, advanced orchestration, enterprise architecture"""
            mock_issue.user.login = "architect"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/888"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            framework = VibeCheckFramework("test_token")
            
            # Mock multiple pattern detection
            multiple_patterns = [
                DetectionResult("infrastructure_without_implementation", True, 0.9, ["custom auth"], ""),
                DetectionResult("over_engineering", True, 0.8, ["sophisticated"], ""),
                DetectionResult("symptom_driven_development", True, 0.7, ["complex"], ""),
                DetectionResult("premature_optimization", True, 0.6, ["advanced"], ""),
                DetectionResult("complexity_escalation", True, 0.75, ["enterprise"], "")
            ]
            
            with patch.object(framework.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = multiple_patterns
                
                # Mock Claude as not available for performance test
                with patch.object(framework, '_check_claude_availability', return_value=False):
                    
                    # Measure workflow execution
                    start_time = datetime.utcnow()
                    
                    result = framework.check_issue_vibes(
                        issue_number=888,
                        repository="test/repo",
                        mode=VibeCheckMode.COMPREHENSIVE
                    )
                    
                    end_time = datetime.utcnow()
                    execution_time = (end_time - start_time).total_seconds()
                    
                    # Validate workflow handled multiple patterns
                    assert isinstance(result, VibeCheckResult)
                    assert result.vibe_level == VibeLevel.BAD_VIBES
                    assert len(result.technical_analysis["detected_patterns"]) == 5
                    assert len(result.coaching_recommendations) > 0
                    
                    # Validate reasonable performance even with multiple patterns
                    assert execution_time < 10.0  # Should complete within 10 seconds
                    
                    # Verify Clear-Thought analysis was triggered for complex case
                    assert result.clear_thought_analysis is not None
                    assert "recommended_tools" in result.clear_thought_analysis


class TestGlobalInstanceWorkflows:
    """Test workflows using global instances"""
    
    @pytest.mark.integration
    def test_global_framework_instance_workflow(self):
        """Test workflow using global framework instance"""
        
        with patch('vibe_check.tools.vibe_check_framework.Github') as mock_github:
            # Setup GitHub API mock
            mock_issue = MagicMock()
            mock_issue.number = 555
            mock_issue.title = "Global instance test"
            mock_issue.body = "Testing global framework instance"
            mock_issue.user.login = "tester"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/555"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Get global framework instance
            framework1 = get_vibe_check_framework("global_token")
            framework2 = get_vibe_check_framework()  # Should reuse existing instance
            
            # Verify singleton behavior
            assert framework1 is framework2
            
            # Mock pattern detection
            with patch.object(framework1.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = []
                
                # Execute workflow through global instance
                result = framework1.check_issue_vibes(
                    issue_number=555,
                    repository="test/repo",
                    mode=VibeCheckMode.QUICK
                )
                
                # Validate workflow execution
                assert isinstance(result, VibeCheckResult)
                assert result.vibe_level == VibeLevel.GOOD_VIBES
    
    @pytest.mark.integration
    def test_global_analyzer_instance_workflow(self):
        """Test workflow using global analyzer instance"""
        
        with patch('vibe_check.tools.analyze_issue.Github') as mock_github:
            # Setup GitHub API mock
            mock_issue = MagicMock()
            mock_issue.number = 666
            mock_issue.title = "Global analyzer test"
            mock_issue.body = "Testing global analyzer instance"
            mock_issue.user.login = "analyzer_tester"
            mock_issue.created_at.isoformat.return_value = "2025-01-01T12:00:00Z"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.html_url = "https://github.com/test/repo/issues/666"
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Get global analyzer instances
            analyzer1 = get_github_analyzer("analyzer_token")
            analyzer2 = get_github_analyzer()  # Should reuse existing instance
            
            # Verify singleton behavior
            assert analyzer1 is analyzer2
            
            # Mock pattern detection
            with patch.object(analyzer1.pattern_detector, 'analyze_text_for_patterns') as mock_patterns:
                mock_patterns.return_value = []
                
                # Execute legacy analyzer workflow
                result = analyzer1.analyze_issue(
                    issue_number=666,
                    repository="test/repo"
                )
                
                # Validate legacy workflow
                assert result["status"] == "analysis_complete"
                assert result["issue_info"]["number"] == 666
                assert result["confidence_summary"]["total_patterns_detected"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])