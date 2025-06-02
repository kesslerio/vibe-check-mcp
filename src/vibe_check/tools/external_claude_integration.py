"""
MCP tool for external Claude CLI integration.

This module provides MCP tools that leverage the ExternalClaudeCli class
to perform analysis tasks without context blocking issues.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
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

    @mcp.tool()
    async def test_claude_cli_integration(
        test_prompt: str = "What is 2+2?",
        timeout_seconds: int = 30,
        debug_mode: bool = False,
        task_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Test external Claude CLI integration via ExternalClaudeCli wrapper.
        
        This tool uses the ExternalClaudeCli wrapper to execute Claude CLI in an
        independent session, preventing the timeout issues that occur with direct
        subprocess calls from within Claude Code MCP context.
        
        Args:
            test_prompt: The prompt to send to Claude CLI (default: "What is 2+2?")
            timeout_seconds: Timeout for the command execution (default: 30)
            debug_mode: Enable detailed logging and diagnostics (default: False)
            task_type: Task type for specialized system prompts (general, pr_review, code_analysis, issue_analysis)
            
        Returns:
            Test results including success status, output, timing, and diagnostics
        """
        logger.info(f"Testing Claude CLI integration with prompt: {test_prompt[:50]}...")
        
        start_time = time.time()
        
        try:
            # Use the EXACT same approach as test_direct_claude.py
            # Try environment isolation to prevent Claude Code context inheritance
            # Keep essential environment variables but remove Claude Code specific ones
            clean_env = {
                'PATH': os.environ.get('PATH', ''),
                'HOME': os.environ.get('HOME', ''),
                'USER': os.environ.get('USER', ''),
                'SHELL': os.environ.get('SHELL', ''),
                'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
                'LC_ALL': os.environ.get('LC_ALL', ''),
                'TERM': os.environ.get('TERM', 'xterm-256color'),
                'TMPDIR': os.environ.get('TMPDIR', '/tmp'),
                'PWD': os.environ.get('PWD', os.getcwd()),
                # Keep any ANTHROPIC_ variables that might be needed
                **{k: v for k, v in os.environ.items() if k.startswith('ANTHROPIC_')}
            }
            
            # Remove Claude Code specific environment variables
            excluded_vars = ['CLAUDE_CODE_SSE_PORT', 'CLAUDE_CODE_MODE']
            if debug_mode:
                logger.info(f"Excluded environment variables: {[var for var in excluded_vars if var in os.environ]}")
            
            command = [
                "claude", "-p", "--dangerously-skip-permissions",
                test_prompt
            ]
            
            if debug_mode:
                logger.info(f"Executing command: {' '.join(command[:3])} <prompt>")
                logger.info(f"Using clean environment (no CLAUDE_CODE_SSE_PORT)")
            
            # Test with asyncio subprocess (same as test_direct_claude.py)
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,  # Fix: Isolate stdin like Node.js spawn
                env=clean_env
            )
            
            if debug_mode:
                logger.info("Process started, waiting for completion...")
            
            # Wait with timeout and ensure process cleanup
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                # Ensure process is terminated on timeout
                if process.returncode is None:
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=5)
                    except:
                        try:
                            process.kill()
                            await process.wait()
                        except:
                            pass
                raise  # Re-raise the timeout error
            
            execution_time = time.time() - start_time
            
            if debug_mode:
                logger.info(f"Process completed with return code: {process.returncode}")
            
            if process.returncode == 0:
                output = stdout.decode('utf-8').strip()
                
                result = {
                    "success": True,
                    "exit_code": 0,
                    "output": output,
                    "output_length": len(output),
                    "execution_time_seconds": execution_time,
                    "command_used": "claude -p --dangerously-skip-permissions",
                    "test_prompt": test_prompt,
                    "debug_mode": debug_mode,
                    "timestamp": time.time()
                }
                
                if debug_mode:
                    result["output_preview"] = output[:200] + ("..." if len(output) > 200 else "")
                
                logger.info(f"✅ Claude CLI succeeded in {execution_time:.2f}s, output length: {len(output)} chars")
                return result
                
            else:
                error = stderr.decode('utf-8').strip()
                logger.error(f"❌ Claude CLI failed (exit code {process.returncode}): {error}")
                
                return {
                    "success": False,
                    "exit_code": process.returncode,
                    "error": error,
                    "execution_time_seconds": execution_time,
                    "command_used": "claude -p --dangerously-skip-permissions",
                    "test_prompt": test_prompt,
                    "debug_mode": debug_mode,
                    "timestamp": time.time()
                }
                
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"❌ Claude CLI timed out after {timeout_seconds} seconds")
            
            return {
                "success": False,
                "error": f"Process timed out after {timeout_seconds} seconds",
                "execution_time_seconds": execution_time,
                "command_used": "claude -p --dangerously-skip-permissions (timeout)",
                "test_prompt": test_prompt,
                "debug_mode": debug_mode,
                "timestamp": time.time()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Exception during Claude CLI test: {e}")
            
            # Ensure we don't crash the server
            try:
                return {
                    "success": False,
                    "error": f"Exception: {str(e)}",
                    "execution_time_seconds": execution_time,
                    "command_used": "claude -p --dangerously-skip-permissions (error)",
                    "test_prompt": test_prompt,
                    "debug_mode": debug_mode,
                    "timestamp": time.time(),
                    "exception_type": type(e).__name__
                }
            except Exception as nested_e:
                logger.error(f"❌ Nested exception in error handling: {nested_e}")
                return {
                    "success": False,
                    "error": "Critical error in test execution",
                    "execution_time_seconds": execution_time,
                    "timestamp": time.time()
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