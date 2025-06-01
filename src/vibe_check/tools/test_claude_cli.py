"""
Test MCP tool for Claude CLI integration.

This tool tests if Claude Code CLI (claude -p) can be invoked successfully
via MCP tools to verify integration functionality.
"""

import asyncio
import subprocess
import tempfile
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ClaudeCliTestRequest(BaseModel):
    """Request model for Claude CLI test."""
    test_prompt: str = "What is 2+2?"
    timeout_seconds: int = 30


class ClaudeCliTestResponse(BaseModel):
    """Response model for Claude CLI test."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    command_used: str
    execution_time_seconds: float
    diagnostics: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None


def register_claude_cli_test_tool(mcp: FastMCP) -> None:
    """Register the Claude CLI test tool with the MCP server."""
    
    @mcp.tool()
    async def test_claude_cli_integration(
        test_prompt: str = "What is 2+2?",
        timeout_seconds: int = 30,
        debug_mode: bool = False
    ) -> ClaudeCliTestResponse:
        """
        Test Claude CLI integration via MCP tool with enhanced diagnostics.
        
        This tool attempts to execute the Claude Code CLI (claude -p) with a simple
        prompt to verify that the integration works correctly from within MCP tools.
        Includes comprehensive error reporting and validation.
        
        Args:
            test_prompt: The prompt to send to Claude CLI (default: "What is 2+2?")
            timeout_seconds: Timeout for the command execution (default: 30)
            debug_mode: Enable detailed logging and diagnostics (default: False)
            
        Returns:
            Test results including success status, output, timing, and diagnostics
        """
        import time
        start_time = time.time()
        
        if debug_mode:
            logger.info(f"Starting Claude CLI integration test with prompt: {test_prompt[:50]}...")
            logger.info(f"Environment: MCP_SERVER={os.environ.get('MCP_SERVER', 'unknown')}")
            logger.info(f"Claude CLI path: {os.environ.get('PATH', '').split(':')[0]}...")
        
        # Create a temporary file for the prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_prompt)
            prompt_file = f.name
        
        try:
            # Construct the Claude CLI command
            command = ["claude", "-p", test_prompt]
            command_str = " ".join(command)
            
            # Use a thread executor to avoid async subprocess issues with Claude CLI
            import concurrent.futures
            import subprocess
            
            def run_claude_command():
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        cwd=Path.cwd(),
                        env=dict(os.environ, CLAUDE_PARENT_PROCESS="mcp-server")
                    )
                    return result
                except subprocess.TimeoutExpired:
                    return None
                except Exception as e:
                    raise e
            
            loop = asyncio.get_event_loop()
            
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, run_claude_command)
                
                execution_time = time.time() - start_time
                
                if result is None:
                    return ClaudeCliTestResponse(
                        success=False,
                        output=None,
                        error=f"Command timed out after {timeout_seconds} seconds",
                        exit_code=-1,
                        command_used=command_str,
                        execution_time_seconds=execution_time
                    )
                
                # Enhanced validation and diagnostics
                diagnostics = {
                    "process_id": os.getpid(),
                    "working_directory": str(Path.cwd()),
                    "environment_vars": {
                        "CLAUDE_PARENT_PROCESS": os.environ.get("CLAUDE_PARENT_PROCESS"),
                        "PATH_contains_claude": "/claude" in os.environ.get("PATH", ""),
                        "TERM": os.environ.get("TERM"),
                    },
                    "command_length": len(command_str),
                    "prompt_length": len(test_prompt)
                }
                
                validation = {}
                if result.returncode == 0 and result.stdout:
                    output_text = result.stdout.strip()
                    validation = {
                        "has_output": bool(output_text),
                        "output_length": len(output_text),
                        "appears_reasonable": len(output_text) > 0 and len(output_text) < 10000,
                        "contains_expected_answer": "4" in output_text if "2+2" in test_prompt else None
                    }
                
                if result.returncode == 0:
                    return ClaudeCliTestResponse(
                        success=True,
                        output=result.stdout.strip(),
                        error=result.stderr.strip() if result.stderr else None,
                        exit_code=result.returncode,
                        command_used=command_str,
                        execution_time_seconds=execution_time,
                        diagnostics=diagnostics,
                        validation=validation
                    )
                else:
                    return ClaudeCliTestResponse(
                        success=False,
                        output=result.stdout.strip() if result.stdout else None,
                        error=result.stderr.strip(),
                        exit_code=result.returncode,
                        command_used=command_str,
                        execution_time_seconds=execution_time,
                        diagnostics=diagnostics,
                        validation=validation
                    )
                    
            except Exception as subprocess_error:
                execution_time = time.time() - start_time
                return ClaudeCliTestResponse(
                    success=False,
                    output=None,
                    error=f"Subprocess error: {str(subprocess_error)}",
                    exit_code=-1,
                    command_used=command_str,
                    execution_time_seconds=execution_time
                )
                
        except FileNotFoundError:
            execution_time = time.time() - start_time
            return ClaudeCliTestResponse(
                success=False,
                output=None,
                error="Claude CLI not found. Make sure 'claude' command is available in PATH.",
                exit_code=-1,
                command_used=command_str,
                execution_time_seconds=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ClaudeCliTestResponse(
                success=False,
                output=None,
                error=f"Unexpected error: {str(e)}",
                exit_code=-1,
                command_used=command_str,
                execution_time_seconds=execution_time
            )
        finally:
            # Clean up temporary file
            try:
                Path(prompt_file).unlink()
            except Exception:
                pass


    @mcp.tool()
    async def test_claude_cli_availability() -> Dict[str, Any]:
        """
        Test if Claude CLI is available and get version information.
        
        Returns:
            Information about Claude CLI availability, version, and path
        """
        try:
            import concurrent.futures
            import subprocess
            
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
                        }
                    }
                else:
                    return {
                        "available": False,
                        "error": "Claude CLI not found in PATH",
                        "which_output": which_result.stderr.strip()
                    }
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(executor, check_availability)
                
        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking Claude CLI availability: {str(e)}"
            }


    @mcp.tool()
    async def test_claude_cli_with_file_input() -> Dict[str, Any]:
        """
        Test Claude CLI with file input to verify file handling works.
        
        Returns:
            Test results for file-based input to Claude CLI
        """
        import time
        start_time = time.time()
        
        # Create a test file
        test_content = """
# Test Code Analysis

def calculate_sum(a, b):
    return a + b

def main():
    result = calculate_sum(2, 3)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            # Test Claude CLI with file input using thread executor
            command = ["claude", "-p", f"Analyze this Python code for any issues: {test_file}"]
            
            import concurrent.futures
            import subprocess
            
            def run_file_command():
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=45,
                        env=dict(os.environ, CLAUDE_PARENT_PROCESS="mcp-server")
                    )
                    return result
                except subprocess.TimeoutExpired:
                    return None
                except Exception as e:
                    raise e
            
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_file_command)
            
            execution_time = time.time() - start_time
            
            if result is None:
                return {
                    "success": False,
                    "error": "Command timed out after 45 seconds",
                    "command": " ".join(command),
                    "test_file_path": test_file,
                    "execution_time_seconds": execution_time
                }
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.stderr else None,
                "exit_code": result.returncode,
                "command": " ".join(command),
                "test_file_path": test_file,
                "execution_time_seconds": execution_time
            }
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": "Command timed out after 45 seconds",
                "execution_time_seconds": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "execution_time_seconds": execution_time
            }
        finally:
            # Clean up test file
            try:
                Path(test_file).unlink()
            except Exception:
                pass


    @mcp.tool()
    async def test_claude_cli_comprehensive() -> Dict[str, Any]:
        """
        Comprehensive Claude CLI test suite with multiple scenarios.
        
        Tests various prompts and use cases to validate Claude CLI integration
        across different types of requests and edge cases.
        
        Returns:
            Comprehensive test results with detailed analysis
        """
        test_scenarios = [
            {
                "name": "simple_math",
                "prompt": "What is 7+3? Answer with just the number.",
                "expected_pattern": r"\b10\b",
                "timeout": 20
            },
            {
                "name": "text_analysis", 
                "prompt": "Analyze this sentence: 'The quick brown fox jumps.' What is the subject?",
                "expected_pattern": r"fox|subject",
                "timeout": 30
            },
            {
                "name": "code_review",
                "prompt": "Review this code: def add(a,b): return a+b. Is this good Python?",
                "expected_pattern": r"good|yes|function|valid",
                "timeout": 30
            }
        ]
        
        results = {
            "overall_success": True,
            "tests_passed": 0,
            "tests_failed": 0,
            "scenario_results": [],
            "summary": ""
        }
        
        for scenario in test_scenarios:
            try:
                # Use the existing integration test for each scenario
                test_result = await test_claude_cli_integration(
                    test_prompt=scenario["prompt"],
                    timeout_seconds=scenario["timeout"],
                    debug_mode=True
                )
                
                import re
                pattern_match = False
                if test_result.success and test_result.output:
                    pattern_match = bool(re.search(scenario["expected_pattern"], test_result.output, re.IGNORECASE))
                
                scenario_result = {
                    "name": scenario["name"],
                    "success": test_result.success and pattern_match,
                    "execution_time": test_result.execution_time_seconds,
                    "output_preview": test_result.output[:100] if test_result.output else None,
                    "pattern_matched": pattern_match,
                    "error": test_result.error
                }
                
                results["scenario_results"].append(scenario_result)
                
                if scenario_result["success"]:
                    results["tests_passed"] += 1
                else:
                    results["tests_failed"] += 1
                    results["overall_success"] = False
                    
            except Exception as e:
                results["scenario_results"].append({
                    "name": scenario["name"],
                    "success": False,
                    "error": f"Test framework error: {str(e)}"
                })
                results["tests_failed"] += 1
                results["overall_success"] = False
        
        # Generate summary
        total_tests = len(test_scenarios)
        results["summary"] = f"Passed {results['tests_passed']}/{total_tests} tests. " + \
                           ("All tests successful!" if results["overall_success"] else "Some tests failed.")
        
        return results


    @mcp.tool()
    async def test_claude_cli_mcp_permissions() -> Dict[str, Any]:
        """
        Test Claude CLI with MCP server permissions bypass.
        
        Tests claude -p --dangerously-skip-permissions with MCP server access
        to verify that Claude CLI can properly interact with a limited set of MCP servers.
        
        Returns:
            Test results for MCP permissions functionality
        """
        import time
        start_time = time.time()
        
        logger.info("Testing Claude CLI MCP permissions bypass...")
        
        # Test command with MCP permissions bypass
        test_prompt = "Use the vibe-check MCP server to check server status"
        command = [
            "claude", 
            "-p", 
            test_prompt,
            "--dangerously-skip-permissions"
        ]
        
        try:
            import concurrent.futures
            import subprocess
            
            def run_mcp_command():
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=45,  # Longer timeout for MCP operations
                        env=dict(os.environ, CLAUDE_PARENT_PROCESS="mcp-server")
                    )
                    return result
                except subprocess.TimeoutExpired:
                    return None
                except Exception as e:
                    raise e
            
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_mcp_command)
            
            execution_time = time.time() - start_time
            
            if result is None:
                return {
                    "success": False,
                    "error": "Command timed out after 45 seconds",
                    "command": " ".join(command),
                    "execution_time_seconds": execution_time,
                    "test_type": "mcp_permissions"
                }
            
            # Analyze the output for MCP-related content
            success_indicators = []
            if result.stdout:
                output_lower = result.stdout.lower()
                if "mcp" in output_lower:
                    success_indicators.append("mentions_mcp")
                if "server" in output_lower:
                    success_indicators.append("mentions_server")
                if "vibe" in output_lower or "check" in output_lower:
                    success_indicators.append("mentions_vibe_check")
                if "status" in output_lower:
                    success_indicators.append("mentions_status")
            
            return {
                "success": result.returncode == 0 and len(success_indicators) > 0,
                "output": result.stdout.strip() if result.stdout else None,
                "error": result.stderr.strip() if result.stderr else None,
                "exit_code": result.returncode,
                "command": " ".join(command),
                "execution_time_seconds": execution_time,
                "test_type": "mcp_permissions",
                "mcp_indicators_found": success_indicators,
                "validation": {
                    "has_mcp_content": len(success_indicators) > 0,
                    "permissions_bypassed": "--dangerously-skip-permissions" in " ".join(command),
                    "output_reasonable": result.stdout and len(result.stdout.strip()) > 10 if result.stdout else False
                }
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"MCP test error: {str(e)}",
                "command": " ".join(command),
                "execution_time_seconds": execution_time,
                "test_type": "mcp_permissions"
            }