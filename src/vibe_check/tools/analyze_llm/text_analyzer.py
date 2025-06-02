"""
Text Analysis using Claude CLI

Core text analysis functionality using external Claude CLI for comprehensive
LLM-powered analysis with full reasoning capabilities.
"""

import asyncio
import logging
import tempfile
import time
from typing import Optional

from ..shared.claude_integration import analyze_content_async
from .llm_models import ExternalClaudeResponse

logger = logging.getLogger(__name__)


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
            full_content = f"{additional_context}\\n\\n{content}"
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
            
            prompt = f"{system_prompts.get(task_type, system_prompts['general'])}\\n\\n{full_content}"
            
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
                import os
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