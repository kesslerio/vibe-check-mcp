"""
Unit Tests for Vibe Check Framework Claude CLI Integration

Tests the Claude CLI integration components:
- Claude availability detection
- Analysis execution and prompt generation
- Security and edge case handling
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile
import subprocess

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.vibe_check_framework import (
    VibeCheckFramework,
    VibeCheckMode,
    VibeLevel,
    VibeCheckResult
)
from vibe_check.core.educational_content import DetailLevel


class TestVibeCheckFrameworkClaudeIntegration:
    """Test Claude CLI integration functionality"""
    
    @pytest.fixture
    def framework(self):
        """Create framework instance for testing"""
        with patch('vibe_check.tools.vibe_check_framework.Github'):
            return VibeCheckFramework()
    
    @patch('shutil.which')
    def test_claude_availability_detection_available(self, mock_which, framework):
        """Test Claude CLI availability detection when available"""
        mock_which.return_value = "/usr/local/bin/claude"
        
        available = framework._is_claude_available()
        
        assert available is True
        mock_which.assert_called_once_with("claude")
    
    @patch('shutil.which')
    def test_claude_availability_detection_unavailable(self, mock_which, framework):
        """Test Claude CLI availability detection when unavailable"""
        mock_which.return_value = None
        
        available = framework._is_claude_available()
        
        assert available is False
        mock_which.assert_called_once_with("claude")
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_claude_analysis_execution_success(self, mock_temp_file, mock_subprocess, framework):
        """Test successful Claude analysis execution"""
        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_prompt.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Mock successful subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Claude analysis result"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Test analysis
        result = framework._run_claude_analysis("Test prompt")
        
        # Verify result
        assert result == "Claude analysis result"
        mock_subprocess.assert_called_once()
        
        # Verify command structure
        call_args = mock_subprocess.call_args[0][0]
        assert "claude" in call_args
        assert "/tmp/test_prompt.txt" in call_args
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_claude_analysis_execution_failure(self, mock_temp_file, mock_subprocess, framework):
        """Test Claude analysis execution failure"""
        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_prompt.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Mock failed subprocess
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Claude error"
        mock_subprocess.return_value = mock_result
        
        # Test analysis failure
        result = framework._run_claude_analysis("Test prompt")
        
        # Should return None on failure
        assert result is None
    
    def test_claude_prompt_generation_comprehensive(self, framework):
        """Test Claude prompt generation for comprehensive analysis"""
        issue_data = {
            "title": "Test Issue",
            "body": "Test content for analysis",
            "number": 42,
            "repository": "test/repo"
        }
        
        prompt = framework._generate_claude_prompt(issue_data, DetailLevel.COMPREHENSIVE)
        
        # Verify prompt structure
        assert "Test Issue" in prompt
        assert "Test content for analysis" in prompt
        assert "comprehensive" in prompt.lower()
        assert "anti-pattern" in prompt.lower()
        assert len(prompt) > 200  # Should be substantial
    
    def test_claude_prompt_generation_brief(self, framework):
        """Test Claude prompt generation for brief analysis"""
        issue_data = {
            "title": "Brief Test",
            "body": "Brief content",
            "number": 1,
            "repository": "test/repo"
        }
        
        prompt = framework._generate_claude_prompt(issue_data, DetailLevel.BRIEF)
        
        # Verify prompt structure
        assert "Brief Test" in prompt
        assert "Brief content" in prompt
        assert len(prompt) < 1000  # Should be concise
    
    @patch('tempfile.NamedTemporaryFile')
    def test_claude_security_prompt_sanitization(self, mock_temp_file, framework):
        """Test that prompts are properly sanitized for security"""
        # Mock file
        mock_file = MagicMock()
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Test with potentially dangerous content
        dangerous_issue = {
            "title": "Test $(rm -rf /)",
            "body": "Content with `malicious command`",
            "number": 42,
            "repository": "test/repo"
        }
        
        prompt = framework._generate_claude_prompt(dangerous_issue, DetailLevel.STANDARD)
        
        # Verify dangerous content is handled safely
        assert "$(rm -rf /)" in prompt  # Should be preserved as text, not executed
        assert "`malicious command`" in prompt  # Should be preserved as text
    
    @patch('subprocess.run')
    def test_claude_timeout_handling(self, mock_subprocess, framework):
        """Test Claude CLI timeout handling"""
        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired("claude", 30)
        
        result = framework._run_claude_analysis("Test prompt")
        
        # Should handle timeout gracefully
        assert result is None
    
    @patch('os.path.exists')
    @patch('tempfile.NamedTemporaryFile')
    def test_claude_file_cleanup(self, mock_temp_file, mock_exists, framework):
        """Test that temporary files are cleaned up properly"""
        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_prompt.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        # Mock file existence
        mock_exists.return_value = True
        
        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Test result"
            mock_subprocess.return_value = mock_result
            
            framework._run_claude_analysis("Test prompt")
        
        # Verify context manager properly handles cleanup
        mock_temp_file.assert_called_once()
        mock_temp_file.return_value.__enter__.assert_called_once()
        mock_temp_file.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])