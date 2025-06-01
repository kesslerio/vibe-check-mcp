"""
Comprehensive Tests for Claude CLI Integration (Issue #43)

Tests Claude CLI integration with comprehensive mocking to avoid external dependencies:
- Claude CLI availability detection
- Claude analysis execution with subprocess mocking
- Prompt generation and temporary file handling
- Error handling and fallback behavior
- Security considerations (temp file cleanup)
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import os
import tempfile
import subprocess

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_check.tools.vibe_check_framework import VibeCheckFramework
from vibe_check.core.pattern_detector import DetectionResult


class TestClaudeAvailabilityDetection:
    """Test Claude CLI availability detection with comprehensive mocking"""
    
    @pytest.fixture
    def vibe_framework(self):
        """Create vibe check framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework("mock_token")
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_available_success(self, mock_run, vibe_framework):
        """Test Claude CLI availability when Claude is installed and working"""
        # Mock successful Claude version check
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Claude CLI version 1.0.0",
            stderr=""
        )
        
        result = vibe_framework._check_claude_availability()
        
        assert result is True
        mock_run.assert_called_once_with(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_available_command_not_found(self, mock_run, vibe_framework):
        """Test Claude CLI availability when command is not found"""
        # Mock FileNotFoundError (command not in PATH)
        mock_run.side_effect = FileNotFoundError("claude: command not found")
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
        mock_run.assert_called_once_with(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_available_timeout(self, mock_run, vibe_framework):
        """Test Claude CLI availability when command times out"""
        # Mock timeout error
        mock_run.side_effect = subprocess.TimeoutExpired('claude', 5)
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
        mock_run.assert_called_once()
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_available_subprocess_error(self, mock_run, vibe_framework):
        """Test Claude CLI availability with subprocess error"""
        # Mock subprocess error
        mock_run.side_effect = subprocess.SubprocessError("Subprocess failed")
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
        mock_run.assert_called_once()
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_available_non_zero_exit(self, mock_run, vibe_framework):
        """Test Claude CLI availability when command exits with error"""
        # Mock non-zero exit code
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Invalid option"
        )
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
        mock_run.assert_called_once()
    
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    def test_claude_available_permission_error(self, mock_run, vibe_framework):
        """Test Claude CLI availability with permission error"""
        # Mock permission error
        mock_run.side_effect = PermissionError("Permission denied")
        
        result = vibe_framework._check_claude_availability()
        
        assert result is False
        mock_run.assert_called_once()


class TestClaudeAnalysisExecution:
    """Test Claude analysis execution with comprehensive subprocess mocking"""
    
    @pytest.fixture
    def vibe_framework(self):
        """Create vibe check framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            framework = VibeCheckFramework("mock_token")
            framework.claude_available = True  # Override availability check
            return framework
    
    @pytest.fixture
    def sample_issue_data(self):
        """Sample issue data for testing"""
        return {
            "number": 42,
            "title": "Feature: Add custom HTTP server",
            "body": "We need to build a custom HTTP server instead of using the SDK",
            "author": "testuser",
            "repository": "test/repo",
            "labels": ["feature"]
        }
    
    @pytest.fixture
    def sample_patterns(self):
        """Sample detection patterns for testing"""
        return [
            DetectionResult(
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.85,
                evidence=["custom server", "instead of SDK"],
                educational_content=""
            )
        ]
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    @patch('os.unlink')
    def test_claude_analysis_success(self, mock_unlink, mock_run, mock_tempfile, 
                                    vibe_framework, sample_issue_data, sample_patterns):
        """Test successful Claude analysis execution"""
        # Setup temporary file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/claude_prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Setup successful subprocess run
        claude_response = """🎯 Overall Vibe Assessment
This looks like infrastructure-without-implementation pattern.

🚨 Integration Risk Check
Building custom server before proving basic API integration works.

🔍 Research Phase Coaching
- Check official SDK documentation first
- Look for existing examples

🎯 Next Steps Recommendation
BAD VIBES - Start with basic API calls instead of custom infrastructure"""
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=claude_response,
            stderr=""
        )
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_patterns)
        
        # Verify temporary file handling
        mock_tempfile.assert_called_once_with(mode='w', suffix='.md', delete=False)
        mock_file.write.assert_called_once()  # Prompt should be written to file
        
        # Verify subprocess call
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'claude'
        assert '-p' in call_args
        
        # Verify subprocess options
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['capture_output'] is True
        assert call_kwargs['text'] is True
        assert call_kwargs['timeout'] == 60
        
        # Verify temporary file cleanup
        mock_unlink.assert_called_once_with("/tmp/claude_prompt_test.md")
        
        # Verify return value
        assert result == claude_response
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    @patch('os.unlink')
    def test_claude_analysis_failure_non_zero_exit(self, mock_unlink, mock_run, mock_tempfile,
                                                   vibe_framework, sample_issue_data, sample_patterns):
        """Test Claude analysis with non-zero exit code"""
        # Setup temporary file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/claude_prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Setup failed subprocess run
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Claude analysis failed"
        )
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_patterns)
        
        # Should return None on failure
        assert result is None
        
        # Should still clean up temporary file
        mock_unlink.assert_called_once_with("/tmp/claude_prompt_test.md")
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    @patch('os.unlink')
    def test_claude_analysis_empty_output(self, mock_unlink, mock_run, mock_tempfile,
                                         vibe_framework, sample_issue_data, sample_patterns):
        """Test Claude analysis with empty output"""
        # Setup temporary file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/claude_prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Setup subprocess with empty output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="   \n\t  ",  # Whitespace only
            stderr=""
        )
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_patterns)
        
        # Should return None for empty output
        assert result is None
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    @patch('os.unlink')
    def test_claude_analysis_subprocess_timeout(self, mock_unlink, mock_run, mock_tempfile,
                                               vibe_framework, sample_issue_data, sample_patterns):
        """Test Claude analysis with subprocess timeout"""
        # Setup temporary file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/claude_prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Setup subprocess timeout
        mock_run.side_effect = subprocess.TimeoutExpired('claude', 60)
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_patterns)
        
        # Should return None on timeout
        assert result is None
        
        # Should still clean up temporary file
        mock_unlink.assert_called_once_with("/tmp/claude_prompt_test.md")
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run')
    @patch('os.unlink')
    def test_claude_analysis_general_exception(self, mock_unlink, mock_run, mock_tempfile,
                                              vibe_framework, sample_issue_data, sample_patterns):
        """Test Claude analysis with general exception"""
        # Setup temporary file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/claude_prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Setup general exception
        mock_run.side_effect = Exception("Unexpected error")
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_patterns)
        
        # Should return None on exception
        assert result is None
        
        # Should still clean up temporary file
        mock_unlink.assert_called_once_with("/tmp/claude_prompt_test.md")
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('vibe_check.tools.vibe_check_framework.subprocess.run') 
    @patch('os.unlink')
    def test_claude_analysis_file_cleanup_failure(self, mock_unlink, mock_run, mock_tempfile,
                                                  vibe_framework, sample_issue_data, sample_patterns):
        """Test Claude analysis with file cleanup failure"""
        # Setup temporary file mock
        mock_file = MagicMock()
        mock_file.name = "/tmp/claude_prompt_test.md"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Setup successful subprocess
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Claude analysis result",
            stderr=""
        )
        
        # Setup file cleanup failure
        mock_unlink.side_effect = OSError("Permission denied")
        
        result = vibe_framework._run_claude_analysis(sample_issue_data, sample_patterns)
        
        # Should still return result despite cleanup failure
        assert result == "Claude analysis result"
        
        # Should have attempted cleanup
        mock_unlink.assert_called_once_with("/tmp/claude_prompt_test.md")


class TestClaudePromptGeneration:
    """Test Claude prompt generation and content validation"""
    
    @pytest.fixture
    def vibe_framework(self):
        """Create vibe check framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework("mock_token")
    
    @pytest.fixture
    def complex_issue_data(self):
        """Complex issue data for comprehensive prompt testing"""
        return {
            "number": 123,
            "title": "Feature: Enterprise microservices architecture with custom authentication",
            "body": """We need to build a sophisticated enterprise microservices architecture with:
            - Custom authentication system instead of using Auth0
            - Custom HTTP server framework
            - Complex orchestration system
            - Advanced caching layer
            - Custom API gateway
            
            This should integrate with cognee, openai, postgres, redis, and docker.
            The architecture needs to be enterprise-grade and sophisticated.""",
            "author": "enterprise_dev",
            "repository": "company/enterprise-system",
            "labels": ["feature", "enterprise", "architecture"]
        }
    
    @pytest.fixture 
    def complex_patterns(self):
        """Complex pattern detection results"""
        return [
            DetectionResult(
                pattern_type="infrastructure_without_implementation",
                detected=True,
                confidence=0.9,
                evidence=["custom authentication", "custom HTTP server", "instead of using"],
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
    
    def test_prompt_generation_basic_content(self, vibe_framework):
        """Test basic prompt generation content and structure"""
        issue_data = {
            "title": "Simple feature request",
            "body": "Add a simple API endpoint",
            "author": "developer",
            "repository": "test/repo",
            "labels": ["feature"]
        }
        
        patterns = []
        
        prompt = vibe_framework._create_sophisticated_vibe_prompt(issue_data, patterns)
        
        # Verify prompt contains required sections
        assert "🎯 Issue Vibe Check Request" in prompt
        assert "🧠 Pattern Detection Results" in prompt
        assert "🔍 Vibe Check Framework" in prompt
        assert "💡 Friendly Recommendations" in prompt
        
        # Verify issue information is included
        assert issue_data["title"] in prompt
        assert issue_data["body"] in prompt
        assert issue_data["author"] in prompt
        assert issue_data["repository"] in prompt
        
        # Verify coaching framework structure
        assert "### 🎯 **Overall Vibe Assessment**" in prompt
        assert "### 🚨 **Integration Risk Check**" in prompt
        assert "### 🔍 **Research Phase Coaching**" in prompt
        assert "### ⚖️ **Complexity Appropriateness Check**" in prompt
        assert "### 🧪 **Success Criteria Vibe Check**" in prompt
        assert "### 🎓 **Learning Opportunities**" in prompt
        assert "### 🎯 **Next Steps Recommendation**" in prompt
    
    def test_prompt_generation_with_patterns(self, vibe_framework, complex_issue_data, complex_patterns):
        """Test prompt generation with detected patterns"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(complex_issue_data, complex_patterns)
        
        # Verify pattern information is included
        assert "infrastructure_without_implementation" in prompt
        assert "over_engineering" in prompt
        
        # Verify pattern names are formatted
        pattern_names = [p.pattern_type for p in complex_patterns if p.detected]
        formatted_patterns = ", ".join(pattern_names)
        assert formatted_patterns in prompt
    
    def test_prompt_generation_third_party_services_detection(self, vibe_framework, complex_issue_data):
        """Test third-party services detection in prompt"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(complex_issue_data, [])
        
        # Should detect services mentioned in issue body
        expected_services = ["cognee", "openai", "postgres", "redis", "docker"]
        for service in expected_services:
            assert service in prompt
    
    def test_prompt_generation_infrastructure_keywords_detection(self, vibe_framework, complex_issue_data):
        """Test infrastructure keywords detection in prompt"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(complex_issue_data, [])
        
        # Should detect infrastructure keywords
        expected_keywords = ["architecture", "server", "docker"]
        for keyword in expected_keywords:
            assert keyword in prompt
    
    def test_prompt_generation_complexity_indicators_detection(self, vibe_framework, complex_issue_data):
        """Test complexity indicators detection in prompt"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(complex_issue_data, [])
        
        # Should detect complexity indicators
        expected_indicators = ["sophisticated", "enterprise", "complex", "advanced"]
        for indicator in expected_indicators:
            assert indicator in prompt
    
    def test_prompt_generation_integration_risk_assessment(self, vibe_framework):
        """Test integration risk assessment prompt generation"""
        # Test with no third-party services
        risk_prompt_none = vibe_framework._generate_integration_risk_prompt([])
        assert "No obvious third-party integration detected" in risk_prompt_none
        assert "Standard development process applies" in risk_prompt_none
        
        # Test with third-party services
        services = ["cognee", "openai", "postgres"]
        risk_prompt_services = vibe_framework._generate_integration_risk_prompt(services)
        assert "Third-party services detected" in risk_prompt_services
        assert "cognee, openai, postgres" in risk_prompt_services
        assert "Key Questions" in risk_prompt_services
        assert "Red Flags to Check" in risk_prompt_services
        assert "infrastructure-without-implementation" in risk_prompt_services
    
    def test_prompt_generation_complexity_assessment(self, vibe_framework):
        """Test complexity assessment prompt generation"""
        # Test with no complexity indicators
        complexity_prompt_none = vibe_framework._generate_complexity_prompt([])
        assert "No obvious over-engineering indicators" in complexity_prompt_none
        assert "appropriately scoped" in complexity_prompt_none
        
        # Test with complexity indicators
        indicators = ["sophisticated", "enterprise", "complex"]
        complexity_prompt_indicators = vibe_framework._generate_complexity_prompt(indicators)
        assert "Complexity indicators detected" in complexity_prompt_indicators
        assert "sophisticated, enterprise, complex" in complexity_prompt_indicators
        assert "Complexity Check Questions" in complexity_prompt_indicators
        assert "justified over simple" in complexity_prompt_indicators
    
    def test_prompt_generation_friendly_language(self, vibe_framework, complex_issue_data):
        """Test that prompt uses friendly, coaching language"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(complex_issue_data, [])
        
        # Should use friendly, encouraging language
        friendly_phrases = [
            "friendly engineering coach",
            "vibe check",
            "helpful, non-intimidating guidance",
            "encouraging learning",
            "Let's",
            "Great",
            "Love"
        ]
        
        # Should contain some friendly phrases
        assert any(phrase in prompt for phrase in friendly_phrases)
        
        # Should not use harsh technical jargon
        harsh_phrases = [
            "anti-pattern",
            "violation",
            "failure",
            "wrong",
            "bad practice"
        ]
        
        # Should avoid harsh language
        assert not any(phrase in prompt for phrase in harsh_phrases)
    
    def test_prompt_generation_vibe_level_recommendations(self, vibe_framework, complex_issue_data):
        """Test that prompt includes all vibe level recommendations"""
        prompt = vibe_framework._create_sophisticated_vibe_prompt(complex_issue_data, [])
        
        # Should include examples for all vibe levels
        vibe_levels = [
            "Good Vibes (✅)",
            "Needs Research (🔍)",
            "Needs POC (🧪)",
            "Complex Vibes (⚖️)",
            "Bad Vibes (🚨)"
        ]
        
        for vibe_level in vibe_levels:
            assert vibe_level in prompt
        
        # Should include specific guidance for each level
        specific_guidance = [
            "solid plan and appropriate scope",
            "do some homework first",
            "basic functionality first",
            "simpler approach first",
            "infrastructure without proving basic functionality"
        ]
        
        for guidance in specific_guidance:
            assert guidance in prompt


class TestClaudeIntegrationSecurity:
    """Test security aspects of Claude CLI integration"""
    
    @pytest.fixture
    def vibe_framework(self):
        """Create vibe check framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework("mock_token")
    
    def test_temporary_file_security(self, vibe_framework):
        """Test that temporary files are handled securely"""
        issue_data = {
            "title": "Test issue with sensitive data",
            "body": "API_KEY=secret123 PASSWORD=admin",
            "author": "user",
            "repository": "test/repo",
            "labels": []
        }
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            with patch('vibe_check.tools.vibe_check_framework.subprocess.run') as mock_run:
                with patch('os.unlink') as mock_unlink:
                    # Setup mocks
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/secure_test.md"
                    mock_tempfile.return_value.__enter__.return_value = mock_file
                    
                    mock_run.return_value = MagicMock(returncode=0, stdout="result", stderr="")
                    
                    vibe_framework._run_claude_analysis(issue_data, [])
                    
                    # Verify temporary file is created with secure settings
                    mock_tempfile.assert_called_once_with(mode='w', suffix='.md', delete=False)
                    
                    # Verify file is always cleaned up
                    mock_unlink.assert_called_once_with("/tmp/secure_test.md")
    
    def test_subprocess_security_settings(self, vibe_framework):
        """Test that subprocess is called with secure settings"""
        issue_data = {"title": "Test", "body": "Test", "author": "user", "repository": "repo", "labels": []}
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            with patch('vibe_check.tools.vibe_check_framework.subprocess.run') as mock_run:
                with patch('os.unlink'):
                    # Setup mocks
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/security_test.md"
                    mock_tempfile.return_value.__enter__.return_value = mock_file
                    
                    mock_run.return_value = MagicMock(returncode=0, stdout="result", stderr="")
                    
                    vibe_framework._run_claude_analysis(issue_data, [])
                    
                    # Verify subprocess security settings
                    mock_run.assert_called_once()
                    call_kwargs = mock_run.call_args[1]
                    
                    # Should capture output (not inherit from parent)
                    assert call_kwargs['capture_output'] is True
                    
                    # Should use text mode
                    assert call_kwargs['text'] is True
                    
                    # Should have timeout to prevent hanging
                    assert call_kwargs['timeout'] == 60
    
    def test_prompt_content_sanitization(self, vibe_framework):
        """Test that prompt content is properly handled"""
        # Test with potentially problematic content
        issue_data = {
            "title": "Feature with special chars: <script>alert('xss')</script>",
            "body": "Content with newlines\nand special chars: & < > \" '",
            "author": "test_user",
            "repository": "test/repo",
            "labels": ["test"]
        }
        
        prompt = vibe_framework._create_sophisticated_vibe_prompt(issue_data, [])
        
        # Verify content is included (we're not sanitizing for HTML, just preserving content)
        assert issue_data["title"] in prompt
        assert issue_data["body"] in prompt
        
        # Verify prompt structure is maintained
        assert "🎯 Issue Vibe Check Request" in prompt
        assert "🔍 Vibe Check Framework" in prompt


class TestClaudeIntegrationEdgeCases:
    """Test edge cases and boundary conditions for Claude integration"""
    
    @pytest.fixture
    def vibe_framework(self):
        """Create vibe check framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework("mock_token")
    
    def test_empty_issue_content(self, vibe_framework):
        """Test Claude integration with empty issue content"""
        empty_issue = {
            "title": "",
            "body": "",
            "author": "user",
            "repository": "repo",
            "labels": []
        }
        
        prompt = vibe_framework._create_sophisticated_vibe_prompt(empty_issue, [])
        
        # Should still generate valid prompt structure
        assert "🎯 Issue Vibe Check Request" in prompt
        assert "🔍 Vibe Check Framework" in prompt
        
        # Should handle empty content gracefully
        assert "**Title:**" in prompt
        assert "**Issue Content:**" in prompt
    
    def test_very_large_issue_content(self, vibe_framework):
        """Test Claude integration with very large issue content"""
        large_content = "A" * 10000  # 10KB of content
        large_issue = {
            "title": "Large issue title",
            "body": large_content,
            "author": "user",
            "repository": "repo",
            "labels": []
        }
        
        prompt = vibe_framework._create_sophisticated_vibe_prompt(large_issue, [])
        
        # Should include the large content
        assert large_content in prompt
        
        # Should still maintain prompt structure
        assert "🎯 Issue Vibe Check Request" in prompt
        assert "🔍 Vibe Check Framework" in prompt
    
    def test_unicode_content_handling(self, vibe_framework):
        """Test Claude integration with Unicode content"""
        unicode_issue = {
            "title": "Unicode test: 🚀 API интеграция с системой 北京",
            "body": "Content with émojis 🎯, açcénts, and 中文字符",
            "author": "developer_国际",
            "repository": "test/repo",
            "labels": ["🏷️ unicode"]
        }
        
        prompt = vibe_framework._create_sophisticated_vibe_prompt(unicode_issue, [])
        
        # Should preserve Unicode content
        assert "🚀 API интеграция с системой 北京" in prompt
        assert "émojis 🎯, açcénts, and 中文字符" in prompt
        assert "developer_国际" in prompt
        
        # Should maintain prompt structure
        assert "🎯 Issue Vibe Check Request" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])