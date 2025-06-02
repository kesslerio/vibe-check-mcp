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

# Add Anthropic SDK import
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

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
        
        
        # NO Anthropic API client - Claude subscription only via Claude Code
        # This ensures we never use API tokens, only Claude subscription
        self.anthropic_client = None
        logger.info("Anthropic API disabled - using Claude subscription via Claude Code only")
    
    def _find_claude_cli(self) -> str:
        """Find the Claude CLI executable path using claude-code-mcp approach."""
        logger.debug('[Debug] Attempting to find Claude CLI...')
        
        # Check for custom CLI name from environment variable (claude-code-mcp pattern)
        custom_cli_name = os.environ.get('CLAUDE_CLI_NAME')
        if custom_cli_name:
            logger.debug(f'[Debug] Using custom Claude CLI name from CLAUDE_CLI_NAME: {custom_cli_name}')
            
            # If it's an absolute path, use it directly
            if os.path.isabs(custom_cli_name):
                logger.debug(f'[Debug] CLAUDE_CLI_NAME is an absolute path: {custom_cli_name}')
                return custom_cli_name
            
            # If it contains path separators (relative path), reject it
            if '/' in custom_cli_name or '\\' in custom_cli_name:
                raise ValueError(
                    f"Invalid CLAUDE_CLI_NAME: Relative paths are not allowed. "
                    f"Use either a simple name (e.g., 'claude') or an absolute path"
                )
        
        cli_name = custom_cli_name or 'claude'
        
        # Try local install path: ~/.claude/local/claude (claude-code-mcp pattern)
        user_path = os.path.expanduser('~/.claude/local/claude')
        logger.debug(f'[Debug] Checking for Claude CLI at local user path: {user_path}')
        
        if os.path.exists(user_path):
            logger.debug(f'[Debug] Found Claude CLI at local user path: {user_path}')
            return user_path
        else:
            logger.debug(f'[Debug] Claude CLI not found at local user path: {user_path}')
        
        # Fallback to CLI name (PATH lookup)
        logger.debug(f'[Debug] Falling back to "{cli_name}" command name, relying on PATH lookup')
        logger.warning(f'[Warning] Claude CLI not found at ~/.claude/local/claude. Falling back to "{cli_name}" in PATH')
        return cli_name
    
    def _get_system_prompt(self, task_type: str) -> str:
        """
        Get specialized system prompt for task type.
        
        Args:
            task_type: Type of analysis task
            
        Returns:
            System prompt for the specific task
        """
        return self.SYSTEM_PROMPTS.get(task_type, self.SYSTEM_PROMPTS["general"])
    
    def _get_claude_args(self, prompt: str, task_type: str) -> List[str]:
        """
        Build Claude CLI arguments using claude-code-mcp approach.
        
        Args:
            prompt: The prompt to send to Claude
            task_type: Type of task for specialized handling
            
        Returns:
            List of command line arguments
        """
        # Use the same pattern as claude-code-mcp: --dangerously-skip-permissions -p prompt
        args = ['--dangerously-skip-permissions', '-p', prompt]
        
        # Add system prompt if we have specialized task types
        system_prompt = self._get_system_prompt(task_type)
        if task_type != "general" and system_prompt != self.SYSTEM_PROMPTS["general"]:
            # Add system prompt as additional context in the prompt itself
            enhanced_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            args = ['--dangerously-skip-permissions', '-p', enhanced_prompt]
        
        logger.debug(f'[Debug] Claude CLI args: {args}')
        return args
    
    async def execute_anthropic_sdk(
        self,
        prompt: str,
        task_type: str = "general"
    ) -> ClaudeCliResult:
        """
        Execute using Anthropic SDK directly (preferred method to avoid CLI recursion).
        
        Args:
            prompt: The prompt to send to Claude
            task_type: Type of task for specialized handling
            
        Returns:
            ClaudeCliResult with execution details
        """
        start_time = time.time()
        logger.info(f"Executing via Anthropic SDK for task: {task_type}")
        
        if not self.anthropic_client:
            return ClaudeCliResult(
                success=False,
                error="Anthropic SDK not available or not configured",
                exit_code=-1,
                execution_time=time.time() - start_time,
                command_used="anthropic_sdk",
                task_type=task_type
            )
        
        try:
            # Get system prompt for task type
            system_prompt = self._get_system_prompt(task_type)
            
            # Make API call
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            execution_time = time.time() - start_time
            
            # Extract response content
            response_text = ""
            if response.content and len(response.content) > 0:
                response_text = response.content[0].text
            
            # Calculate cost (approximate)
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            cost_usd = self._calculate_cost(input_tokens, output_tokens)
            
            logger.info(f"Anthropic SDK completed successfully in {execution_time:.2f}s")
            
            return ClaudeCliResult(
                success=True,
                output=response_text,
                error=None,
                exit_code=0,
                execution_time=execution_time,
                command_used="anthropic_sdk",
                task_type=task_type,
                cost_usd=cost_usd,
                duration_ms=execution_time * 1000,
                session_id=response.id if hasattr(response, 'id') else None,
                num_turns=1,
                sdk_metadata={
                    "model": "claude-3-5-sonnet-20241022",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error with Anthropic SDK: {e}")
            
            return ClaudeCliResult(
                success=False,
                error=f"Anthropic SDK error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                command_used="anthropic_sdk",
                task_type=task_type
            )
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate approximate cost in USD for Claude 3.5 Sonnet."""
        # Claude 3.5 Sonnet pricing (as of 2024)
        input_cost_per_1k = 0.003  # $3 per 1M tokens
        output_cost_per_1k = 0.015  # $15 per 1M tokens
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return round(input_cost + output_cost, 6)
    
    def execute_claude_cli_direct(
        self,
        prompt: str,
        task_type: str = "general"
    ) -> ClaudeCliResult:
        """
        Execute Claude CLI directly using claude-code-mcp approach (preferred method).
        
        Args:
            prompt: The prompt to send to Claude CLI
            task_type: Type of task for specialized handling
            
        Returns:
            ClaudeCliResult with execution details
        """
        start_time = time.time()
        logger.info(f"Executing Claude CLI directly for task: {task_type}")
        
        try:
            # Build command using claude-code-mcp pattern
            claude_args = self._get_claude_args(prompt, task_type)
            
            logger.debug(f'[Debug] Invoking Claude CLI: {self.claude_cli_path} {" ".join(claude_args)}')
            
            # Create clean environment to avoid MCP recursion detection
            clean_env = dict(os.environ)
            # Remove MCP and Claude Code specific environment variables
            for var in ["MCP_SERVER", "CLAUDE_CODE_MODE", "CLAUDE_CLI_SESSION", "CLAUDECODE", 
                       "MCP_CLAUDE_DEBUG", "ANTHROPIC_MCP_SERVERS"]:
                clean_env.pop(var, None)
            
            # Use regular subprocess (like claude-code-mcp) instead of asyncio
            command = [self.claude_cli_path] + claude_args
            logger.debug(f'[Debug] Running command: {" ".join(command)}')
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=os.getcwd(),
                env=clean_env
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                output = result.stdout
                logger.info(f"Claude CLI completed successfully in {execution_time:.2f}s")
                logger.debug(f'[Debug] Claude CLI stdout: {output.strip()}')
                
                if result.stderr:
                    logger.debug(f'[Debug] Claude CLI stderr: {result.stderr.strip()}')
                
                return ClaudeCliResult(
                    success=True,
                    output=output,
                    error=None,
                    exit_code=0,
                    execution_time=execution_time,
                    command_used="claude_cli_direct",
                    task_type=task_type,
                    sdk_metadata={
                        "isolation_method": "claude_cli_direct",
                        "args_used": claude_args
                    }
                )
            else:
                # Handle error response
                error_msg = result.stderr.strip() if result.stderr else "Claude CLI failed"
                output = result.stdout.strip() if result.stdout else ""
                
                logger.error(f"Claude CLI failed. Exit code: {result.returncode}. Stderr: {error_msg}")
                
                return ClaudeCliResult(
                    success=False,
                    output=output,
                    error=error_msg,
                    exit_code=result.returncode,
                    execution_time=execution_time,
                    command_used="claude_cli_direct",
                    task_type=task_type
                )
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.warning(f"Claude CLI timed out after {self.timeout_seconds}s (subprocess timeout)")
            
            return ClaudeCliResult(
                success=False,
                error=f"Claude CLI timeout after {self.timeout_seconds} seconds",
                exit_code=124,
                execution_time=execution_time,
                command_used="claude_cli_direct",
                task_type=task_type
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing Claude CLI: {e}")
            
            return ClaudeCliResult(
                success=False,
                error=f"Claude CLI execution error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                command_used="claude_cli_direct",
                task_type=task_type
            )
    
    async def analyze_content(
        self,
        content: str,
        task_type: str = "general",
        additional_context: Optional[str] = None,
        prefer_claude_cli: bool = True
    ) -> ClaudeCliResult:
        """
        Analyze content using Claude CLI direct (preferred) or Anthropic SDK (fallback).
        
        Args:
            content: Content to analyze
            task_type: Type of analysis (pr_review, code_analysis, etc.)
            additional_context: Optional additional context
            prefer_claude_cli: Whether to prefer Claude CLI direct execution (default: True)
            
        Returns:
            ClaudeCliResult with analysis
        """
        # Build prompt with context and content
        prompt_parts = []
        
        if additional_context:
            prompt_parts.append(f"Context: {additional_context}")
        
        prompt_parts.append(f"Content to analyze:\n{content}")
        
        prompt = "\n\n".join(prompt_parts)
        
        # ONLY use Claude CLI direct execution - NO API fallback
        # This ensures we use Claude subscription via Claude Code, not API tokens
        logger.info("Using Claude CLI direct execution (subscription-based, no API)")
        result = self.execute_claude_cli_direct(
            prompt=prompt,
            task_type=task_type
        )
        
        # Return result (success or failure) - no API fallback
        if not result.success:
            logger.error(f"Claude CLI execution failed: {result.error}")
            logger.error("NO API FALLBACK - Fix Claude Code integration or check subscription")
        
        return result


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
    parser.add_argument(
        "--mcp-config",
        help="Path to MCP configuration file"
    )
    parser.add_argument(
        "--permission-prompt-tool",
        help="Name of the permission tool for auto-approval"
    )
    parser.add_argument(
        "--allowedTools",
        help="Comma-separated list of allowed tools (or '*' for all)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not args.prompt and not args.input_file:
        parser.error("Either --prompt or --input-file must be specified")
    
    # Initialize executor
    executor = ExternalClaudeCli(timeout_seconds=args.timeout)
    
    # Build additional arguments for Claude CLI
    additional_args = []
    if args.mcp_config:
        additional_args.extend(["--mcp-config", args.mcp_config])
    
    if args.permission_prompt_tool:
        additional_args.extend(["--permission-prompt-tool", args.permission_prompt_tool])

    if args.allowedTools:
        additional_args.extend(["--allowedTools", args.allowedTools])
    
    # Execute based on input type
    if args.input_file:
        # Read file and analyze
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            result = await executor.analyze_content(
                content=content,
                task_type=args.task_type,
                additional_context=f"File: {args.input_file}",
                prefer_claude_cli=True  # Prefer Claude CLI direct execution
            )
        except Exception as e:
            result = ClaudeCliResult(
                success=False,
                error=f"Error reading file {args.input_file}: {str(e)}",
                exit_code=1,
                task_type=args.task_type
            )
    else:
        result = await executor.analyze_content(
            content=args.prompt,
            task_type=args.task_type,
            prefer_claude_cli=True  # Prefer Claude CLI direct execution
        )
    
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