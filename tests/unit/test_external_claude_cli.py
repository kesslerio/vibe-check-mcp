"""
Unit tests for external Claude CLI integration.

Tests the ExternalClaudeCli class functionality including:
- CLI path detection and validation
- System prompt generation for different task types
- Isolated environment creation
- Command execution and result parsing
- Error handling and timeout management
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path

import pytest

# Import the class under test
from vibe_check.tools.external_claude_cli import ExternalClaudeCli, ClaudeCliResult


class TestExternalClaudeCli:
    """Test suite for ExternalClaudeCli class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = ExternalClaudeCli(timeout_seconds=30)

    def test_init_default_timeout(self):
        """Test initialization with default timeout."""
        cli = ExternalClaudeCli()
        assert cli.timeout_seconds == 60

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        cli = ExternalClaudeCli(timeout_seconds=120)
        assert cli.timeout_seconds == 120

    @patch('subprocess.run')
    def test_find_claude_cli_success(self, mock_run):
        """Test successful Claude CLI path detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/usr/local/bin/claude\n"
        )
        
        cli = ExternalClaudeCli()
        result = cli._find_claude_cli()
        
        assert result == "/usr/local/bin/claude"
        mock_run.assert_called_once_with(
            ["which", "claude"],
            capture_output=True,
            text=True,
            timeout=10
        )

    @patch('subprocess.run')
    def test_find_claude_cli_not_found(self, mock_run):
        """Test Claude CLI path detection when not found."""
        mock_run.return_value = MagicMock(returncode=1)
        
        cli = ExternalClaudeCli()
        result = cli._find_claude_cli()
        
        assert result == "claude"  # Default fallback

    @patch('subprocess.run', side_effect=Exception("Command failed"))
    def test_find_claude_cli_exception(self, mock_run):
        """Test Claude CLI path detection with exception."""
        cli = ExternalClaudeCli()
        result = cli._find_claude_cli()
        
        assert result == "claude"  # Default fallback

    def test_get_system_prompt_pr_review(self):
        """Test system prompt for PR review task."""
        prompt = self.cli._get_system_prompt("pr_review")
        
        assert "senior software engineer" in prompt.lower()
        assert "code quality" in prompt.lower()
        assert "anti-pattern detection" in prompt.lower()

    def test_get_system_prompt_code_analysis(self):
        """Test system prompt for code analysis task."""
        prompt = self.cli._get_system_prompt("code_analysis")
        
        assert "expert code analyst" in prompt.lower()
        assert "anti-pattern detection" in prompt.lower()
        assert "quality issues" in prompt.lower()

    def test_get_system_prompt_issue_analysis(self):
        """Test system prompt for issue analysis task."""
        prompt = self.cli._get_system_prompt("issue_analysis")
        
        assert "technical product manager" in prompt.lower()
        assert "anti-pattern risk" in prompt.lower()
        assert "requirements quality" in prompt.lower()

    def test_get_system_prompt_general(self):
        """Test system prompt for general task."""
        prompt = self.cli._get_system_prompt("general")
        
        assert "helpful assistant" in prompt.lower()
        assert "actionable insights" in prompt.lower()

    def test_get_system_prompt_unknown_task(self):
        """Test system prompt for unknown task type falls back to general."""
        prompt = self.cli._get_system_prompt("unknown_task")
        
        # Should return general prompt
        general_prompt = self.cli._get_system_prompt("general")
        assert prompt == general_prompt

    def test_create_isolated_environment(self):
        """Test creation of isolated environment variables."""
        env = self.cli._create_isolated_environment()
        
        # Check isolation markers are added
        assert env["CLAUDE_EXTERNAL_EXECUTION"] == "true"
        assert env["CLAUDE_MCP_ISOLATED"] == "true"
        assert "CLAUDE_TASK_ID" in env
        assert env["CLAUDE_TASK_ID"].startswith("external_")
        
        # Check conflicting variables are removed
        for var in ["CLAUDE_CODE_MODE", "CLAUDE_CLI_SESSION", "MCP_SERVER"]:
            assert var not in env

    @pytest.mark.asyncio
    async def test_execute_claude_cli_success_json(self):
        """Test successful Claude CLI execution with JSON response."""
        # Mock successful subprocess execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            json.dumps({
                "result": "Test analysis result",
                "cost_usd": 0.15,
                "duration_ms": 2500,
                "session_id": "test-session-123",
                "num_turns": 1
            }).encode('utf-8'),
            b""
        )

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('asyncio.wait_for', return_value=mock_process.communicate.return_value):
                result = await self.cli.execute_claude_cli(
                    prompt="Test prompt",
                    task_type="general"
                )

        assert result.success is True
        assert result.output == "Test analysis result"
        assert result.cost_usd == 0.15
        assert result.duration_ms == 2500
        assert result.session_id == "test-session-123"
        assert result.num_turns == 1
        assert result.exit_code == 0
        assert result.task_type == "general"

    @pytest.mark.asyncio
    async def test_execute_claude_cli_success_text_fallback(self):
        """Test Claude CLI execution with text fallback when JSON parsing fails."""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            b"Plain text response without JSON",
            b""
        )

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('asyncio.wait_for', return_value=mock_process.communicate.return_value):
                result = await self.cli.execute_claude_cli(
                    prompt="Test prompt",
                    task_type="general"
                )

        assert result.success is True
        assert result.output == "Plain text response without JSON"
        assert result.cost_usd is None
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_claude_cli_error_response(self):
        """Test Claude CLI execution with error response."""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (
            b"",
            b"Error: Invalid command"
        )

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('asyncio.wait_for', return_value=mock_process.communicate.return_value):
                result = await self.cli.execute_claude_cli(
                    prompt="Test prompt",
                    task_type="general"
                )

        assert result.success is False
        assert "Error: Invalid command" in result.error
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_execute_claude_cli_timeout(self):
        """Test Claude CLI execution timeout handling."""
        mock_process = AsyncMock()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                result = await self.cli.execute_claude_cli(
                    prompt="Test prompt",
                    task_type="general"
                )

        assert result.success is False
        assert "timed out" in result.error.lower()
        assert result.exit_code == -1
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_claude_cli_exception(self):
        """Test Claude CLI execution with exception."""
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Process creation failed")):
            result = await self.cli.execute_claude_cli(
                prompt="Test prompt",
                task_type="general"
            )

        assert result.success is False
        assert "Process creation failed" in result.error
        assert result.exit_code == -1

    @pytest.mark.asyncio
    async def test_analyze_content_with_context(self):
        """Test content analysis with additional context."""
        mock_result = ClaudeCliResult(
            success=True,
            output="Analysis complete",
            task_type="code_analysis"
        )

        with patch.object(self.cli, 'execute_claude_cli', return_value=mock_result) as mock_execute:
            result = await self.cli.analyze_content(
                content="Test code content",
                task_type="code_analysis",
                additional_context="File: test.py"
            )

        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert "File: test.py" in kwargs['prompt']
        assert "Test code content" in kwargs['prompt']
        assert kwargs['task_type'] == "code_analysis"

    @pytest.mark.asyncio
    async def test_analyze_content_without_context(self):
        """Test content analysis without additional context."""
        mock_result = ClaudeCliResult(
            success=True,
            output="Analysis complete",
            task_type="general"
        )

        with patch.object(self.cli, 'execute_claude_cli', return_value=mock_result) as mock_execute:
            result = await self.cli.analyze_content(
                content="Test content",
                task_type="general"
            )

        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert "Analyze the following content:" in kwargs['prompt']
        assert "Test content" in kwargs['prompt']

    @pytest.mark.asyncio
    async def test_analyze_file_success(self):
        """Test successful file analysis."""
        file_content = "def hello():\n    print('Hello, world!')"
        
        mock_result = ClaudeCliResult(
            success=True,
            output="File analysis complete",
            task_type="code_analysis"
        )

        with patch('builtins.open', mock_open(read_data=file_content)):
            with patch.object(self.cli, 'analyze_content', return_value=mock_result) as mock_analyze:
                result = await self.cli.analyze_file(
                    file_path="/test/path/test.py",
                    task_type="code_analysis"
                )

        mock_analyze.assert_called_once_with(
            content=file_content,
            task_type="code_analysis",
            additional_context="File: /test/path/test.py\nSize: 39 characters"
        )

    @pytest.mark.asyncio
    async def test_analyze_file_read_error(self):
        """Test file analysis with read error."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = await self.cli.analyze_file(
                file_path="/nonexistent/file.py",
                task_type="code_analysis"
            )

        assert result.success is False
        assert "File read error" in result.error
        assert "File not found" in result.error
        assert result.exit_code == -1

    def test_claude_cli_result_to_dict(self):
        """Test ClaudeCliResult to_dict conversion."""
        result = ClaudeCliResult(
            success=True,
            output="Test output",
            error=None,
            exit_code=0,
            execution_time=2.5,
            command_used="claude test",
            task_type="general",
            cost_usd=0.10,
            duration_ms=2500,
            session_id="test-123",
            num_turns=1,
            sdk_metadata={"model": "claude-3"}
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["output"] == "Test output"
        assert result_dict["error"] is None
        assert result_dict["exit_code"] == 0
        assert result_dict["execution_time_seconds"] == 2.5
        assert result_dict["command_used"] == "claude test"
        assert result_dict["task_type"] == "general"
        assert result_dict["cost_usd"] == 0.10
        assert result_dict["duration_ms"] == 2500
        assert result_dict["session_id"] == "test-123"
        assert result_dict["num_turns"] == 1
        assert result_dict["sdk_metadata"] == {"model": "claude-3"}
        assert "timestamp" in result_dict

    def test_command_construction(self):
        """Test that commands are constructed correctly."""
        self.cli.claude_cli_path = "/usr/local/bin/claude"
        self.cli.timeout_seconds = 60
        
        # Mock the execute method to capture command construction
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b'{"result": "test"}', b"")
            mock_exec.return_value = mock_process
            
            with patch('asyncio.wait_for', return_value=mock_process.communicate.return_value):
                asyncio.run(self.cli.execute_claude_cli("test prompt", "pr_review"))

        # Verify command construction
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        
        assert args[0] == "timeout"
        assert args[1] == "65"  # timeout + 5
        assert args[2] == "/usr/local/bin/claude"
        assert args[3] == "-p"
        assert args[4] == "test prompt"
        assert args[5] == "--output-format"
        assert args[6] == "json"
        assert args[7] == "--system-prompt"
        # args[8] should be the system prompt for pr_review