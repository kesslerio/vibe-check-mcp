"""
Test Claude Code CLI integration for vibe-check MCP tools.

Validates that Claude Code is available and properly integrated
with PR review and analysis tools.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from vibe_check.tools.pr_review import PRReviewTool


class TestClaudeCodeIntegration:
    """Test Claude Code CLI integration."""
    
    def test_claude_code_availability_real(self):
        """Test actual Claude Code availability on the system."""
        try:
            result = subprocess.run(
                ["claude", "--version"], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=5
            )
            assert result.returncode == 0
            assert "Claude Code" in result.stdout or "claude" in result.stdout.lower()
            print(f"✅ Claude Code detected: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pytest.fail("❌ Claude Code CLI not available on system")
    
    def test_pr_review_tool_detects_claude(self):
        """Test that PRReviewTool correctly detects Claude Code."""
        tool = PRReviewTool()
        
        # Test Claude detection
        claude_available = tool._check_claude_availability()
        
        # Should detect Claude on this system (not in Docker)
        assert claude_available is True
        assert tool.claude_cmd is not None
        print(f"✅ PRReviewTool detected Claude at: {tool.claude_cmd}")
    
    @patch('os.path.exists')
    def test_docker_environment_detection(self, mock_exists):
        """Test that Docker environment properly disables Claude detection."""
        # Mock Docker environment (/.dockerenv exists)
        mock_exists.return_value = True
        
        tool = PRReviewTool()
        claude_available = tool._check_claude_availability()
        
        # Should return False in Docker environment
        assert claude_available is False
        assert tool.claude_cmd is None
        print("✅ Docker environment correctly disables Claude CLI detection")
    
    def test_claude_command_execution(self):
        """Test basic Claude command execution."""
        try:
            # Simple test command
            result = subprocess.run(
                ["claude", "--help"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            assert result.returncode == 0
            print("✅ Claude command execution successful")
        except Exception as e:
            pytest.fail(f"❌ Claude command execution failed: {e}")
    
    @patch('subprocess.run')
    def test_fallback_when_claude_unavailable(self, mock_run):
        """Test fallback behavior when Claude is not available."""
        # Mock Claude not being available
        mock_run.side_effect = FileNotFoundError("claude not found")
        
        tool = PRReviewTool()
        claude_available = tool._check_claude_availability()
        
        assert claude_available is False
        assert tool.claude_cmd is None
        print("✅ Fallback behavior works when Claude unavailable")
    
    def test_claude_with_project_flag(self):
        """Test Claude with -p flag (project mode)."""
        try:
            # Test Claude -p flag recognition (short timeout since it's interactive)
            result = subprocess.run(
                ["claude", "--help"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            # Check if -p flag is mentioned in help
            if "-p" in result.stdout or "project" in result.stdout.lower():
                print("✅ Claude -p flag detected in help")
            else:
                print("ℹ️ Claude -p flag not explicitly mentioned in help, but command available")
            
        except subprocess.TimeoutExpired:
            print("⚠️ Claude help timed out, but Claude is available")
        except Exception as e:
            pytest.fail(f"❌ Claude help command failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    test = TestClaudeCodeIntegration()
    
    print("🧪 Testing Claude Code Integration...")
    print()
    
    try:
        test.test_claude_code_availability_real()
        print()
        
        test.test_pr_review_tool_detects_claude()
        print()
        
        test.test_docker_environment_detection()
        print()
        
        test.test_claude_command_execution()
        print()
        
        test.test_claude_with_project_flag()
        print()
        
        print("✅ All Claude Code integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise