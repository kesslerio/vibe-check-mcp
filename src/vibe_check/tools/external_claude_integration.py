"""
MCP tool for external Claude CLI integration.

This module provides MCP tools that leverage the ExternalClaudeCli class
to perform analysis tasks without context blocking issues.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from pydantic import BaseModel

from .external_claude_cli import ExternalClaudeCli, ClaudeCliResult

logger = logging.getLogger(__name__)


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
                # Build command for external script
                command = [
                    "python3",
                    str(external_script_path),
                    "--prompt", full_content,
                    "--task-type", task_type,
                    "--timeout", str(timeout_seconds)
                ]
                
                logger.debug(f"Executing command: {' '.join(command)}")
                
                # Execute external script
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds + 10  # Allow extra time for process overhead
                )
                
                if process.returncode == 0:
                    # Parse JSON result
                    result_data = json.loads(stdout.decode('utf-8'))
                    return ExternalClaudeResponse(**result_data)
                else:
                    # Handle error
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                    logger.error(f"External script failed: {error_msg}")
                    
                    return ExternalClaudeResponse(
                        success=False,
                        error=f"External script error: {error_msg}",
                        exit_code=process.returncode,
                        execution_time_seconds=0.0,
                        task_type=task_type,
                        timestamp=0.0
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
                timestamp=0.0
            )
            
        except Exception as e:
            logger.error(f"Error in external Claude analysis: {e}")
            return ExternalClaudeResponse(
                success=False,
                error=f"Integration error: {str(e)}",
                exit_code=-1,
                execution_time_seconds=0.0,
                task_type=task_type,
                timestamp=0.0
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
                    stderr=asyncio.subprocess.PIPE
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
                    stderr=asyncio.subprocess.PIPE
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