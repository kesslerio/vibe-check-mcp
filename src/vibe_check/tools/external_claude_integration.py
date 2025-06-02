"""
MCP tool for external Claude CLI integration.

This module provides MCP tools that leverage the ExternalClaudeCli class
to perform analysis tasks without context blocking issues.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from pydantic import BaseModel

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

from .external_claude_cli import ExternalClaudeCli, ClaudeCliResult

logger = logging.getLogger(__name__)


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


def register_external_claude_tools(mcp: FastMCP) -> None:
    """Register external Claude CLI integration tools with the MCP server."""
    
    # Path to external script
    external_script_path = Path(__file__).parent / "external_claude_cli.py"
    
    @mcp.tool()
    async def external_claude_analyze(
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
        timeout_seconds: int = 60
    ) -> ExternalClaudeResponse:
        """
        Analyze content using external Claude CLI to avoid context blocking.
        
        This tool executes Claude CLI in a separate process to prevent the
        timeout issues that occur when calling Claude CLI from within Claude Code.
        
        Args:
            content: Content to analyze
            task_type: Type of analysis (general, pr_review, code_analysis, issue_analysis)
            additional_context: Optional additional context for the analysis
            timeout_seconds: Maximum time to wait for response
            
        Returns:
            Analysis results from external Claude CLI execution
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
                    "claude", "--dangerously-skip-permissions", "-p",
                    prompt
                ]
                
                logger.debug(f"Executing Claude CLI directly: claude --dangerously-skip-permissions -p <prompt>")
                
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
                        command_used="claude --dangerously-skip-permissions -p"
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
                        command_used="claude --dangerously-skip-permissions -p"
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
                command_used="claude --dangerously-skip-permissions -p (timeout)"
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
                command_used="claude --dangerously-skip-permissions -p (error)"
            )
    
    @mcp.tool()
    async def external_pr_review(
        pr_diff: str,
        pr_description: str = "",
        file_changes: Optional[List[str]] = None,
        timeout_seconds: int = 90
    ) -> ExternalClaudeResponse:
        """
        Perform comprehensive PR review using external Claude CLI.
        
        This tool provides specialized PR review capabilities with anti-pattern
        detection, security analysis, and code quality assessment.
        
        Args:
            pr_diff: The full diff content of the pull request
            pr_description: Description/title of the pull request
            file_changes: List of changed files for context
            timeout_seconds: Maximum time to wait for analysis
            
        Returns:
            Comprehensive PR review results
        """
        logger.info("Starting external PR review")
        
        # Build context
        context_parts = []
        if pr_description:
            context_parts.append(f"PR Description: {pr_description}")
        if file_changes:
            context_parts.append(f"Changed files: {', '.join(file_changes)}")
        
        additional_context = "\n".join(context_parts) if context_parts else None
        
        return await external_claude_analyze(
            content=pr_diff,
            task_type="pr_review",
            additional_context=additional_context,
            timeout_seconds=timeout_seconds
        )
    
    @mcp.tool()
    async def external_code_analysis(
        code_content: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        timeout_seconds: int = 60
    ) -> ExternalClaudeResponse:
        """
        Analyze code for anti-patterns and quality issues using external Claude CLI.
        
        This tool provides specialized code analysis focusing on anti-pattern
        detection, security vulnerabilities, and maintainability concerns.
        
        Args:
            code_content: The code to analyze
            file_path: Optional file path for context
            language: Programming language for specialized analysis
            timeout_seconds: Maximum time to wait for analysis
            
        Returns:
            Detailed code analysis results
        """
        logger.info(f"Starting external code analysis for {language or 'unknown'} code")
        
        # Build context
        context_parts = []
        if file_path:
            context_parts.append(f"File: {file_path}")
        if language:
            context_parts.append(f"Language: {language}")
        
        additional_context = "\n".join(context_parts) if context_parts else None
        
        return await external_claude_analyze(
            content=code_content,
            task_type="code_analysis",
            additional_context=additional_context,
            timeout_seconds=timeout_seconds
        )
    
    @mcp.tool()
    async def external_issue_analysis(
        issue_content: str,
        issue_title: str = "",
        issue_labels: Optional[List[str]] = None,
        timeout_seconds: int = 60
    ) -> ExternalClaudeResponse:
        """
        Analyze GitHub issues for anti-patterns and quality using external Claude CLI.
        
        This tool provides specialized issue analysis focusing on anti-pattern
        prevention, requirements quality, and implementation guidance.
        
        Args:
            issue_content: The issue body/content
            issue_title: Title of the issue
            issue_labels: List of issue labels for context
            timeout_seconds: Maximum time to wait for analysis
            
        Returns:
            Issue analysis with anti-pattern prevention guidance
        """
        logger.info("Starting external issue analysis")
        
        # Build context
        context_parts = []
        if issue_title:
            context_parts.append(f"Issue Title: {issue_title}")
        if issue_labels:
            context_parts.append(f"Labels: {', '.join(issue_labels)}")
        
        additional_context = "\n".join(context_parts) if context_parts else None
        
        return await external_claude_analyze(
            content=issue_content,
            task_type="issue_analysis",
            additional_context=additional_context,
            timeout_seconds=timeout_seconds
        )
    
    @mcp.tool()
    async def external_github_issue_vibe_check(
        issue_number: int,
        repository: str = "kesslerio/vibe-check-mcp",
        post_comment: bool = False,
        analysis_mode: str = "quick",
        timeout_seconds: int = 90
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
    async def external_claude_status() -> Dict[str, Any]:
        """
        Check the status of external Claude CLI integration.
        
        Returns:
            Status information about external Claude CLI availability and configuration
        """
        logger.info("Checking external Claude CLI status")
        
        try:
            # Check if external script exists
            script_exists = external_script_path.exists()
            
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
                "external_script_available": script_exists,
                "external_script_path": str(external_script_path),
                "claude_cli_available": claude_available,
                "claude_cli_version": claude_version,
                "python_available": python_available,
                "python_version": python_version,
                "integration_ready": script_exists and claude_available and python_available,
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
                "claude", "--dangerously-skip-permissions", "-p",
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