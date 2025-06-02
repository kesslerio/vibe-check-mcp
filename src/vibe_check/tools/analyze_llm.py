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
    - analyze_text_llm: General content analysis with Claude CLI reasoning
    - analyze_pr_llm: Pull request review with Claude CLI reasoning
    - analyze_code_llm: Code analysis with Claude CLI reasoning
    - analyze_issue_llm: Issue analysis with Claude CLI reasoning
    - analyze_github_issue_llm: GitHub issue vibe check with Claude CLI reasoning
    - analyze_llm_status: Status check for Claude CLI integration
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from pydantic import BaseModel

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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeCliResult:
    """Container for Claude CLI execution results with SDK metadata."""
    
    def __init__(
        self,
        success: bool,
        output: Optional[str] = None,
        error: Optional[str] = None,
        exit_code: Optional[int] = None,
        execution_time: float = 0.0,
        command_used: str = "",
        task_type: str = "general",
        cost_usd: Optional[float] = None,
        duration_ms: Optional[float] = None,
        session_id: Optional[str] = None,
        num_turns: Optional[int] = None,
        sdk_metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.command_used = command_used
        self.task_type = task_type
        self.cost_usd = cost_usd
        self.duration_ms = duration_ms
        self.session_id = session_id
        self.num_turns = num_turns
        self.sdk_metadata = sdk_metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
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
            "timestamp": time.time()
        }


class ExternalClaudeCli:
    """External Claude CLI executor with isolation and specialized prompts."""
    
    # System prompts for specialized task types (used with --system-prompt)
    SYSTEM_PROMPTS = {
        "pr_review": """You are a senior software engineer conducting thorough code reviews. Analyze pull requests with focus on:

1. **Code Quality**: Structure, organization, naming conventions, error handling
2. **Security & Performance**: Vulnerabilities, performance implications, resource usage
3. **Anti-Pattern Detection**: Infrastructure-without-implementation, symptom-driven development, complexity escalation
4. **Actionable Recommendations**: Specific improvements, best practices, testing requirements

Provide constructive, educational feedback that improves code quality and prevents anti-patterns.""",

        "code_analysis": """You are an expert code analyst specializing in anti-pattern detection and code quality assessment. Focus on:

1. **Anti-Pattern Detection**: Infrastructure without implementation, symptom-driven development, complexity escalation, documentation neglect
2. **Quality Issues**: Structure problems, maintainability concerns, performance bottlenecks  
3. **Security Analysis**: Common vulnerabilities, input validation, authentication issues
4. **Educational Guidance**: Refactoring suggestions, best practices, prevention strategies

Provide detailed analysis that helps developers learn and prevent future anti-patterns.""",

        "issue_analysis": """You are a technical product manager analyzing GitHub issues for quality and anti-pattern prevention. Evaluate issues for:

1. **Anti-Pattern Risk**: Infrastructure-without-implementation indicators, symptom vs root cause, complexity escalation potential
2. **Requirements Quality**: Problem definition clarity, measurable criteria, appropriate scope
3. **Implementation Strategy**: Approach validation, technical debt implications, resource considerations
4. **Educational Value**: Pattern prevention, alternative approaches, learning opportunities

Promote good engineering practices through constructive analysis.""",

        "general": """You are a helpful assistant providing clear, accurate, and actionable insights. Focus on clarity and practical recommendations."""
    }
    
    def __init__(self, timeout_seconds: int = 60):
        """
        Initialize external Claude CLI executor.
        
        Args:
            timeout_seconds: Maximum time to wait for Claude CLI response
        """
        self.timeout_seconds = timeout_seconds
        self.claude_cli_path = self._find_claude_cli()
        
        # NO Anthropic API client - Claude subscription only via Claude Code
        # This ensures we never use API tokens, only Claude subscription
        self.anthropic_client = None
        logger.info("Anthropic API disabled - using Claude subscription via Claude Code only")
    
    def _find_claude_cli(self) -> str:
        """Find the Claude CLI executable path using claude-code-mcp approach."""
        logger.debug('[Debug] Attempting to find Claude CLI...')
        
        # Check for custom CLI name from environment variable (claude-code-mcp pattern)
        custom_cli_name = os.environ.get('CLAUDE_CLI_NAME')
        if custom_cli_name:
            logger.debug(f'[Debug] Using custom Claude CLI name from CLAUDE_CLI_NAME: {custom_cli_name}')
            
            # If it's an absolute path, use it directly
            if os.path.isabs(custom_cli_name):
                logger.debug(f'[Debug] CLAUDE_CLI_NAME is an absolute path: {custom_cli_name}')
                return custom_cli_name
            
            # If it contains path separators (relative path), reject it
            if '/' in custom_cli_name or '\\' in custom_cli_name:
                raise ValueError(
                    f"Invalid CLAUDE_CLI_NAME: Relative paths are not allowed. "
                    f"Use either a simple name (e.g., 'claude') or an absolute path"
                )
        
        cli_name = custom_cli_name or 'claude'
        
        # Try local install path: ~/.claude/local/claude (claude-code-mcp pattern)
        user_path = os.path.expanduser('~/.claude/local/claude')
        logger.debug(f'[Debug] Checking for Claude CLI at local user path: {user_path}')
        
        if os.path.exists(user_path):
            logger.debug(f'[Debug] Found Claude CLI at local user path: {user_path}')
            return user_path
        else:
            logger.debug(f'[Debug] Claude CLI not found at local user path: {user_path}')
        
        # Fallback to CLI name (PATH lookup)
        logger.debug(f'[Debug] Falling back to "{cli_name}" command name, relying on PATH lookup')
        logger.warning(f'[Warning] Claude CLI not found at ~/.claude/local/claude. Falling back to "{cli_name}" in PATH')
        return cli_name
    
    def _get_system_prompt(self, task_type: str) -> str:
        """
        Get specialized system prompt for task type.
        
        Args:
            task_type: Type of analysis task
            
        Returns:
            System prompt for the specific task
        """
        return self.SYSTEM_PROMPTS.get(task_type, self.SYSTEM_PROMPTS["general"])
    
    def _get_claude_args(self, prompt: str, task_type: str) -> List[str]:
        """
        Build Claude CLI arguments using claude-code-mcp approach.
        
        Args:
            prompt: The prompt to send to Claude
            task_type: Type of task for specialized handling
            
        Returns:
            List of command line arguments
        """
        # Use the same pattern as claude-code-mcp: --dangerously-skip-permissions -p prompt
        args = ['--dangerously-skip-permissions', '-p', prompt]
        
        # Add system prompt if we have specialized task types
        system_prompt = self._get_system_prompt(task_type)
        if task_type != "general" and system_prompt != self.SYSTEM_PROMPTS["general"]:
            # Add system prompt as additional context in the prompt itself
            enhanced_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            args = ['--dangerously-skip-permissions', '-p', enhanced_prompt]
        
        logger.debug(f'[Debug] Claude CLI args: {args}')
        return args
    
    def execute_claude_cli_direct(
        self,
        prompt: str,
        task_type: str = "general"
    ) -> ClaudeCliResult:
        """
        Execute Claude CLI directly using claude-code-mcp approach (preferred method).
        
        Args:
            prompt: The prompt to send to Claude CLI
            task_type: Type of task for specialized handling
            
        Returns:
            ClaudeCliResult with execution details
        """
        start_time = time.time()
        logger.info(f"Executing Claude CLI directly for task: {task_type}")
        
        try:
            # Build command using claude-code-mcp pattern
            claude_args = self._get_claude_args(prompt, task_type)
            
            logger.debug(f'[Debug] Invoking Claude CLI: {self.claude_cli_path} {" ".join(claude_args)}')
            
            # Create clean environment to avoid MCP recursion detection
            clean_env = dict(os.environ)
            # Remove MCP and Claude Code specific environment variables
            for var in ["MCP_SERVER", "CLAUDE_CODE_MODE", "CLAUDE_CLI_SESSION", "CLAUDECODE", 
                       "MCP_CLAUDE_DEBUG", "ANTHROPIC_MCP_SERVERS"]:
                clean_env.pop(var, None)
            
            # Use regular subprocess (like claude-code-mcp) instead of asyncio
            command = [self.claude_cli_path] + claude_args
            logger.debug(f'[Debug] Running command: {" ".join(command)}')
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=os.getcwd(),
                env=clean_env,
                stdin=subprocess.DEVNULL  # Fix: Isolate stdin to prevent Claude CLI hanging
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                output = result.stdout
                logger.info(f"Claude CLI completed successfully in {execution_time:.2f}s")
                logger.debug(f'[Debug] Claude CLI stdout: {output.strip()}')
                
                if result.stderr:
                    logger.debug(f'[Debug] Claude CLI stderr: {result.stderr.strip()}')
                
                return ClaudeCliResult(
                    success=True,
                    output=output,
                    error=None,
                    exit_code=0,
                    execution_time=execution_time,
                    command_used="claude_cli_direct",
                    task_type=task_type,
                    sdk_metadata={
                        "isolation_method": "claude_cli_direct",
                        "args_used": claude_args
                    }
                )
            else:
                # Handle error response
                error_msg = result.stderr.strip() if result.stderr else "Claude CLI failed"
                output = result.stdout.strip() if result.stdout else ""
                
                logger.error(f"Claude CLI failed. Exit code: {result.returncode}. Stderr: {error_msg}")
                
                return ClaudeCliResult(
                    success=False,
                    output=output,
                    error=error_msg,
                    exit_code=result.returncode,
                    execution_time=execution_time,
                    command_used="claude_cli_direct",
                    task_type=task_type
                )
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.warning(f"Claude CLI timed out after {self.timeout_seconds}s (subprocess timeout)")
            
            return ClaudeCliResult(
                success=False,
                error=f"Claude CLI timeout after {self.timeout_seconds} seconds",
                exit_code=124,
                execution_time=execution_time,
                command_used="claude_cli_direct",
                task_type=task_type
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing Claude CLI: {e}")
            
            return ClaudeCliResult(
                success=False,
                error=f"Claude CLI execution error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                command_used="claude_cli_direct",
                task_type=task_type
            )
    
    async def analyze_content(
        self,
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
        prefer_claude_cli: bool = True
    ) -> ClaudeCliResult:
        """
        Analyze content using Claude CLI direct (preferred) or Anthropic SDK (fallback).
        
        Args:
            content: Content to analyze
            task_type: Type of analysis (pr_review, code_analysis, etc.)
            additional_context: Optional additional context
            prefer_claude_cli: Whether to prefer Claude CLI direct execution (default: True)
            
        Returns:
            ClaudeCliResult with analysis
        """
        # Build prompt with context and content
        prompt_parts = []
        
        if additional_context:
            prompt_parts.append(f"Context: {additional_context}")
        
        prompt_parts.append(f"Content to analyze:\n{content}")
        
        prompt = "\n\n".join(prompt_parts)
        
        # ONLY use Claude CLI direct execution - NO API fallback
        # This ensures we use Claude subscription via Claude Code, not API tokens
        logger.info("Using Claude CLI direct execution (subscription-based, no API)")
        result = self.execute_claude_cli_direct(
            prompt=prompt,
            task_type=task_type
        )
        
        # Return result (success or failure) - no API fallback
        if not result.success:
            logger.error(f"Claude CLI execution failed: {result.error}")
            logger.error("NO API FALLBACK - Fix Claude Code integration or check subscription")
        
        return result


# GitHub helper functions
def _get_github_token() -> Optional[str]:
    """Get GitHub token from environment or gh CLI."""
    # Try environment variable first
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    # Fallback to gh CLI
    try:
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=10)
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
        timeout_seconds: int = 60
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
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
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
                    "general": "Please analyze the following:"
                }
                
                prompt = f"{system_prompts.get(task_type, system_prompts['general'])}\n\n{full_content}"
                
                command = [
                    "claude", "-p", "--dangerously-skip-permissions",
                    prompt
                ]
                
                logger.debug(f"Executing Claude CLI directly: claude -p --dangerously-skip-permissions <prompt>")
                
                # Execute Claude CLI directly (like ! bash mode)
                start_time = time.time()
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL  # Fix: Isolate stdin like Node.js spawn
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds + 10  # Allow extra time for process overhead
                )
                
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    # Claude CLI succeeded - return the direct output
                    output_text = stdout.decode('utf-8').strip()
                    logger.info(f"Claude CLI completed successfully in {execution_time:.2f}s")
                    
                    return ExternalClaudeResponse(
                        success=True,
                        output=output_text,
                        error=None,
                        exit_code=0,
                        execution_time_seconds=execution_time,
                        task_type=task_type,
                        timestamp=time.time(),
                        command_used="claude -p --dangerously-skip-permissions"
                    )
                else:
                    # Handle error
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                    logger.error(f"Claude CLI failed: {error_msg}")
                    
                    return ExternalClaudeResponse(
                        success=False,
                        error=f"Claude CLI error: {error_msg}",
                        exit_code=process.returncode,
                        execution_time_seconds=execution_time,
                        task_type=task_type,
                        timestamp=time.time(),
                        command_used="claude -p --dangerously-skip-permissions"
                    )
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                    
        except asyncio.TimeoutError:
            logger.warning(f"External Claude analysis timed out after {timeout_seconds + 10}s")
            return ExternalClaudeResponse(
                success=False,
                error=f"Analysis timed out after {timeout_seconds + 10} seconds",
                exit_code=-1,
                execution_time_seconds=timeout_seconds + 10,
                task_type=task_type,
                timestamp=time.time(),
                command_used="claude -p --dangerously-skip-permissions (timeout)"
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
                command_used="claude -p --dangerously-skip-permissions (error)"
            )
    
    @mcp.tool()
    async def analyze_pr_llm(
        pr_diff: str,
        pr_description: str = "",
        file_changes: Optional[List[str]] = None,
        timeout_seconds: int = 90
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
            timeout_seconds=timeout_seconds
        )
    
    @mcp.tool()
    async def analyze_code_llm(
        code_content: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        timeout_seconds: int = 60
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
            timeout_seconds=timeout_seconds
        )
    
    @mcp.tool()
    async def analyze_issue_llm(
        issue_content: str,
        issue_title: str = "",
        issue_labels: Optional[List[str]] = None,
        timeout_seconds: int = 60
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
            timeout_seconds=timeout_seconds
        )
    
    @mcp.tool()
    async def analyze_github_issue_llm(
        issue_number: int,
        repository: str = "kesslerio/vibe-check-mcp",
        post_comment: bool = True,
        analysis_mode: str = "comprehensive",
        detail_level: str = "standard",
        timeout_seconds: int = 90
    ) -> Dict[str, Any]:
        """
        🧠 Comprehensive GitHub issue vibe check using Claude CLI reasoning.
        
        This tool fetches the GitHub issue, analyzes it for anti-patterns and engineering
        guidance using Claude CLI, and optionally posts a friendly coaching comment.
        For fast direct issue analysis, use analyze_issue_nollm instead.
        
        Args:
            issue_number: GitHub issue number to analyze
            repository: Repository in format "owner/repo" (default: "kesslerio/vibe-check-mcp")
            post_comment: Whether to post analysis as GitHub comment (default: True)
            analysis_mode: "quick" or "comprehensive" analysis (default: "comprehensive")
            detail_level: Educational detail level - brief/standard/comprehensive (default: "standard")
            timeout_seconds: Maximum time to wait for analysis (default: 90)
            
        Returns:
            Comprehensive Claude CLI vibe check analysis with GitHub integration
        """
        logger.info(f"Starting external GitHub issue vibe check for {repository}#{issue_number}")
        
        # Get GitHub token for fetching issue
        token = _get_github_token()
        if not token or not GITHUB_AVAILABLE:
            return {
                "status": "error",
                "error": "GitHub authentication not available",
                "solution": "Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable or run 'gh auth login'"
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
            
            # Create vibe check prompt based on detail level
            detail_instructions = {
                "brief": "Provide a concise 3-section analysis with key points only.",
                "standard": "Provide a balanced analysis with practical guidance and clear recommendations.",
                "comprehensive": "Provide detailed analysis with extensive educational content, examples, and learning opportunities."
            }
            
            detail_instruction = detail_instructions.get(detail_level, detail_instructions["standard"])
            
            vibe_prompt = f"""You are a friendly engineering coach providing a "vibe check" on this GitHub issue. Focus on preventing common engineering anti-patterns while encouraging good practices.

{detail_instruction}

{issue_context}

Please provide a vibe check analysis in this format:

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
            result = await analyze_text_llm(
                content=vibe_prompt,
                task_type="issue_analysis",
                additional_context=f"Vibe check for GitHub issue {repository}#{issue_number}",
                timeout_seconds=timeout_seconds
            )
            
            # Build response
            response = {
                "status": "vibe_check_complete",
                "issue_number": issue_number,
                "repository": repository,
                "analysis_mode": analysis_mode,
                "claude_analysis": result.output if result.success else None,
                "analysis_error": result.error if not result.success else None,
                "comment_posted": False
            }
            
            # Post comment if requested and analysis succeeded
            if post_comment and result.success and result.output:
                comment_body = f"""## 🎯 Comprehensive Vibe Check

{result.output}

---
*This vibe check was generated by the Vibe Check MCP framework using external Claude CLI for enhanced analysis.*"""
                
                comment_posted = _post_github_comment(issue_number, repository, comment_body)
                response["comment_posted"] = comment_posted
                
                if not comment_posted:
                    response["comment_error"] = "Failed to post comment - check GitHub authentication"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in GitHub issue vibe check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issue_number": issue_number,
                "repository": repository
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
                    "claude", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL  # Fix: Isolate stdin like Node.js spawn
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
                claude_available = process.returncode == 0
                claude_version = stdout.decode('utf-8').strip() if stdout else "unknown"
            except Exception:
                claude_available = False
                claude_version = "not available"
            
            # Check Python availability
            try:
                process = await asyncio.create_subprocess_exec(
                    "python3", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.DEVNULL  # Fix: Isolate stdin like Node.js spawn
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
                python_available = process.returncode == 0
                python_version = stdout.decode('utf-8').strip() if stdout else "unknown"
            except Exception:
                python_available = False
                python_version = "not available"
            
            return {
                "claude_cli_available": claude_available,
                "claude_cli_version": claude_version,
                "python_available": python_available,
                "python_version": python_version,
                "integration_ready": claude_available and python_available,
                "supported_task_types": ["general", "pr_review", "code_analysis", "issue_analysis"]
            }
            
        except Exception as e:
            logger.error(f"Error checking external Claude status: {e}")
            return {
                "error": f"Status check failed: {str(e)}",
                "integration_ready": False
            }

    @mcp.tool()
    async def test_claude_cli_with_env(
        test_prompt: str = "What is 2+2?",
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Test Claude CLI without environment isolation (inherits all env vars).
        """
        logger.info(f"Testing Claude CLI with full environment inheritance...")
        
        start_time = time.time()
        
        try:
            command = [
                "claude", "-p", "--dangerously-skip-permissions",
                test_prompt
            ]
            
            logger.info(f"CLAUDE_CODE_SSE_PORT present: {'CLAUDE_CODE_SSE_PORT' in os.environ}")
            
            # Use inherited environment (no isolation)
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL  # Fix: Isolate stdin like Node.js spawn
                # No env parameter = inherit all environment variables
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                output = stdout.decode('utf-8').strip()
                logger.info(f"✅ Claude CLI with env inheritance succeeded in {execution_time:.2f}s")
                
                return {
                    "success": True,
                    "exit_code": 0,
                    "output": output,
                    "output_length": len(output),
                    "execution_time_seconds": execution_time,
                    "environment_isolation": False,
                    "claude_sse_port_present": os.environ.get('CLAUDE_CODE_SSE_PORT') is not None,
                    "timestamp": time.time()
                }
            else:
                error = stderr.decode('utf-8').strip()
                logger.error(f"❌ Claude CLI with env inheritance failed: {error}")
                
                return {
                    "success": False,
                    "exit_code": process.returncode,
                    "error": error,
                    "execution_time_seconds": execution_time,
                    "environment_isolation": False,
                    "claude_sse_port_present": os.environ.get('CLAUDE_CODE_SSE_PORT') is not None,
                    "timestamp": time.time()
                }
                
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Process timed out after {timeout_seconds} seconds",
                "execution_time_seconds": execution_time,
                "environment_isolation": False,
                "timestamp": time.time()
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "execution_time_seconds": execution_time,
                "environment_isolation": False,
                "timestamp": time.time()
            }


async def main():
    """Main entry point for external Claude CLI execution."""
    parser = argparse.ArgumentParser(
        description="External Claude CLI executor for MCP tools"
    )
    parser.add_argument(
        "--prompt", "-p",
        help="Direct prompt to send to Claude CLI"
    )
    parser.add_argument(
        "--input-file", "-f",
        help="File to analyze with Claude CLI"
    )
    parser.add_argument(
        "--task-type", "-t",
        choices=["pr_review", "code_analysis", "issue_analysis", "general"],
        default="general",
        help="Type of analysis task"
    )
    parser.add_argument(
        "--timeout", "-T",
        type=int,
        default=60,
        help="Timeout in seconds (default: 60)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for results (JSON format)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--mcp-config",
        help="Path to MCP configuration file"
    )
    parser.add_argument(
        "--permission-prompt-tool",
        help="Name of the permission tool for auto-approval"
    )
    parser.add_argument(
        "--allowedTools",
        help="Comma-separated list of allowed tools (or '*' for all)"
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
            with open(args.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            result = await executor.analyze_content(
                content=content,
                task_type=args.task_type,
                additional_context=f"File: {args.input_file}",
                prefer_claude_cli=True  # Prefer Claude CLI direct execution
            )
        except Exception as e:
            result = ClaudeCliResult(
                success=False,
                error=f"Error reading file {args.input_file}: {str(e)}",
                exit_code=1,
                task_type=args.task_type
            )
    else:
        result = await executor.analyze_content(
            content=args.prompt,
            task_type=args.task_type,
            prefer_claude_cli=True  # Prefer Claude CLI direct execution
        )
    
    # Output results
    result_dict = result.to_dict()
    
    if args.output:
        # Write to file
        with open(args.output, 'w') as f:
            json.dump(result_dict, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result_dict, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    asyncio.run(main())