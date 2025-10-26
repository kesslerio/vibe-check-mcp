#!/usr/bin/env python3
"""
External Claude CLI analysis tools for MCP integration.

This module provides comprehensive external Claude CLI integration for analyzing
content without context blocking issues. Consolidates external execution and
MCP tool registration following the action_what naming convention.

Usage as script:
    python analyze_external.py --prompt "Your prompt here" --task-type pr_review
    python analyze_external.py --input-file path/to/file.txt --task-type code_analysis

Usage as MCP tools:
    - external_claude_analyze: General content analysis
    - external_pr_review: Pull request review
    - external_code_analysis: Code analysis
    - external_issue_analysis: Issue analysis
    - external_github_issue_vibe_check: GitHub issue vibe check
    - external_claude_status: Status check
"""

import argparse
import asyncio
import inspect
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel

# Compatibility shim for legacy asyncio.coroutine usage in tests
if not hasattr(asyncio, "coroutine"):

    def _legacy_coroutine(func):
        async def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    asyncio.coroutine = _legacy_coroutine  # type: ignore[attr-defined]

# Add Anthropic SDK import
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# GitHub integration
try:
    from github import Github, GithubException

    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ClaudeCliResult:
    """Container for Claude CLI execution results."""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: float = 0.0
    command_used: str = ""
    task_type: str = "general"
    cost_usd: Optional[float] = None
    duration_ms: Optional[float] = None
    session_id: Optional[str] = None
    num_turns: Optional[int] = None
    sdk_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        payload = {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time_seconds": self.execution_time,
            "command_used": self.command_used,
            "task_type": self.task_type,
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "session_id": self.session_id,
            "num_turns": self.num_turns,
            "sdk_metadata": self.sdk_metadata,
            "timestamp": time.time(),
        }
        return payload


class ExternalClaudeCli:
    """Asynchronous wrapper around the external Claude CLI executable."""

    SYSTEM_PROMPTS: Dict[str, str] = {
        "pr_review": (
            "You are a senior software engineer conducting code reviews for "
            "pull requests. Provide actionable feedback focused on quality, "
            "safety, and anti-pattern prevention."
        ),
        "code_analysis": (
            "You are an expert code analyst. Highlight anti-patterns, quality "
            "issues, and security concerns while teaching best practices."
        ),
        "issue_analysis": (
            "You are a technical product manager evaluating issue quality. "
            "Assess clarity, requirements, and delivery risks."
        ),
        "general": (
            "You are a helpful assistant providing clear, actionable, and "
            "pragmatic insights."
        ),
    }

    def __init__(
        self,
        timeout_seconds: int = 60,
        executable_path: str = "~/.claude/local/claude",
    ) -> None:
        self.timeout_seconds = max(timeout_seconds, 1)
        self._default_executable = Path(executable_path).expanduser()
        self.claude_cli_path = str(self._resolve_executable_path())
        self._tool_call_count = 0
        self._mock_mode = os.environ.get("MOCK_CLAUDE_CLI") == "1"

    @property
    def tool_calls(self) -> int:
        """Return the number of CLI invocations for diagnostics/tests."""
        return self._tool_call_count

    def reset_tool_calls(self) -> None:
        """Reset the tool call counter (useful for tests)."""
        self._tool_call_count = 0

    def _resolve_executable_path(self) -> Path:
        """Resolve the CLI path using defaults and environment overrides."""
        override = os.environ.get("CLAUDE_CLI_PATH") or os.environ.get(
            "CLAUDE_CLI_NAME"
        )
        if override:
            return Path(override).expanduser()
        return self._default_executable

    def _find_claude_cli(self) -> str:
        """Compatibility helper used by legacy tests and integrations."""
        self.validate_executable()
        return str(self.claude_cli_path)

    def validate_executable(self) -> bool:
        """Check whether the configured executable is available."""
        if self._mock_mode:
            return True

        path = Path(self.claude_cli_path).expanduser()
        if path.exists() and os.access(path, os.X_OK):
            return True

        resolved = shutil.which(str(self.claude_cli_path))
        if resolved:
            self.claude_cli_path = resolved
            return True

        return False

    def _create_isolated_environment(self) -> Dict[str, str]:
        """Create an isolated environment to prevent recursive MCP execution."""
        env = dict(os.environ)
        for var in (
            "CLAUDE_CODE_MODE",
            "CLAUDE_CLI_SESSION",
            "MCP_SERVER",
            "ANTHROPIC_MCP_SERVERS",
            "CLAUDECODE",
        ):
            env.pop(var, None)

        env["CLAUDE_EXTERNAL_EXECUTION"] = "true"
        env["CLAUDE_TASK_ID"] = (
            f"external-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
        )
        if self._mock_mode:
            env["MOCK_CLAUDE_CLI"] = "1"
        return env

    def _get_system_prompt(self, task_type: str) -> str:
        """Return the system prompt for the requested task."""
        return self.SYSTEM_PROMPTS.get(task_type, self.SYSTEM_PROMPTS["general"])

    def _build_command(
        self,
        prompt: str,
        task_type: str,
        additional_args: Optional[List[str]],
    ) -> List[str]:
        """Construct the CLI command with timeout and formatting options."""
        timeout_value = str(self.timeout_seconds + 5)
        command: List[str] = [
            "timeout",
            timeout_value,
            str(self.claude_cli_path),
            "-p",
            prompt,
            "--output-format",
            "json",
            "--system-prompt",
            self._get_system_prompt(task_type),
        ]
        if additional_args:
            command.extend(additional_args)
        return command

    @staticmethod
    def _parse_response(stdout_text: str) -> Dict[str, Any]:
        """Parse CLI stdout, falling back to raw text."""
        cleaned = stdout_text.strip()
        if not cleaned:
            return {}
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"result": cleaned}

    def _mock_result(
        self, prompt: str, task_type: str, metadata: Dict[str, Any]
    ) -> ClaudeCliResult:
        """Generate a deterministic mock response for tests."""
        preview = prompt.strip().splitlines()[:3]
        summary = " ".join(preview)[:200]
        output = f"[MOCK:{task_type}] {summary}".strip()
        command = f"mock://claude/{task_type}"
        return ClaudeCliResult(
            success=True,
            output=output or "[MOCK] Empty prompt",
            execution_time=0.01,
            command_used=command,
            task_type=task_type,
            cost_usd=0.0,
            duration_ms=10,
            session_id=f"mock-session-{self.tool_calls}",
            num_turns=1,
            sdk_metadata={"mock": True, **metadata},
        )

    def _missing_cli_result(self, task_type: str) -> ClaudeCliResult:
        """Return a structured error when the CLI is unavailable."""
        message = (
            "Claude CLI executable not found. Install Claude Code CLI or set "
            "CLAUDE_CLI_PATH."
        )
        return ClaudeCliResult(
            success=False,
            error=message,
            exit_code=-1,
            command_used="external-claude-cli",
            task_type=task_type,
            sdk_metadata={"fallback": True},
        )

    def _increment_tool_calls(self) -> None:
        self._tool_call_count += 1

    async def _await_process_cleanup(self, process: asyncio.subprocess.Process) -> None:
        """Best-effort await for process cleanup when mocks are used."""
        if hasattr(process, "wait"):
            wait_result = process.wait()
            if inspect.isawaitable(wait_result):
                await wait_result
                return
        communicate_result = process.communicate()
        if inspect.isawaitable(communicate_result):
            await communicate_result

    async def execute_claude_cli(
        self,
        prompt: str,
        task_type: str = "general",
        additional_args: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClaudeCliResult:
        """Execute the Claude CLI asynchronously and capture structured output."""
        self._increment_tool_calls()
        metadata = metadata or {}

        if self._mock_mode:
            return self._mock_result(prompt, task_type, metadata)

        cli_available = self.validate_executable()
        in_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
        if not cli_available and not in_pytest:
            logger.error("Claude CLI executable validation failed")
            return self._missing_cli_result(task_type)

        command = self._build_command(prompt, task_type, additional_args)
        env = self._create_isolated_environment()
        start_time = time.monotonic()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except FileNotFoundError:
            logger.exception("Claude CLI executable could not be started")
            return self._missing_cli_result(task_type)
        except Exception as exc:
            logger.exception("Failed to start Claude CLI: %s", exc)
            return ClaudeCliResult(
                success=False,
                error=f"Failed to start Claude CLI: {exc}",
                exit_code=-1,
                execution_time=time.monotonic() - start_time,
                command_used=" ".join(command),
                task_type=task_type,
                sdk_metadata={**metadata, "startup_error": True},
            )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            process.kill()
            await self._await_process_cleanup(process)
            return ClaudeCliResult(
                success=False,
                error=f"Claude CLI timed out after {self.timeout_seconds} seconds",
                exit_code=-1,
                execution_time=time.monotonic() - start_time,
                command_used=" ".join(command),
                task_type=task_type,
                sdk_metadata={**metadata, "timeout": self.timeout_seconds},
            )

        execution_time = time.monotonic() - start_time
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        parsed = self._parse_response(stdout_text)

        success = process.returncode == 0
        output_text = parsed.get("result") if success else None
        if success and not output_text and stdout_text.strip():
            output_text = stdout_text.strip()

        error_text = stderr_text or parsed.get("error")

        result = ClaudeCliResult(
            success=success,
            output=output_text,
            error=error_text if not success else None,
            exit_code=process.returncode,
            execution_time=execution_time,
            command_used=" ".join(command),
            task_type=task_type,
            cost_usd=parsed.get("cost_usd"),
            duration_ms=parsed.get("duration_ms"),
            session_id=parsed.get("session_id"),
            num_turns=parsed.get("num_turns"),
            sdk_metadata={**metadata, "raw_response": parsed},
        )

        if success and not result.output and parsed:
            result.output = json.dumps(parsed)

        if not success and not result.error:
            result.error = stderr_text or "Claude CLI reported an error"

        return result

    async def analyze_content(
        self,
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
        prefer_claude_cli: bool = True,
    ) -> ClaudeCliResult:
        """Analyze provided content via Claude CLI."""
        _ = prefer_claude_cli
        prompt_parts: List[str] = []
        if additional_context:
            prompt_parts.append(f"Context: {additional_context}")
        prompt_parts.append(f"Content to analyze:\n{content}")
        prompt = "\n\n".join(prompt_parts)
        return await self.execute_claude_cli(prompt, task_type)

    async def analyze_file(
        self,
        file_path: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
    ) -> ClaudeCliResult:
        """Analyze the contents of a file using Claude CLI."""
        path = Path(file_path)
        if not path.exists():
            return ClaudeCliResult(
                success=False,
                error=f"File not found: {file_path}",
                exit_code=1,
                command_used="external-claude-cli",
                task_type=task_type,
            )

        content = await asyncio.to_thread(path.read_text, encoding="utf-8")
        context = additional_context or f"File: {path}"
        return await self.analyze_content(
            content=content,
            task_type=task_type,
            additional_context=context,
        )

    async def run_claude_analysis(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute analysis and return a high-level dictionary response."""
        context = context or {}
        task_type = context.get("task_type", "general")
        additional_args = context.get("additional_args")
        metadata = context.get("metadata", {})

        result = await self.execute_claude_cli(
            prompt=prompt,
            task_type=task_type,
            additional_args=additional_args,
            metadata=metadata,
        )

        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "metadata": {
                "task_type": task_type,
                "tool_calls": self.tool_calls,
                "command_used": result.command_used,
                "cost_usd": result.cost_usd,
                "duration_ms": result.duration_ms,
                "session_id": result.session_id,
                "raw": result.sdk_metadata,
            },
        }


# GitHub helper functions
def _get_github_token() -> Optional[str]:
    """Get GitHub token from environment or gh CLI."""
    # Try environment variable first
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get(
        "GITHUB_TOKEN"
    )
    if token:
        return token

    # Fallback to gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not get GitHub token from gh CLI: {e}")

    return None


def _post_github_comment(issue_number: int, repository: str, comment_body: str) -> bool:
    """Post comment to GitHub issue using proper authentication."""
    if not GITHUB_AVAILABLE:
        logger.error("GitHub library not available for posting comments")
        return False

    token = _get_github_token()
    if not token:
        logger.error("No GitHub token available for posting comments")
        return False

    try:
        github_client = Github(token)
        repo = github_client.get_repo(repository)
        issue = repo.get_issue(issue_number)
        issue.create_comment(comment_body)
        logger.info(f"Successfully posted comment to {repository}#{issue_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to post GitHub comment: {e}")
        return False


# Pydantic models for MCP tools
class ExternalClaudeRequest(BaseModel):
    """Request model for external Claude CLI integration."""

    content: str
    task_type: str = "general"
    additional_context: Optional[str] = None
    timeout_seconds: int = 60


class ExternalClaudeResponse(BaseModel):
    """Response model for external Claude CLI integration."""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_seconds: float
    task_type: str
    timestamp: float
    command_used: str = ""


class PullRequestAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    pr_diff: str
    pr_description: str = ""
    file_changes: Optional[List[str]] = None
    timeout_seconds: int = 90


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""

    code_content: str
    file_path: Optional[str] = None
    language: Optional[str] = None
    timeout_seconds: int = 60


def register_llm_analysis_tools(mcp: FastMCP) -> None:
    """Register LLM-powered analysis tools with the MCP server."""

    @mcp.tool()
    async def analyze_text_llm(
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> ExternalClaudeResponse:
        """
        🧠 Deep text analysis using Claude CLI reasoning.

        This tool executes Claude CLI in a separate process to provide comprehensive
        LLM-powered analysis with full reasoning capabilities. For fast pattern
        detection without LLM calls, use analyze_text_nollm instead.

        Args:
            content: Text content to analyze
            task_type: Type of analysis (general, pr_review, code_analysis, issue_analysis)
            additional_context: Optional additional context for the analysis
            timeout_seconds: Maximum time to wait for response

        Returns:
            Comprehensive Claude CLI analysis results
        """
        logger.info(f"Starting external Claude analysis for task type: {task_type}")

        try:
            # Prepare the full content
            if additional_context:
                full_content = f"{additional_context}\n\n{content}"
            else:
                full_content = content

            # Create temporary file for large content
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as temp_file:
                temp_file.write(full_content)
                temp_file_path = temp_file.name

            try:
                # Use direct Claude CLI approach (like Claude Code's ! bash mode)
                # This bypasses recursion detection by using the same execution context

                # Build task-specific system prompt
                system_prompts = {
                    "code_analysis": "You are an expert code analyst. Review this code for potential issues, anti-patterns, security vulnerabilities, and provide improvement suggestions:",
                    "pr_review": "You are a senior software engineer conducting a code review. Analyze this pull request for code quality, security, and best practices:",
                    "issue_analysis": "You are a technical product manager. Analyze this GitHub issue for quality, clarity, and implementation considerations:",
                    "general": "Please analyze the following:",
                }

                prompt = f"{system_prompts.get(task_type, system_prompts['general'])}\n\n{full_content}"

                command = ["claude", "-p", "--dangerously-skip-permissions", prompt]

                logger.debug(
                    f"Executing Claude CLI directly: claude -p --dangerously-skip-permissions <prompt>"
                )

                # Execute Claude CLI directly (like ! bash mode)
                start_time = time.time()
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL,  # Fix: Isolate stdin like Node.js spawn
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                    + 10,  # Allow extra time for process overhead
                )

                execution_time = time.time() - start_time

                if process.returncode == 0:
                    # Claude CLI succeeded - return the direct output
                    output_text = stdout.decode("utf-8").strip()
                    logger.info(
                        f"Claude CLI completed successfully in {execution_time:.2f}s"
                    )

                    return ExternalClaudeResponse(
                        success=True,
                        output=output_text,
                        error=None,
                        exit_code=0,
                        execution_time_seconds=execution_time,
                        task_type=task_type,
                        timestamp=time.time(),
                        command_used="claude -p --dangerously-skip-permissions",
                    )
                else:
                    # Handle error
                    error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                    logger.error(f"Claude CLI failed: {error_msg}")

                    return ExternalClaudeResponse(
                        success=False,
                        error=f"Claude CLI error: {error_msg}",
                        exit_code=process.returncode,
                        execution_time_seconds=execution_time,
                        task_type=task_type,
                        timestamp=time.time(),
                        command_used="claude -p --dangerously-skip-permissions",
                    )

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

        except asyncio.TimeoutError:
            logger.warning(
                f"External Claude analysis timed out after {timeout_seconds + 10}s"
            )
            return ExternalClaudeResponse(
                success=False,
                error=f"Analysis timed out after {timeout_seconds + 10} seconds",
                exit_code=-1,
                execution_time_seconds=timeout_seconds + 10,
                task_type=task_type,
                timestamp=time.time(),
                command_used="claude -p --dangerously-skip-permissions (timeout)",
            )

        except Exception as e:
            logger.error(f"Error in external Claude analysis: {e}")
            return ExternalClaudeResponse(
                success=False,
                error=f"Integration error: {str(e)}",
                exit_code=-1,
                execution_time_seconds=0.0,
                task_type=task_type,
                timestamp=time.time(),
                command_used="claude -p --dangerously-skip-permissions (error)",
            )

    @mcp.tool()
    async def analyze_pr_llm(
        pr_diff: str,
        pr_description: str = "",
        file_changes: Optional[List[str]] = None,
        timeout_seconds: int = 90,
    ) -> ExternalClaudeResponse:
        """
        🧠 Comprehensive PR review using Claude CLI reasoning.

        This tool provides deep PR analysis with LLM-powered reasoning including
        anti-pattern detection, security analysis, and code quality assessment.
        For fast direct PR analysis, use analyze_pr_nollm instead.

        Args:
            pr_diff: The full diff content of the pull request
            pr_description: Description/title of the pull request
            file_changes: List of changed files for context
            timeout_seconds: Maximum time to wait for analysis

        Returns:
            Comprehensive Claude CLI PR review results
        """
        logger.info("Starting external PR review")

        # Build context
        context_parts = []
        if pr_description:
            context_parts.append(f"PR Description: {pr_description}")
        if file_changes:
            context_parts.append(f"Changed files: {', '.join(file_changes)}")

        additional_context = "\n".join(context_parts) if context_parts else None

        return await analyze_text_llm(
            content=pr_diff,
            task_type="pr_review",
            additional_context=additional_context,
            timeout_seconds=timeout_seconds,
        )

    @mcp.tool()
    async def analyze_code_llm(
        code_content: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> ExternalClaudeResponse:
        """
        🧠 Deep code analysis using Claude CLI reasoning.

        This tool provides comprehensive code analysis with LLM-powered reasoning
        for anti-pattern detection, security vulnerabilities, and maintainability.

        Args:
            code_content: The code to analyze
            file_path: Optional file path for context
            language: Programming language for specialized analysis
            timeout_seconds: Maximum time to wait for analysis

        Returns:
            Detailed Claude CLI code analysis results
        """
        logger.info(f"Starting external code analysis for {language or 'unknown'} code")

        # Build context
        context_parts = []
        if file_path:
            context_parts.append(f"File: {file_path}")
        if language:
            context_parts.append(f"Language: {language}")

        additional_context = "\n".join(context_parts) if context_parts else None

        return await analyze_text_llm(
            content=code_content,
            task_type="code_analysis",
            additional_context=additional_context,
            timeout_seconds=timeout_seconds,
        )

    @mcp.tool()
    async def analyze_issue_llm(
        issue_content: str,
        issue_title: str = "",
        issue_labels: Optional[List[str]] = None,
        timeout_seconds: int = 60,
    ) -> ExternalClaudeResponse:
        """
        🧠 Deep GitHub issue analysis using Claude CLI reasoning.

        This tool provides comprehensive issue analysis with LLM-powered reasoning
        for anti-pattern prevention, requirements quality, and implementation guidance.
        For fast direct issue analysis, use analyze_issue_nollm instead.

        Args:
            issue_content: The issue body/content
            issue_title: Title of the issue
            issue_labels: List of issue labels for context
            timeout_seconds: Maximum time to wait for analysis

        Returns:
            Comprehensive Claude CLI issue analysis with anti-pattern prevention guidance
        """
        logger.info("Starting external issue analysis")

        # Build context
        context_parts = []
        if issue_title:
            context_parts.append(f"Issue Title: {issue_title}")
        if issue_labels:
            context_parts.append(f"Labels: {', '.join(issue_labels)}")

        additional_context = "\n".join(context_parts) if context_parts else None

        return await analyze_text_llm(
            content=issue_content,
            task_type="issue_analysis",
            additional_context=additional_context,
            timeout_seconds=timeout_seconds,
        )

    @mcp.tool()
    async def analyze_github_issue_llm(
        issue_number: int,
        repository: str = "kesslerio/vibe-check-mcp",
        post_comment: bool = False,
        analysis_mode: str = "quick",
        timeout_seconds: int = 90,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive vibe check on GitHub issue using external Claude CLI.

        This tool fetches the GitHub issue, analyzes it for anti-patterns and engineering
        guidance, and optionally posts a friendly coaching comment.

        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo"
            post_comment: Whether to post analysis as GitHub comment
            analysis_mode: "quick" or "comprehensive" analysis
            timeout_seconds: Maximum time to wait for analysis

        Returns:
            Comprehensive vibe check analysis with GitHub integration
        """
        logger.info(
            f"Starting external GitHub issue vibe check for {repository}#{issue_number}"
        )

        # Get GitHub token for fetching issue
        token = _get_github_token()
        if not token or not GITHUB_AVAILABLE:
            return {
                "status": "error",
                "error": "GitHub authentication not available",
                "solution": "Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable or run 'gh auth login'",
            }

        try:
            # Fetch issue data
            github_client = Github(token)
            repo = github_client.get_repo(repository)
            issue = repo.get_issue(issue_number)

            # Build comprehensive issue context
            issue_context = f"""# GitHub Issue Analysis
            
**Issue:** {issue.title}
**Repository:** {repository}
**Author:** {issue.user.login}
**State:** {issue.state}
**Labels:** {', '.join([label.name for label in issue.labels]) if issue.labels else 'None'}

**Issue Content:**
{issue.body or 'No content provided'}
"""

            # Create vibe check prompt
            vibe_prompt = f"""You are a friendly engineering coach providing a "vibe check" on this GitHub issue. Focus on preventing common engineering anti-patterns while encouraging good practices.

{issue_context}

Please provide a comprehensive vibe check analysis in this format:

## 🎯 Vibe Check Summary
[One-sentence friendly assessment]

## 🔍 Engineering Guidance
- Research Phase: [Have we done our homework on existing solutions?]
- POC Needs: [Do we need to prove basic functionality first?]
- Complexity Check: [Is the proposed complexity justified?]

## 💡 Friendly Recommendations
[3-5 practical, encouraging recommendations]

## 🎓 Learning Opportunities  
[2-3 educational suggestions based on patterns detected]

Use friendly, coaching language that helps developers learn rather than intimidate."""

            # Run external Claude analysis
            result = await external_claude_analyze(
                content=vibe_prompt,
                task_type="issue_analysis",
                additional_context=f"Vibe check for GitHub issue {repository}#{issue_number}",
                timeout_seconds=timeout_seconds,
            )

            # Build response
            response = {
                "status": "vibe_check_complete",
                "issue_number": issue_number,
                "repository": repository,
                "analysis_mode": analysis_mode,
                "claude_analysis": result.output if result.success else None,
                "analysis_error": result.error if not result.success else None,
                "comment_posted": False,
            }

            # Post comment if requested and analysis succeeded
            if post_comment and result.success and result.output:
                comment_body = f"""## 🎯 Comprehensive Vibe Check

{result.output}

---
*🤖 This vibe check was lovingly crafted by [Vibe Check MCP](https://github.com/kesslerio/vibe-check-mcp) using the Claude Code SDK. Because your code deserves better than just "looks good to me" 🚀*"""

                comment_posted = _post_github_comment(
                    issue_number, repository, comment_body
                )
                response["comment_posted"] = comment_posted

                if not comment_posted:
                    response["comment_error"] = (
                        "Failed to post comment - check GitHub authentication"
                    )

            return response

        except Exception as e:
            logger.error(f"Error in GitHub issue vibe check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issue_number": issue_number,
                "repository": repository,
            }

    @mcp.tool()
    async def analyze_llm_status() -> Dict[str, Any]:
        """
        Check the status of external Claude CLI integration.

        Returns:
            Status information about external Claude CLI availability and configuration
        """
        logger.info("Checking external Claude CLI status")

        try:
            # Check if Claude CLI is available
            try:
                process = await asyncio.create_subprocess_exec(
                    "claude",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL,  # Fix: Isolate stdin like Node.js spawn
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=10
                )
                claude_available = process.returncode == 0
                claude_version = stdout.decode("utf-8").strip() if stdout else "unknown"
            except Exception:
                claude_available = False
                claude_version = "not available"

            # Check Python availability
            try:
                process = await asyncio.create_subprocess_exec(
                    "python3",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL,  # Fix: Isolate stdin like Node.js spawn
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=5
                )
                python_available = process.returncode == 0
                python_version = stdout.decode("utf-8").strip() if stdout else "unknown"
            except Exception:
                python_available = False
                python_version = "not available"

            return {
                "claude_cli_available": claude_available,
                "claude_cli_version": claude_version,
                "python_available": python_available,
                "python_version": python_version,
                "integration_ready": claude_available and python_available,
                "supported_task_types": [
                    "general",
                    "pr_review",
                    "code_analysis",
                    "issue_analysis",
                ],
            }

        except Exception as e:
            logger.error(f"Error checking external Claude status: {e}")
            return {
                "error": f"Status check failed: {str(e)}",
                "integration_ready": False,
            }

    @mcp.tool()
    async def test_claude_cli_with_env(
        test_prompt: str = "What is 2+2?", timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Test Claude CLI without environment isolation (inherits all env vars).
        """
        logger.info(f"Testing Claude CLI with full environment inheritance...")

        start_time = time.time()

        try:
            command = ["claude", "-p", "--dangerously-skip-permissions", test_prompt]

            logger.info(
                f"CLAUDE_CODE_SSE_PORT present: {'CLAUDE_CODE_SSE_PORT' in os.environ}"
            )

            # Use inherited environment (no isolation)
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,  # Fix: Isolate stdin like Node.js spawn
                # No env parameter = inherit all environment variables
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout_seconds
            )

            execution_time = time.time() - start_time

            if process.returncode == 0:
                output = stdout.decode("utf-8").strip()
                logger.info(
                    f"✅ Claude CLI with env inheritance succeeded in {execution_time:.2f}s"
                )

                return {
                    "success": True,
                    "exit_code": 0,
                    "output": output,
                    "output_length": len(output),
                    "execution_time_seconds": execution_time,
                    "environment_isolation": False,
                    "claude_sse_port_present": os.environ.get("CLAUDE_CODE_SSE_PORT")
                    is not None,
                    "timestamp": time.time(),
                }
            else:
                error = stderr.decode("utf-8").strip()
                logger.error(f"❌ Claude CLI with env inheritance failed: {error}")

                return {
                    "success": False,
                    "exit_code": process.returncode,
                    "error": error,
                    "execution_time_seconds": execution_time,
                    "environment_isolation": False,
                    "claude_sse_port_present": os.environ.get("CLAUDE_CODE_SSE_PORT")
                    is not None,
                    "timestamp": time.time(),
                }

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Process timed out after {timeout_seconds} seconds",
                "execution_time_seconds": execution_time,
                "environment_isolation": False,
                "timestamp": time.time(),
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "execution_time_seconds": execution_time,
                "environment_isolation": False,
                "timestamp": time.time(),
            }


def register_external_claude_tools(mcp: FastMCP) -> None:
    """Register lightweight external Claude CLI MCP tools."""

    cli = ExternalClaudeCli()

    def _set_timeout(timeout: int) -> None:
        cli.timeout_seconds = max(timeout, 1)

    def _to_response(result: ClaudeCliResult, task_type: str) -> ExternalClaudeResponse:
        return ExternalClaudeResponse(
            success=result.success,
            output=result.output,
            error=result.error,
            exit_code=result.exit_code,
            execution_time_seconds=result.execution_time,
            task_type=task_type,
            timestamp=time.time(),
            command_used=result.command_used,
        )

    @mcp.tool()
    async def external_claude_analyze(
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> ExternalClaudeResponse:
        _set_timeout(timeout_seconds)
        result = await cli.analyze_content(
            content=content,
            task_type=task_type,
            additional_context=additional_context,
        )
        return _to_response(result, task_type)

    @mcp.tool()
    async def external_pr_review(
        prompt: str,
        additional_context: Optional[str] = None,
        timeout_seconds: int = 90,
    ) -> ExternalClaudeResponse:
        _set_timeout(timeout_seconds)
        result = await cli.analyze_content(
            content=prompt,
            task_type="pr_review",
            additional_context=additional_context,
        )
        return _to_response(result, "pr_review")

    @mcp.tool()
    async def external_code_analysis(
        code_content: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> ExternalClaudeResponse:
        _set_timeout(timeout_seconds)
        context_parts: List[str] = []
        if file_path:
            context_parts.append(f"File: {file_path}")
        if language:
            context_parts.append(f"Language: {language}")
        context = " | ".join(context_parts) if context_parts else None
        result = await cli.analyze_content(
            content=code_content,
            task_type="code_analysis",
            additional_context=context,
        )
        return _to_response(result, "code_analysis")

    @mcp.tool()
    async def external_issue_analysis(
        issue_content: str,
        issue_title: Optional[str] = None,
        issue_labels: Optional[List[str]] = None,
        timeout_seconds: int = 60,
    ) -> ExternalClaudeResponse:
        _set_timeout(timeout_seconds)
        context_parts: List[str] = []
        if issue_title:
            context_parts.append(f"Title: {issue_title}")
        if issue_labels:
            context_parts.append(f"Labels: {', '.join(issue_labels)}")
        context = " | ".join(context_parts) if context_parts else None
        result = await cli.analyze_content(
            content=issue_content,
            task_type="issue_analysis",
            additional_context=context,
        )
        return _to_response(result, "issue_analysis")

    @mcp.tool()
    async def external_claude_status() -> Dict[str, Any]:
        available = cli.validate_executable()
        version_info: Dict[str, Any] = {}
        if available:
            try:
                process = await asyncio.create_subprocess_exec(
                    str(cli.claude_cli_path),
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=5
                )
                version_info = {
                    "stdout": stdout.decode().strip(),
                    "stderr": stderr.decode().strip(),
                    "exit_code": process.returncode,
                }
            except Exception as exc:  # pragma: no cover - diagnostics only
                version_info = {"error": str(exc)}
        return {
            "available": available,
            "cli_path": str(cli.claude_cli_path),
            "tool_calls": cli.tool_calls,
            "version": version_info,
        }


async def main():
    """Main entry point for external Claude CLI execution."""
    parser = argparse.ArgumentParser(
        description="External Claude CLI executor for MCP tools"
    )
    parser.add_argument("--prompt", "-p", help="Direct prompt to send to Claude CLI")
    parser.add_argument("--input-file", "-f", help="File to analyze with Claude CLI")
    parser.add_argument(
        "--task-type",
        "-t",
        choices=["pr_review", "code_analysis", "issue_analysis", "general"],
        default="general",
        help="Type of analysis task",
    )
    parser.add_argument(
        "--timeout", "-T", type=int, default=60, help="Timeout in seconds (default: 60)"
    )
    parser.add_argument("--output", "-o", help="Output file for results (JSON format)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("--mcp-config", help="Path to MCP configuration file")
    parser.add_argument(
        "--permission-prompt-tool", help="Name of the permission tool for auto-approval"
    )
    parser.add_argument(
        "--allowedTools", help="Comma-separated list of allowed tools (or '*' for all)"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if not args.prompt and not args.input_file:
        parser.error("Either --prompt or --input-file must be specified")

    # Initialize executor
    executor = ExternalClaudeCli(timeout_seconds=args.timeout)

    # Execute based on input type
    if args.input_file:
        # Read file and analyze
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                content = f.read()
            result = await executor.analyze_content(
                content=content,
                task_type=args.task_type,
                additional_context=f"File: {args.input_file}",
                prefer_claude_cli=True,  # Prefer Claude CLI direct execution
            )
        except Exception as e:
            result = ClaudeCliResult(
                success=False,
                error=f"Error reading file {args.input_file}: {str(e)}",
                exit_code=1,
                task_type=args.task_type,
            )
    else:
        result = await executor.analyze_content(
            content=args.prompt,
            task_type=args.task_type,
            prefer_claude_cli=True,  # Prefer Claude CLI direct execution
        )

    # Output results
    result_dict = result.to_dict()

    if args.output:
        # Write to file
        with open(args.output, "w") as f:
            json.dump(result_dict, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result_dict, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    asyncio.run(main())
