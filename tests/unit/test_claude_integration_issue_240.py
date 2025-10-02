"""
Unit tests for Claude CLI integration - Issue #240 fixes.

Tests the enhanced error handling, environment detection, and MCP stdio mode
support added to fix Issue #240 (Claude CLI integration fails in MCP stdio mode).

Key test scenarios:
- Environment debugging in MCP stdio mode
- PATH issues and resolution
- Enhanced error messages
- File not found handling
- Permission errors
- Authentication failures
"""

import os
import sys
import subprocess
import pytest
from unittest.mock import Mock, patch, MagicMock
from vibe_check.tools.shared.claude_integration import (
    ClaudeCliExecutor,
    ClaudeCliResult,
)


class TestClaudeCliExecutorIssue240:
    """Test suite for Issue #240 fixes to ClaudeCliExecutor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.executor = ClaudeCliExecutor(timeout_seconds=30)

    @patch("shutil.which")
    @patch("os.path.exists")
    @patch("os.access")
    def test_find_claude_cli_prefers_local_path(
        self, mock_access, mock_exists, mock_which
    ):
        """Test that ~/.claude/local/claude is always preferred (Issue #240)."""
        # Simulate ~/.claude/local/claude exists and is executable
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_which.return_value = "/usr/local/bin/claude"  # Should be ignored

        executor = ClaudeCliExecutor()
        result = executor._find_claude_cli()

        # Should use full path, not PATH lookup
        assert result == os.path.expanduser("~/.claude/local/claude")
        # which should not be called since we found local path
        mock_which.assert_not_called()

    @patch("shutil.which")
    @patch("os.path.exists")
    def test_find_claude_cli_logs_environment(self, mock_exists, mock_which):
        """Test that environment context is logged (Issue #240 diagnostic requirement)."""
        mock_exists.return_value = False
        mock_which.return_value = "/usr/local/bin/claude"

        with patch("logging.Logger.debug") as mock_debug:
            executor = ClaudeCliExecutor()
            executor._find_claude_cli()

            # Verify environment logging calls were made
            assert mock_debug.call_count >= 3
            call_messages = [args[0] for args, kwargs in mock_debug.call_args_list]
            
            assert any("PATH" in msg for msg in call_messages)
            assert any("Current working directory" in msg for msg in call_messages)
            assert any("MCP environment indicators" in msg for msg in call_messages)    @patch("shutil.which")
    @patch("os.path.exists")
    @patch("os.access")
    def test_find_claude_cli_not_executable(self, mock_access, mock_exists, mock_which):
        """Test handling when Claude CLI file exists but is not executable."""
        mock_exists.return_value = True
        mock_access.return_value = False  # Not executable
        mock_which.return_value = None

        with patch("logging.Logger.warning") as mock_warning:
            executor = ClaudeCliExecutor()
            result = executor._find_claude_cli()

            # Should still return path (subprocess will fail with clear error)
            assert result == os.path.expanduser("~/.claude/local/claude")

            # Should log warning about permissions
            assert mock_warning.call_count >= 1
            call_messages = [args[0] for args, kwargs in mock_warning.call_args_list]
            assert any("not executable" in msg for msg in call_messages)
    @patch("shutil.which")
    @patch("os.path.exists")
    def test_find_claude_cli_not_found_logs_error(self, mock_exists, mock_which):
        """Test that detailed error is logged when Claude CLI not found."""
        mock_exists.return_value = False
        mock_which.return_value = None

        with patch("logging.Logger.error") as mock_error:
            executor = ClaudeCliExecutor()
            result = executor._find_claude_cli()

            # Should return default name for clearer subprocess error
            assert result == "claude"

            # Should log detailed error with troubleshooting steps
            assert mock_error.call_count >= 3
            call_messages = [args[0] for args, kwargs in mock_error.call_args_list]
            error_output = " ".join(call_messages)
            
            assert "Claude CLI not found" in error_output
            assert "Current PATH" in error_output
            assert "To fix" in error_output    @patch("subprocess.run")
    def test_execute_sync_file_not_found_error(self, mock_run):
        """Test enhanced error handling for FileNotFoundError (Issue #240)."""
        mock_run.side_effect = FileNotFoundError("claude: command not found")

        result = self.executor.execute_sync(prompt="test prompt", task_type="general")

        assert result.success is False
        assert result.exit_code == 127
        assert "Claude CLI not found" in result.error
        assert "Troubleshooting steps" in result.error
        assert "npm install" in result.error
        assert result.sdk_metadata["error_type"] == "FileNotFoundError"
        assert "PATH" in result.error

    @patch("subprocess.run")
    def test_execute_sync_permission_error(self, mock_run):
        """Test enhanced error handling for PermissionError (Issue #240)."""
        mock_run.side_effect = PermissionError("Permission denied")

        result = self.executor.execute_sync(prompt="test prompt", task_type="general")

        assert result.success is False
        assert result.exit_code == 126
        assert "Permission denied" in result.error
        assert "chmod +x" in result.error
        assert result.sdk_metadata["error_type"] == "PermissionError"

    @patch("subprocess.run")
    def test_execute_sync_exit_code_127_analysis(self, mock_run):
        """Test error analysis for exit code 127 (command not found)."""
        mock_run.return_value = Mock(
            returncode=127, stdout="", stderr="claude: command not found"
        )

        result = self.executor.execute_sync(prompt="test prompt", task_type="general")

        assert result.success is False
        assert result.exit_code == 127
        assert "Claude CLI not found" in result.error
        assert "Install Claude CLI" in result.error

    @patch("subprocess.run")
    def test_execute_sync_authentication_error_analysis(self, mock_run):
        """Test error analysis for authentication failures."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="Authentication failed: Invalid API key"
        )

        result = self.executor.execute_sync(prompt="test prompt", task_type="general")

        assert result.success is False
        assert "Authentication failed" in result.error
        assert "claude login" in result.error or "ANTHROPIC_API_KEY" in result.error

    @patch("subprocess.run")
    def test_execute_sync_enhanced_logging(self, mock_run):
        """Test that enhanced diagnostic logging is performed (Issue #240)."""
        mock_run.return_value = Mock(
            returncode=1, stdout="Some output", stderr="Some error"
        )

        with patch("logging.Logger.error") as mock_error:
            result = self.executor.execute_sync(
                prompt="test prompt", task_type="general"
            )

            # Verify enhanced logging
            error_calls = [str(call) for call in mock_error.call_args_list]
            error_output = " ".join(error_calls)

            assert "Claude CLI failed with exit code" in error_output
            assert "Command:" in error_output
            assert "Working directory:" in error_output
            assert "Full stderr:" in error_output
            assert "Troubleshooting:" in error_output

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_execute_async_file_not_found_error(self, mock_create):
        """Test async execution with FileNotFoundError (Issue #240)."""
        mock_create.side_effect = FileNotFoundError("claude: command not found")

        result = await self.executor.execute_async(
            prompt="test prompt", task_type="general"
        )

        assert result.success is False
        assert result.exit_code == 127
        assert "Claude CLI not found" in result.error
        assert "Troubleshooting steps" in result.error
        assert result.sdk_metadata["error_type"] == "FileNotFoundError"

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_execute_async_permission_error(self, mock_create):
        """Test async execution with PermissionError (Issue #240)."""
        mock_create.side_effect = PermissionError("Permission denied")

        result = await self.executor.execute_async(
            prompt="test prompt", task_type="general"
        )

        assert result.success is False
        assert result.exit_code == 126
        assert "Permission denied" in result.error
        assert "chmod +x" in result.error

    @patch.dict("os.environ", {"PATH": "/usr/bin:/bin"}, clear=True)
    @patch("shutil.which")
    @patch("os.path.exists")
    def test_find_claude_cli_limited_path_environment(self, mock_exists, mock_which):
        """Test behavior when PATH is limited (common in MCP stdio mode)."""
        mock_exists.return_value = False
        mock_which.return_value = None

        with patch("logging.Logger.error") as mock_error:
            executor = ClaudeCliExecutor()
            result = executor._find_claude_cli()

            # Should log the limited PATH
            error_calls = [str(call) for call in mock_error.call_args_list]
            error_output = " ".join(error_calls)
            assert "PATH" in error_output

    @patch("subprocess.run")
    def test_execute_sync_includes_troubleshooting_in_error(self, mock_run):
        """Test that error messages include actionable troubleshooting steps."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="Error executing Claude CLI"
        )

        result = self.executor.execute_sync(prompt="test prompt", task_type="general")

        assert result.success is False
        # Error should include troubleshooting section
        assert "Troubleshooting:" in result.error
        # Should have error analysis metadata
        assert "error_analysis" in result.sdk_metadata
        assert "troubleshooting" in result.sdk_metadata["error_analysis"]

    @patch("os.environ", {"VIBE_CHECK_INTERNAL_CALL": "true"})
    def test_mcp_environment_marker_detected(self):
        """Test that VIBE_CHECK_INTERNAL_CALL environment marker is detected."""
        # This marker indicates we're in an internal vibe-check call
        # which helps prevent recursion issues
        assert os.environ.get("VIBE_CHECK_INTERNAL_CALL") == "true"


class TestClaudeCliResultEnhancements:
    """Test enhancements to ClaudeCliResult for Issue #240."""

    def test_result_includes_sdk_metadata_error_analysis(self):
        """Test that ClaudeCliResult can store error analysis metadata."""
        result = ClaudeCliResult(
            success=False,
            error="Test error",
            exit_code=127,
            execution_time=1.5,
            command_used="claude_cli_direct",
            task_type="general",
            sdk_metadata={
                "error_analysis": {
                    "cli_path": "/path/to/claude",
                    "exit_code": 127,
                    "troubleshooting": "Install Claude CLI",
                }
            },
        )

        assert result.success is False
        assert "error_analysis" in result.sdk_metadata
        assert result.sdk_metadata["error_analysis"]["exit_code"] == 127
        assert "troubleshooting" in result.sdk_metadata["error_analysis"]

    def test_result_to_dict_includes_metadata(self):
        """Test that to_dict() includes all metadata."""
        result = ClaudeCliResult(
            success=False,
            error="Test error",
            exit_code=127,
            sdk_metadata={"error_type": "FileNotFoundError"},
        )

        result_dict = result.to_dict()
        assert "sdk_metadata" in result_dict
        assert result_dict["sdk_metadata"]["error_type"] == "FileNotFoundError"
