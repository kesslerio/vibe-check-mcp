"""
User diagnostic tools for Claude CLI integration.

This module provides essential diagnostic capabilities for end users to
troubleshoot Claude CLI issues. These are the essential tools that normal
users need, separated from comprehensive development testing tools.
"""

import asyncio
import concurrent.futures
import os
import subprocess
import time
import logging
from typing import Dict, Any

# FastMCP import moved inside functions to avoid early environment loading
from vibe_check.core.vibe_config import get_vibe_config, vibe_message

logger = logging.getLogger(__name__)


def register_diagnostic_tools(mcp) -> None:
    """Register user diagnostic tools with the MCP server."""
    
    @mcp.tool()
    async def claude_cli_status() -> Dict[str, Any]:
        """
        Check Claude CLI availability and version information.
        
        Essential diagnostic tool for users to verify their Claude CLI installation
        and get version details. This tool helps troubleshoot basic setup issues.
        
        Returns:
            Information about Claude CLI availability, version, and path
        """
        try:
            def check_availability():
                # Test if claude command exists
                which_result = subprocess.run(
                    ["which", "claude"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if which_result.returncode == 0:
                    claude_path = which_result.stdout.strip()
                    
                    # Try to get version
                    version_result = subprocess.run(
                        ["claude", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return {
                        "available": True,
                        "path": claude_path,
                        "version_info": {
                            "stdout": version_result.stdout.strip(),
                            "stderr": version_result.stderr.strip(),
                            "exit_code": version_result.returncode
                        },
                        "vibe": "✅ Claude CLI is vibing perfectly"
                    }
                else:
                    return {
                        "available": False,
                        "error": "Claude CLI not found in PATH",
                        "which_output": which_result.stderr.strip(),
                        "vibe": "❌ Claude CLI went missing",
                        "fix_the_vibe": "Get Claude CLI installed or add it to your PATH"
                    }
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(executor, check_availability)
                
        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking Claude CLI availability: {str(e)}",
                "vibe": "⚠️ Can't read Claude CLI's vibe right now",
                "suggestion": "Check your system configuration and try again"
            }

    @mcp.tool()
    async def claude_cli_diagnostics() -> Dict[str, Any]:
        """
        Diagnose Claude CLI integration issues and timeout problems.
        
        Essential diagnostic tool for users experiencing Claude CLI timeout issues
        or recursion problems when using Claude CLI from within Claude Code.
        Provides actionable guidance for troubleshooting.
        
        Returns:
            Detailed diagnosis of potential issues and recommended solutions
        """
        start_time = time.time()
        
        # Check environment for potential issues
        env_indicators = {
            "claude_code_mode": os.environ.get("CLAUDE_CODE_MODE"),
            "claude_cli_session": os.environ.get("CLAUDE_CLI_SESSION"),
            "mcp_server": os.environ.get("MCP_SERVER"),
            "term": os.environ.get("TERM"),
            "parent_process": os.environ.get("CLAUDE_PARENT_PROCESS"),
            "pwd": os.getcwd(),
            "path_has_claude": "/claude" in os.environ.get("PATH", "")
        }
        
        # Test basic subprocess functionality
        try:
            echo_result = subprocess.run(
                ["echo", "Claude CLI diagnostics test"],
                capture_output=True,
                text=True,
                timeout=5
            )
            basic_subprocess_works = echo_result.returncode == 0
        except Exception:
            basic_subprocess_works = False
            
        # Analyze potential issues
        issues_found = []
        recommendations = []
        risk_level = "low"
        
        if env_indicators["claude_code_mode"]:
            issues_found.append("Running within Claude Code environment")
            recommendations.append("Consider using external scripts for Claude CLI calls")
            risk_level = "medium"
            
        if env_indicators["claude_cli_session"]:
            issues_found.append("Claude CLI session already active")
            recommendations.append("Exit current Claude CLI session before testing")
            risk_level = "high"
            
        if not basic_subprocess_works:
            issues_found.append("Basic subprocess functionality not working")
            recommendations.append("Check system permissions and shell configuration")
            risk_level = "high"
            
        # Generate user-friendly status
        if risk_level == "low":
            vibe = "✅ Claude CLI vibes are looking good"
        elif risk_level == "medium":
            vibe = "⚠️ Claude CLI might get moody with timeouts"
        else:
            vibe = "❌ Claude CLI vibes are way off"
            
        # Add general recommendations
        if not recommendations:
            recommendations.append("Claude CLI integration looks healthy")
        else:
            recommendations.append("Use external Claude CLI wrapper tools when available")
            recommendations.append("Set shorter timeouts if experiencing delays")
            
        execution_time = time.time() - start_time
        
        return {
            "vibe": vibe,
            "risk_level": risk_level,
            "issues_found": issues_found,
            "recommendations": recommendations,
            "environment_details": env_indicators,
            "basic_subprocess_works": basic_subprocess_works,
            "execution_time_seconds": execution_time,
            "summary": f"Diagnostic complete. Risk level: {risk_level}. " + 
                      f"{'No issues detected.' if not issues_found else f'{len(issues_found)} potential issues found.'}"
        }