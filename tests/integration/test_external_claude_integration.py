"""
Integration tests for external Claude CLI integration.

Tests the full integration between MCP tools and external Claude CLI including:
- End-to-end external Claude CLI execution
- MCP server tool registration and execution
- Real subprocess integration (with mocked Claude CLI)
- Performance and timeout validation
- Error handling across the integration stack
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import integration components
from vibe_check.server import mcp
from vibe_check.tools.analyze_llm_backup import ExternalClaudeCli
from vibe_check.tools.legacy.review_pr_monolithic_backup import PRReviewTool


class TestExternalClaudeIntegration:
    """Integration tests for external Claude CLI functionality."""

    def setup_method(self):
        """Set up integration test environment."""
        self.cli = ExternalClaudeCli(timeout_seconds=30)
        self.pr_tool = PRReviewTool()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_external_claude_cli_mock_execution(self):
        """Test external Claude CLI execution with mocked subprocess."""
        # Mock successful Claude CLI response
        mock_response = {
            "result": "This is a test analysis of the provided content.",
            "cost_usd": 0.15,
            "duration_ms": 2500,
            "session_id": "test-session-123",
            "num_turns": 1,
            "is_error": False,
        }

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = asyncio.coroutine(
            lambda: (json.dumps(mock_response).encode("utf-8"), b"")
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.cli.execute_claude_cli(
                prompt="Analyze this test content for quality issues.",
                task_type="general",
            )

        assert result.success is True
        assert result.output == "This is a test analysis of the provided content."
        assert result.cost_usd == 0.15
        assert result.duration_ms == 2500
        assert result.session_id == "test-session-123"
        assert result.task_type == "general"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_external_claude_cli_error_handling(self):
        """Test external Claude CLI error handling."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = asyncio.coroutine(
            lambda: (b"", b"Error: API authentication failed")
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.cli.execute_claude_cli(
                prompt="Test prompt", task_type="general"
            )

        assert result.success is False
        assert "API authentication failed" in result.error
        assert result.exit_code == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_external_claude_cli_timeout(self):
        """Test external Claude CLI timeout handling."""
        # Create a CLI with very short timeout for testing
        short_timeout_cli = ExternalClaudeCli(timeout_seconds=1)

        mock_process = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = asyncio.coroutine(lambda: None)

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                result = await short_timeout_cli.execute_claude_cli(
                    prompt="Long running analysis", task_type="general"
                )

        assert result.success is False
        assert "timed out" in result.error.lower()
        assert result.exit_code == -1
        mock_process.kill.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_content_integration(self):
        """Test content analysis integration with context building."""
        mock_response = {
            "result": "Code analysis: The function lacks error handling and documentation.",
            "cost_usd": 0.12,
            "session_id": "analysis-session-456",
        }

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = asyncio.coroutine(
            lambda: (json.dumps(mock_response).encode("utf-8"), b"")
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.cli.analyze_content(
                content="def hello(): print('hello')",
                task_type="code_analysis",
                additional_context="File: hello.py\nLanguage: Python",
            )

        assert result.success is True
        assert "lacks error handling" in result.output
        assert result.cost_usd == 0.12

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_file_integration(self):
        """Test file analysis integration."""
        test_content = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            mock_response = {
                "result": "Function analysis: Missing input validation and error handling.",
                "cost_usd": 0.08,
            }

            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = asyncio.coroutine(
                lambda: (json.dumps(mock_response).encode("utf-8"), b"")
            )

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                result = await self.cli.analyze_file(
                    file_path=temp_path, task_type="code_analysis"
                )

            assert result.success is True
            assert "Missing input validation" in result.output

        finally:
            os.unlink(temp_path)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pr_review_external_claude_integration(self):
        """Test PR review integration with external Claude CLI."""
        # Mock PR data collection
        mock_pr_data = {
            "title": "Feature: Add user authentication",
            "body": "Implements secure user authentication\nFixes #456",
            "author": {"login": "developer"},
            "createdAt": "2023-01-01T12:00:00Z",
            "baseRefName": "main",
            "headRefName": "feature/auth",
            "additions": 250,
            "deletions": 30,
            "files": [
                {"path": "src/auth.py", "additions": 200, "deletions": 10},
                {"path": "tests/test_auth.py", "additions": 50, "deletions": 20},
            ],
        }

        mock_diff = """
diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..abc123
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,50 @@
+import hashlib
+
+def authenticate_user(username, password):
+    # Authentication logic here
+    return True
"""

        # Mock Claude analysis response
        mock_claude_response = {
            "result": """
## 🎯 Overview
This PR implements user authentication functionality with secure password handling.

## ✅ Strengths
- Good separation of concerns
- Proper import statements
- Clear function naming

## ⚠️ Critical Issues
- Missing input validation for username/password
- Hardcoded return value instead of actual authentication
- No rate limiting or brute force protection

## 💡 Enhancement Suggestions
- Add comprehensive input validation
- Implement proper password hashing
- Add logging for security events
""",
            "cost_usd": 0.35,
            "duration_ms": 3200,
            "session_id": "pr-review-789",
        }

        mock_pr_result = MagicMock()
        mock_pr_result.stdout = json.dumps(mock_pr_data)

        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 0
        mock_diff_result.stdout = mock_diff

        mock_comment_result = MagicMock()
        mock_comment_result.stdout = "Comment posted successfully"

        mock_claude_process = MagicMock()
        mock_claude_process.returncode = 0
        mock_claude_process.communicate = asyncio.coroutine(
            lambda: (json.dumps(mock_claude_response).encode("utf-8"), b"")
        )

        # Mock the subprocess calls in order: gh pr view, gh pr diff, Claude CLI, gh pr comment
        mock_github_result = {
            "comment_posted": True,
            "comment_result": "Comment posted successfully",
            "labels_added": [],
            "re_review_label": False,
            "github_url": "https://github.com/test/repo/pull/456",
        }

        with patch(
            "subprocess.run",
            side_effect=[mock_pr_result, mock_diff_result, mock_comment_result],
        ):
            with patch(
                "asyncio.create_subprocess_exec", return_value=mock_claude_process
            ):
                with patch.object(
                    self.pr_tool, "_check_claude_availability", return_value=True
                ):
                    with patch.object(
                        self.pr_tool,
                        "_post_review_to_github",
                        return_value=mock_github_result,
                    ):
                        result = await self.pr_tool.review_pull_request(
                            pr_number=456,
                            repository="test/repo",
                            analysis_mode="comprehensive",
                        )

        assert result["pr_number"] == 456
        assert result["analysis"]["analysis_method"] == "external-claude-cli"
        assert result["analysis"]["cost_usd"] == 0.35
        assert result["github_integration"]["comment_posted"] is True

    @pytest.mark.integration
    def test_system_prompt_specialization(self):
        """Test that different task types get appropriate system prompts."""
        pr_prompt = self.cli._get_system_prompt("pr_review")
        code_prompt = self.cli._get_system_prompt("code_analysis")
        issue_prompt = self.cli._get_system_prompt("issue_analysis")

        # PR review prompt should mention code reviews
        assert "code review" in pr_prompt.lower()
        assert "pull request" in pr_prompt.lower() or "pr" in pr_prompt.lower()

        # Code analysis prompt should mention anti-patterns
        assert "anti-pattern" in code_prompt.lower()
        assert "code analyst" in code_prompt.lower()

        # Issue analysis prompt should mention requirements
        assert "requirements" in issue_prompt.lower()
        assert "technical product manager" in issue_prompt.lower()

    @pytest.mark.integration
    def test_environment_isolation(self):
        """Test that execution environments are properly isolated."""
        import time

        env1 = self.cli._create_isolated_environment()
        time.sleep(0.001)  # Ensure different timestamps
        env2 = self.cli._create_isolated_environment()

        # Each environment should have unique task IDs
        assert env1["CLAUDE_TASK_ID"] != env2["CLAUDE_TASK_ID"]

        # Both should have isolation markers
        assert env1["CLAUDE_EXTERNAL_EXECUTION"] == "true"
        assert env2["CLAUDE_EXTERNAL_EXECUTION"] == "true"

        # Conflicting variables should be removed
        for var in ["CLAUDE_CODE_MODE", "CLAUDE_CLI_SESSION", "MCP_SERVER"]:
            assert var not in env1
            assert var not in env2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_content_handling(self):
        """Test handling of large content payloads."""
        # Create large content (100KB)
        large_content = "This is a test line.\n" * 5000

        mock_response = {
            "result": "Large content analysis completed successfully.",
            "cost_usd": 0.50,
        }

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = asyncio.coroutine(
            lambda: (json.dumps(mock_response).encode("utf-8"), b"")
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.cli.analyze_content(
                content=large_content, task_type="general"
            )

        assert result.success is True
        assert "Large content analysis" in result.output

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_executions(self):
        """Test multiple concurrent external Claude executions."""
        mock_responses = [
            {"result": f"Analysis {i} complete", "cost_usd": 0.1 + i * 0.05}
            for i in range(3)
        ]

        async def mock_communicate(response):
            await asyncio.sleep(0.1)  # Simulate some processing time
            return (json.dumps(response).encode("utf-8"), b"")

        mock_processes = []
        for response in mock_responses:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = lambda r=response: mock_communicate(r)
            mock_processes.append(mock_process)

        with patch("asyncio.create_subprocess_exec", side_effect=mock_processes):
            # Execute multiple analyses concurrently
            tasks = [
                self.cli.analyze_content(f"Content {i}", "general") for i in range(3)
            ]
            results = await asyncio.gather(*tasks)

        # All should succeed
        for i, result in enumerate(results):
            assert result.success is True
            assert f"Analysis {i}" in result.output

    @pytest.mark.integration
    def test_command_construction_integration(self):
        """Test that commands are constructed correctly for different scenarios."""
        # Test with custom Claude path
        self.cli.claude_cli_path = "/custom/path/to/claude"
        self.cli.timeout_seconds = 45

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = asyncio.coroutine(
                lambda: (b'{"result": "test"}', b"")
            )
            mock_exec.return_value = mock_process

            asyncio.run(
                self.cli.execute_claude_cli(
                    prompt="Test analysis prompt",
                    task_type="code_analysis",
                    additional_args=["--verbose"],
                )
            )

        # Verify command construction
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]

        expected_command = [
            "timeout",
            "50",  # timeout + 5
            "/custom/path/to/claude",
            "-p",
            "Test analysis prompt",
            "--output-format",
            "json",
            "--system-prompt",
            # system prompt content would be next
        ]

        # Check the base command structure
        assert args[:7] == tuple(expected_command[:7])
        assert "--verbose" in args  # Additional args should be included

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self):
        """Test various error recovery scenarios."""
        # Test JSON parsing fallback
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = asyncio.coroutine(
            lambda: (b"Plain text response", b"")
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.cli.execute_claude_cli(
                prompt="Test prompt", task_type="general"
            )

        assert result.success is True
        assert result.output == "Plain text response"
        assert result.cost_usd is None  # No SDK metadata available

    @pytest.mark.integration
    def test_debug_file_integration(self):
        """Test debug file creation and cleanup."""
        # This would test actual debug file creation in a real scenario
        # For now, we verify the debug logic exists in the PR review integration
        assert hasattr(self.pr_tool, "_run_claude_analysis")

        # In a real test, we would verify:
        # - Debug files are created in /tmp/
        # - They contain proper execution metadata
        # - They're cleaned up appropriately


class TestMCPServerIntegration:
    """Integration tests for MCP server with external Claude tools."""

    @pytest.mark.integration
    def test_external_claude_tools_registration(self):
        """Test that external Claude tools are properly registered with MCP server."""
        # Verify that the tools are available in the server
        # This would require accessing the FastMCP server's tool registry
        pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_tool_execution_mock(self):
        """Test MCP tool execution with mocked external processes."""
        # This would test the actual MCP tool execution
        # Requires setting up a test MCP client
        pass


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
