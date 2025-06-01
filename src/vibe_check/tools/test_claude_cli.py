"""
Test MCP tool for Claude CLI integration.

This tool tests if Claude Code CLI (claude -p) can be invoked successfully
via MCP tools to verify integration functionality.
"""

import asyncio
import subprocess
import tempfile
import json
from typing import Dict, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel


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


def register_claude_cli_test_tool(mcp: FastMCP) -> None:
    """Register the Claude CLI test tool with the MCP server."""
    
    @mcp.tool()
    async def test_claude_cli_integration(
        test_prompt: str = "What is 2+2?",
        timeout_seconds: int = 30
    ) -> ClaudeCliTestResponse:
        """
        Test Claude CLI integration via MCP tool.
        
        This tool attempts to execute the Claude Code CLI (claude -p) with a simple
        prompt to verify that the integration works correctly from within MCP tools.
        
        Args:
            test_prompt: The prompt to send to Claude CLI (default: "What is 2+2?")
            timeout_seconds: Timeout for the command execution (default: 30)
            
        Returns:
            Test results including success status, output, and timing information
        """
        import time
        start_time = time.time()
        
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
                
                if result.returncode == 0:
                    return ClaudeCliTestResponse(
                        success=True,
                        output=result.stdout.strip(),
                        error=result.stderr.strip() if result.stderr else None,
                        exit_code=result.returncode,
                        command_used=command_str,
                        execution_time_seconds=execution_time
                    )
                else:
                    return ClaudeCliTestResponse(
                        success=False,
                        output=result.stdout.strip() if result.stdout else None,
                        error=result.stderr.strip(),
                        exit_code=result.returncode,
                        command_used=command_str,
                        execution_time_seconds=execution_time
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