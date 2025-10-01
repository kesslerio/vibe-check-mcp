"""
LLM Analysis Tool Registry

Registers all LLM-powered analysis tools with the MCP server and provides
status checking functionality.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List

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


def register_llm_production_tools(mcp) -> None:
    """Register production LLM-powered analysis tools with the MCP server.

    These are the core analysis tools that end users need for anti-pattern detection
    and code analysis. Always enabled in production mode.

    Tools registered (6 total):
    - analyze_text_llm
    - analyze_pr_llm
    - analyze_code_llm
    - analyze_issue_llm
    - analyze_github_issue_llm
    - analyze_github_pr_llm
    """
    logger.info("Registering production LLM analysis tools...")

    # Register the text analyzer
    mcp.tool()(analyze_text_llm)

    # Register specialized analyzers
    mcp.tool()(analyze_pr_llm)
    mcp.tool()(analyze_code_llm)
    mcp.tool()(analyze_issue_llm)
    mcp.tool()(analyze_github_issue_llm)
    mcp.tool()(analyze_github_pr_llm)


def register_llm_diagnostic_tools(mcp) -> None:
    """Register diagnostic LLM tools with the MCP server.

    These tools are for system monitoring, health checking, and debugging.
    Only enabled when VIBE_CHECK_DIAGNOSTICS=true.

    Tools registered (7 total):
    - check_async_analysis_status
    - get_async_system_status
    - async_system_health_check
    - async_system_metrics
    - async_system_degradation_status
    - analyze_llm_status
    - test_claude_cli_with_env
    """
    logger.info("Registering diagnostic LLM tools...")

    # Register async analysis monitoring tools
    mcp.tool()(check_async_analysis_status)
    mcp.tool()(get_async_system_status)
    mcp.tool()(async_system_health_check)
    mcp.tool()(async_system_metrics)
    mcp.tool()(async_system_degradation_status)

    # Register status tool
    @mcp.tool()
    async def analyze_llm_status() -> Dict[str, Any]:
        """
        [DIAGNOSTIC] Check the status of external Claude CLI integration.
        
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
        [DIAGNOSTIC] Test Claude CLI without environment isolation (inherits all env vars).
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
    [DIAGNOSTIC] Check the status of a queued async analysis.
    
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
    [DIAGNOSTIC] Get the overall status of the async analysis system.
    
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


# Health Monitoring Tools
async def async_system_health_check(detailed: bool = False) -> Dict[str, Any]:
    """
    [DIAGNOSTIC] Perform comprehensive health check of the async analysis system.
    
    This tool provides detailed health diagnostics for all system components
    including queue, workers, resource monitoring, and external dependencies.
    
    Args:
        detailed: Whether to include detailed component information
        
    Returns:
        Comprehensive health check results with component status and metrics
    """
    logger.info("Performing async system health check")
    
    try:
        from ..async_analysis.health_monitoring import get_global_health_monitor
        
        health_monitor = get_global_health_monitor()
        
        if detailed:
            # Perform full health check
            health_results = await health_monitor.perform_comprehensive_health_check()
            
            return {
                "status": "health_check_complete",
                "summary": health_monitor.get_health_summary(),
                "detailed_results": {
                    component: result.to_dict() 
                    for component, result in health_results.items()
                },
                "alerts": health_monitor.alerts[-10:] if health_monitor.alerts else [],
                "timestamp": time.time()
            }
        else:
            # Quick health summary
            summary = health_monitor.get_health_summary()
            
            return {
                "status": "health_summary",
                "summary": summary,
                "timestamp": time.time()
            }
        
    except Exception as e:
        logger.error(f"Error performing health check: {e}")
        return {
            "status": "error",
            "error": f"Health check failed: {str(e)}"
        }


async def async_system_metrics(
    include_trends: bool = True,
    include_history: bool = False
) -> Dict[str, Any]:
    """
    [DIAGNOSTIC] Get comprehensive metrics for the async analysis system.
    
    This tool provides performance metrics, resource utilization,
    and system statistics for monitoring and optimization.
    
    Args:
        include_trends: Whether to include trend analysis
        include_history: Whether to include historical data points
        
    Returns:
        Comprehensive system metrics with performance indicators
    """
    logger.info("Collecting async system metrics")
    
    try:
        from ..async_analysis.health_monitoring import get_global_health_monitor
        
        health_monitor = get_global_health_monitor()
        
        # Collect current metrics
        current_metrics = await health_monitor.collect_system_metrics()
        metrics_summary = health_monitor.get_metrics_summary()
        
        result = {
            "status": "metrics_collected",
            "current_metrics": current_metrics.to_dict(),
            "summary": metrics_summary,
            "collection_timestamp": time.time()
        }
        
        if include_history and health_monitor.metrics_history:
            # Include recent historical data
            recent_history = health_monitor.metrics_history[-50:]  # Last 50 data points
            result["historical_data"] = [m.to_dict() for m in recent_history]
        
        if include_trends:
            # Add additional trend analysis
            result["trends"] = _calculate_extended_trends(health_monitor.metrics_history)
        
        return result
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return {
            "status": "error",
            "error": f"Metrics collection failed: {str(e)}"
        }


def _calculate_extended_trends(metrics_history: List) -> Dict[str, Any]:
    """Calculate extended trend analysis from metrics history."""
    if len(metrics_history) < 5:
        return {"message": "Insufficient data for trend analysis"}
    
    trends = {}
    
    try:
        # Get recent vs older data
        recent_20 = metrics_history[-20:] if len(metrics_history) >= 20 else metrics_history
        older_20 = metrics_history[-40:-20] if len(metrics_history) >= 40 else []
        
        if older_20:
            # Queue utilization trend
            recent_queue = [m.queue_size for m in recent_20]
            older_queue = [m.queue_size for m in older_20]
            
            recent_avg_queue = sum(recent_queue) / len(recent_queue)
            older_avg_queue = sum(older_queue) / len(older_queue)
            
            if older_avg_queue > 0:
                queue_trend = ((recent_avg_queue - older_avg_queue) / older_avg_queue) * 100
                trends["queue_utilization_change_percent"] = round(queue_trend, 2)
            
            # System resource trends
            recent_memory = [m.system_memory_percent for m in recent_20]
            older_memory = [m.system_memory_percent for m in older_20]
            
            if recent_memory and older_memory:
                memory_trend = (sum(recent_memory) / len(recent_memory)) - (sum(older_memory) / len(older_memory))
                trends["memory_usage_change_percent"] = round(memory_trend, 2)
        
        # Overall health trend
        health_states = [m.overall_health for m in recent_20]
        healthy_ratio = health_states.count("healthy") / len(health_states)
        trends["health_stability_percent"] = round(healthy_ratio * 100, 2)
        
    except Exception as e:
        trends["error"] = f"Trend calculation error: {str(e)}"
    
    return trends


async def async_system_degradation_status(
    pr_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    [DIAGNOSTIC] Get graceful degradation status and recommendations.
    
    This tool provides information about system availability, fallback usage,
    and recommended strategies for handling requests during system issues.
    
    Args:
        pr_data: Optional PR metadata to get specific recommendations
        
    Returns:
        Degradation status with recommendations and fallback statistics
    """
    logger.info("Getting async system degradation status")
    
    try:
        from ..async_analysis.graceful_degradation import get_global_degradation_manager
        
        degradation_manager = get_global_degradation_manager()
        
        # Check current system availability
        availability = await degradation_manager.check_system_availability()
        
        # Get fallback statistics
        fallback_stats = degradation_manager.get_fallback_stats()
        
        result = {
            "status": "degradation_status_retrieved",
            "system_availability": availability.value,
            "fallback_statistics": fallback_stats,
            "timestamp": time.time()
        }
        
        # Get specific recommendations if PR data provided
        if pr_data:
            strategy = degradation_manager.get_recommended_strategy(pr_data)
            result["recommended_strategy"] = strategy
        
        # Add general recommendations based on availability
        if availability.value == "fully_available":
            result["general_recommendation"] = "System operating normally, all features available"
        elif availability.value == "degraded":
            result["general_recommendation"] = "System degraded, expect slower responses and possible fallbacks"
        elif availability.value == "partial_failure":
            result["general_recommendation"] = "System experiencing issues, fallbacks likely for complex operations"
        else:  # unavailable
            result["general_recommendation"] = "System unavailable, only basic pattern detection available"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting degradation status: {e}")
        return {
            "status": "error",
            "error": f"Degradation status check failed: {str(e)}"
        }


def register_llm_analysis_tools(mcp) -> None:
    """Register all LLM-powered analysis tools with the MCP server.

    Backward-compatible wrapper that registers both production and diagnostic tools.
    This function is maintained for backward compatibility with existing tests.

    Use register_llm_production_tools() and register_llm_diagnostic_tools()
    separately for fine-grained control in production deployments.
    """
    logger.info("Registering all LLM analysis tools (production + diagnostic)...")
    register_llm_production_tools(mcp)
    register_llm_diagnostic_tools(mcp)