"""
LLM Analysis Tool Registry

Registers all LLM-powered analysis tools with the MCP server and provides
status checking functionality.
"""

import asyncio
import logging
import time
from typing import Dict, Any

from fastmcp import FastMCP

from .text_analyzer import analyze_text_llm
from .specialized_analyzers import (
    analyze_pr_llm,
    analyze_code_llm, 
    analyze_issue_llm,
    analyze_github_issue_llm,
    analyze_github_pr_llm
)
from .llm_models import ExternalClaudeResponse

logger = logging.getLogger(__name__)


def register_llm_analysis_tools(mcp: FastMCP) -> None:
    """Register LLM-powered analysis tools with the MCP server."""
    
    # Register the text analyzer
    mcp.tool()(analyze_text_llm)
    
    # Register specialized analyzers  
    mcp.tool()(analyze_pr_llm)
    mcp.tool()(analyze_code_llm)
    mcp.tool()(analyze_issue_llm)
    mcp.tool()(analyze_github_issue_llm)
    mcp.tool()(analyze_github_pr_llm)
    
    # Register async analysis tools
    mcp.tool()(check_async_analysis_status)
    mcp.tool()(get_async_system_status)
    
    # Register status tool
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
                    stdin=asyncio.subprocess.DEVNULL
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
                    stdin=asyncio.subprocess.DEVNULL
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
            
            import os
            logger.info(f"CLAUDE_CODE_SSE_PORT present: {'CLAUDE_CODE_SSE_PORT' in os.environ}")
            
            # Use inherited environment (no isolation)
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
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


# Async Analysis Tools
async def check_async_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """
    Check the status of a queued async analysis.
    
    This tool allows users to monitor the progress of massive PRs that are
    being processed in the background queue system.
    
    Args:
        analysis_id: The job ID returned from starting an async analysis
        
    Returns:
        Comprehensive status information including progress, timing, and results
    """
    logger.info(f"Checking async analysis status for job {analysis_id}")
    
    try:
        from ..async_analysis.integration import check_analysis_status
        
        result = await check_analysis_status(analysis_id)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error checking async analysis status: {e}")
        return {
            "status": "error",
            "error": f"Failed to check analysis status: {str(e)}",
            "analysis_id": analysis_id
        }


async def get_async_system_status() -> Dict[str, Any]:
    """
    Get the overall status of the async analysis system.
    
    This tool provides system-wide information about the background processing
    queue, active workers, and performance metrics.
    
    Returns:
        System status including queue metrics, worker status, and performance data
    """
    logger.info("Getting async analysis system status")
    
    try:
        from ..async_analysis.integration import get_system_status
        
        result = await get_system_status()
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting async system status: {e}")
        return {
            "status": "error",
            "error": f"Failed to get system status: {str(e)}"
        }