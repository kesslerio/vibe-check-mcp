#!/usr/bin/env python3
"""
External Claude CLI integration script for MCP tools.

This script provides an isolated execution environment for Claude CLI calls,
preventing the context blocking issues that occur when calling Claude CLI
from within Claude Code MCP server context.

Usage:
    python external_claude_cli.py --prompt "Your prompt here" --task-type pr_review
    python external_claude_cli.py --input-file path/to/file.txt --task-type code_analysis
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
    
    def _find_claude_cli(self) -> str:
        """Find the Claude CLI executable path."""
        # Check if claude is in PATH
        try:
            result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Error finding Claude CLI: {e}")
        
        # Return default assumption
        return "claude"
    
    def _get_system_prompt(self, task_type: str) -> str:
        """
        Get specialized system prompt for task type.
        
        Args:
            task_type: Type of analysis task
            
        Returns:
            System prompt for the specific task
        """
        return self.SYSTEM_PROMPTS.get(task_type, self.SYSTEM_PROMPTS["general"])
    
    def _create_isolated_environment(self) -> Dict[str, str]:
        """
        Create isolated environment variables for Claude CLI execution.
        
        Returns:
            Environment dictionary with isolation markers
        """
        env = dict(os.environ)
        
        # Add isolation markers
        env["CLAUDE_EXTERNAL_EXECUTION"] = "true"
        env["CLAUDE_MCP_ISOLATED"] = "true"
        env["CLAUDE_TASK_ID"] = f"external_{int(time.time() * 1000)}"
        
        # Remove potentially conflicting variables
        for var in ["CLAUDE_CODE_MODE", "CLAUDE_CLI_SESSION", "MCP_SERVER"]:
            env.pop(var, None)
        
        return env
    
    async def execute_claude_cli(
        self,
        prompt: str,
        task_type: str = "general",
        additional_args: Optional[List[str]] = None
    ) -> ClaudeCliResult:
        """
        Execute Claude CLI using SDK best practices with JSON output and system prompts.
        
        Args:
            prompt: The prompt to send to Claude CLI
            task_type: Type of task for specialized handling
            additional_args: Additional CLI arguments
            
        Returns:
            ClaudeCliResult with execution details and SDK metadata
        """
        start_time = time.time()
        
        # Get system prompt for task type
        system_prompt = self._get_system_prompt(task_type)
        
        # Build command using SDK best practices
        command = [
            "timeout", str(self.timeout_seconds + 5),  # Use timeout command as recommended
            self.claude_cli_path, 
            "-p", prompt,
            "--output-format", "json",  # Use JSON format for structured responses
            "--system-prompt", system_prompt  # Use system prompt for task specialization
        ]
        
        if additional_args:
            command.extend(additional_args)
        
        command_str = " ".join(command)
        logger.info(f"Executing Claude CLI for task: {task_type}")
        logger.debug(f"Command: {command_str}")
        
        try:
            # Create isolated environment
            env = self._create_isolated_environment()
            
            # Execute in subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds + 10  # Allow extra time for timeout command
                )
                
                execution_time = time.time() - start_time
                
                # Handle output
                if process.returncode == 0 and stdout:
                    try:
                        # Parse JSON response from Claude CLI
                        sdk_response = json.loads(stdout.decode('utf-8'))
                        
                        logger.info(f"Claude CLI completed in {execution_time:.2f}s")
                        
                        return ClaudeCliResult(
                            success=not sdk_response.get("is_error", False),
                            output=sdk_response.get("result"),
                            error=None,
                            exit_code=process.returncode,
                            execution_time=execution_time,
                            command_used=command_str,
                            task_type=task_type,
                            cost_usd=sdk_response.get("cost_usd"),
                            duration_ms=sdk_response.get("duration_ms"),
                            session_id=sdk_response.get("session_id"),
                            num_turns=sdk_response.get("num_turns"),
                            sdk_metadata=sdk_response
                        )
                        
                    except json.JSONDecodeError as e:
                        # Fallback to text output if JSON parsing fails
                        logger.warning(f"Failed to parse JSON response: {e}")
                        return ClaudeCliResult(
                            success=True,
                            output=stdout.decode('utf-8').strip(),
                            error=stderr.decode('utf-8').strip() if stderr else None,
                            exit_code=process.returncode,
                            execution_time=execution_time,
                            command_used=command_str,
                            task_type=task_type
                        )
                else:
                    # Handle error response
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                    return ClaudeCliResult(
                        success=False,
                        error=error_msg.strip(),
                        exit_code=process.returncode,
                        execution_time=execution_time,
                        command_used=command_str,
                        task_type=task_type
                    )
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                
                execution_time = time.time() - start_time
                logger.warning(f"Claude CLI timed out after {self.timeout_seconds + 10}s")
                
                return ClaudeCliResult(
                    success=False,
                    error=f"Command timed out after {self.timeout_seconds + 10} seconds",
                    exit_code=-1,
                    execution_time=execution_time,
                    command_used=command_str,
                    task_type=task_type
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing Claude CLI: {e}")
            
            return ClaudeCliResult(
                success=False,
                error=f"Execution error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                command_used=command_str,
                task_type=task_type
            )
    
    async def analyze_content(
        self,
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None
    ) -> ClaudeCliResult:
        """
        Analyze content using specialized system prompts for the task type.
        
        Args:
            content: Content to analyze
            task_type: Type of analysis (pr_review, code_analysis, etc.)
            additional_context: Optional additional context
            
        Returns:
            ClaudeCliResult with analysis
        """
        # Build prompt with content and context
        if additional_context:
            prompt = f"{additional_context}\n\nContent to analyze:\n{content}"
        else:
            prompt = f"Analyze the following content:\n\n{content}"
        
        return await self.execute_claude_cli(
            prompt=prompt,
            task_type=task_type
        )
    
    async def analyze_file(
        self,
        file_path: str,
        task_type: str = "code_analysis"
    ) -> ClaudeCliResult:
        """
        Analyze a file using Claude CLI.
        
        Args:
            file_path: Path to file to analyze
            task_type: Type of analysis
            
        Returns:
            ClaudeCliResult with file analysis
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add file context
            file_context = f"File: {file_path}\nSize: {len(content)} characters"
            
            return await self.analyze_content(
                content=content,
                task_type=task_type,
                additional_context=file_context
            )
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ClaudeCliResult(
                success=False,
                error=f"File read error: {str(e)}",
                exit_code=-1,
                task_type=task_type
            )


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
        result = await executor.analyze_file(args.input_file, args.task_type)
    else:
        result = await executor.execute_claude_cli(args.prompt, args.task_type)
    
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