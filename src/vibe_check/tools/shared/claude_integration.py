"""
Claude CLI Integration

Consolidated Claude CLI execution utilities shared across vibe check tools.
Provides consistent Claude CLI execution, timeout handling, and environment isolation.

Model Selection:
- "sonnet" (default): Fast, efficient for routine analysis
- "opus": Advanced reasoning for complex scenarios  
- "haiku": Ultra-fast for simple checks
- Full model names: e.g., "claude-sonnet-4-20250514" for version pinning

Security Features:
- Input validation prevents command injection attacks
- Model parameter validation with helpful error messages
- Environment isolation to prevent recursion issues
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# Valid model configurations
VALID_MODELS = {"sonnet", "opus", "haiku"}
VALID_MODEL_PATTERNS = [
    r"^claude-(sonnet|opus|haiku)-[\d]+-[\d]{8}$",  # claude-sonnet-4-20250514
    r"^claude-[\d][\.\d]*-(sonnet|opus|haiku)$",     # claude-3.5-sonnet
]


def _validate_model(model: str) -> str:
    """
    Validate Claude model parameter to prevent command injection and provide helpful errors.
    
    Args:
        model: Model name to validate
        
    Returns:
        The validated model name
        
    Raises:
        ValueError: If model name is invalid or potentially dangerous
    """
    if not model or not isinstance(model, str):
        raise ValueError("Model must be a non-empty string")
    
    # Check for command injection patterns
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "{", "}", "<", ">"]
    if any(char in model for char in dangerous_chars):
        raise ValueError(f"Invalid model name contains dangerous characters: {model}")
    
    # Allow simple model names
    if model in VALID_MODELS:
        return model
    
    # Allow full model names that match expected patterns
    for pattern in VALID_MODEL_PATTERNS:
        if re.match(pattern, model):
            return model
    
    # Log warning for unknown models but allow them (Claude CLI will validate)
    logger.warning(f"Unknown model '{model}', will be validated by Claude CLI")
    return model


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


class ClaudeCliExecutor:
    """Shared Claude CLI executor with isolation and specialized prompts."""
    
    # System prompts for specialized task types
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
        Initialize Claude CLI executor.
        
        Args:
            timeout_seconds: Maximum time to wait for Claude CLI response
        """
        self.timeout_seconds = timeout_seconds
        self.claude_cli_path = self._find_claude_cli()
    
    def _find_claude_cli(self) -> str:
        """Find the Claude CLI executable path using claude-code-mcp approach."""
        logger.debug('[Debug] Attempting to find Claude CLI...')
        
        # Check for custom CLI name from environment variable
        custom_cli_name = os.environ.get('CLAUDE_CLI_NAME')
        if custom_cli_name:
            logger.debug(f'[Debug] Using custom Claude CLI name from CLAUDE_CLI_NAME: {custom_cli_name}')
            
            # If it's an absolute path, use it directly
            if os.path.isabs(custom_cli_name):
                logger.debug(f'[Debug] CLAUDE_CLI_NAME is an absolute path: {custom_cli_name}')
                return custom_cli_name
            
            # If it contains path separators (relative path), reject it
            if '/' in custom_cli_name or '\\\\' in custom_cli_name:
                raise ValueError(
                    f"Invalid CLAUDE_CLI_NAME: Relative paths are not allowed. "
                    f"Use either a simple name (e.g., 'claude') or an absolute path"
                )
        
        cli_name = custom_cli_name or 'claude'
        
        # Try local install path: ~/.claude/local/claude
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
    
    def _get_claude_md_content(self) -> str:
        """
        Read CLAUDE.md content from the project directory.
        
        Since Claude CLI runs from home directory to avoid recursion,
        we must explicitly read and include CLAUDE.md instructions.
        
        Returns:
            CLAUDE.md content or empty string if not found
        """
        try:
            # Find project root by walking up from current file location
            current_file = os.path.abspath(__file__)
            # Navigate up: shared -> tools -> vibe_check -> src -> project_root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
            claude_md_path = os.path.join(project_root, "CLAUDE.md")
            
            if os.path.exists(claude_md_path):
                with open(claude_md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.debug(f"Successfully read CLAUDE.md from {claude_md_path}")
                return content
            else:
                logger.warning(f"CLAUDE.md not found at {claude_md_path}")
                return ""
        except Exception as e:
            logger.error(f"Error reading CLAUDE.md: {e}")
            return ""
    
    def _get_system_prompt(self, task_type: str) -> str:
        """
        Get specialized system prompt for task type, enhanced with CLAUDE.md instructions.
        
        Args:
            task_type: Type of analysis task
            
        Returns:
            System prompt for the specific task, including CLAUDE.md content
        """
        base_prompt = self.SYSTEM_PROMPTS.get(task_type, self.SYSTEM_PROMPTS["general"])
        
        # Add CLAUDE.md instructions for comprehensive guidance
        claude_md_content = self._get_claude_md_content()
        if claude_md_content:
            enhanced_prompt = f"""{base_prompt}

## Project Engineering Guidelines (CLAUDE.md)

You must follow these project-specific engineering guidelines:

{claude_md_content}

Please apply these guidelines throughout your analysis and recommendations."""
            return enhanced_prompt
        else:
            return base_prompt
    
    def _get_mcp_config_path(self) -> str:
        """
        Get path to MCP config file that excludes vibe-check server.
        
        This prevents recursive MCP calls that cause infinite loops and hanging.
        Uses the project's standard MCP config with safe external servers only.
        Returns path to MCP config file.
        """
        # Use project's MCP config file in project root
        # __file__ is: /path/to/src/vibe_check/tools/shared/claude_integration.py
        # We need to go up 4 levels to reach project root
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
        config_path = os.path.join(project_root, "mcp-config.json")
        
        if os.path.exists(config_path):
            logger.debug(f"Using MCP config at: {config_path}")
            return config_path
        else:
            logger.warning(f"MCP config not found at: {config_path}")
            return ""
    
    def _get_claude_args(self, prompt: str, task_type: str, model: str = "sonnet") -> List[str]:
        """
        Build Claude CLI arguments following SDK best practices.
        
        Args:
            prompt: The prompt to send to Claude
            task_type: Type of task for specialized handling
            model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
            
        Returns:
            List of command line arguments
        """
        # Enhanced task configuration with comprehensive tool allowlists
        # NO MAX TURNS LIMIT - Let Claude analyze as thoroughly as needed
        if task_type == "general":
            max_turns = None  # No limit
            allowed_tools = "Read,Write"
            
        elif task_type == "issue_analysis":
            max_turns = None  # No limit
            allowed_tools = ",".join([
                # Basic file operations
                "Read", "Write",
                # Git operations
                "Bash(git:*)",
                # GitHub issue tools
                "mcp__github__get_issue",
                "mcp__github__get_issue_comments", 
                "mcp__github__add_issue_comment",
                "mcp__github__list_issues",
                "mcp__github__search_issues",
                "mcp__github__update_issue",
                # Clear thought analysis tools
                "mcp__clear-thought-server__sequentialthinking",
                "mcp__clear-thought-server__mentalmodel",
                "mcp__clear-thought-server__designpattern",
                "mcp__clear-thought-server__debuggingapproach",
                # Research tools
                "mcp__brave-search__brave_web_search",
                "mcp__tavily-mcp__tavily-search"
            ])
            
        elif task_type == "pr_review":
            max_turns = None  # No limit
            allowed_tools = ",".join([
                # Basic file and code operations
                "Read", "Write", "Grep", "Glob",
                # Git operations  
                "Bash(git:*)",
                # GitHub PR tools
                "mcp__github__get_pull_request",
                "mcp__github__get_pull_request_diff",
                "mcp__github__get_pull_request_files",
                "mcp__github__get_pull_request_comments",
                "mcp__github__add_pull_request_review_comment_to_pending_review",
                "mcp__github__create_and_submit_pull_request_review",
                "mcp__github__list_pull_requests",
                # Clear thought analysis tools
                "mcp__clear-thought-server__sequentialthinking",
                "mcp__clear-thought-server__mentalmodel",
                "mcp__clear-thought-server__designpattern",
                "mcp__clear-thought-server__programmingparadigm",
                "mcp__clear-thought-server__debuggingapproach",
                # Research and documentation tools
                "mcp__brave-search__brave_web_search",
                "mcp__tavily-mcp__tavily-search"
            ])
            
        elif task_type == "code_analysis":
            max_turns = None  # No limit
            allowed_tools = ",".join([
                "Read", "Grep", "Glob",
                # Clear thought tools for code analysis
                "mcp__clear-thought-server__sequentialthinking",
                "mcp__clear-thought-server__mentalmodel", 
                "mcp__clear-thought-server__designpattern",
                "mcp__clear-thought-server__programmingparadigm",
                "mcp__clear-thought-server__debuggingapproach",
                # Research for best practices
                "mcp__brave-search__brave_web_search",
                "mcp__tavily-mcp__tavily-search"
            ])
            
        elif task_type == "comprehensive_review":  # New task type for thorough analysis
            max_turns = None  # No limit
            allowed_tools = ",".join([
                # All file operations
                "Read", "Write", "Grep", "Glob",
                # Git operations
                "Bash(git:*)",
                # Complete GitHub toolset
                "mcp__github__get_issue",
                "mcp__github__get_issue_comments",
                "mcp__github__add_issue_comment",
                "mcp__github__get_pull_request",
                "mcp__github__get_pull_request_diff", 
                "mcp__github__get_pull_request_files",
                "mcp__github__create_and_submit_pull_request_review",
                "mcp__github__search_code",
                "mcp__github__search_issues",
                # Full clear thought toolkit
                "mcp__clear-thought-server__sequentialthinking",
                "mcp__clear-thought-server__mentalmodel",
                "mcp__clear-thought-server__designpattern",
                "mcp__clear-thought-server__programmingparadigm",
                "mcp__clear-thought-server__debuggingapproach",
                "mcp__clear-thought-server__collaborativereasoning",
                "mcp__clear-thought-server__decisionframework",
                "mcp__clear-thought-server__scientificmethod",
                "mcp__clear-thought-server__structuredargumentation",
                # Research capabilities
                "mcp__brave-search__brave_web_search",
                "mcp__tavily-mcp__tavily-search",
                "mcp__tavily-mcp__tavily-extract"
            ])
        else:
            max_turns = None  # No limit
            allowed_tools = "Read,Write"  # Basic operations
        
        # Start with base args following SDK best practices
        # Use explicit tool allowlists for security instead of --dangerously-skip-permissions
        args = [
            # NOTE: Removed --output-format json and --verbose to get clean text output
            # The JSON format was returning session metadata instead of analysis content
        ]
        
        # Add model parameter for Claude model selection (with validation)
        validated_model = _validate_model(model)
        args.extend(['--model', validated_model])
        
        # Add max turns only if specified (None = no limit)
        if max_turns is not None:
            args.extend(['--max-turns', str(max_turns)])
        # If max_turns is None, don't add the flag at all - Claude CLI will run unlimited
        
        # CRITICAL: Prevent recursive MCP calls by using empty MCP config
        # This prevents infinite loops and hanging (Issue #94)
        mcp_config_path = self._get_mcp_config_path()
        if mcp_config_path:  # Only add if config file exists
            args.extend(['--mcp-config', mcp_config_path])
        
        # Add explicit tool permissions for security (Issue #90 compliance)
        # This is much safer than --dangerously-skip-permissions
        args.extend(['--allowedTools', allowed_tools])
        
        # Add print flag and prompt (prompt must be last)
        args.append('-p')
        
        # Add system prompt if we have specialized task types
        system_prompt = self._get_system_prompt(task_type)
        if task_type != "general" and system_prompt != self.SYSTEM_PROMPTS["general"]:
            # Add system prompt as additional context in the prompt itself
            enhanced_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            args.append(enhanced_prompt)
        else:
            args.append(prompt)
        
        logger.debug(f'[Debug] Claude CLI args: {args}')
        return args
    
    def _is_running_in_mcp_context(self) -> bool:
        """
        Detect if we're currently running within a Claude CLI MCP context that would cause recursion.
        
        This specifically prevents recursive Claude CLI calls when Claude CLI has already loaded
        vibe-check as an MCP server and is calling it again.
        
        Returns:
            True if running in recursive Claude CLI context, False for normal MCP usage
        """
        # Check for internal vibe-check call marker (most reliable indicator)
        if os.environ.get("VIBE_CHECK_INTERNAL_CALL") == "true":
            return True
        
        recursion_indicators = []
        
        # Check for Claude CLI specific environment variables that indicate we're inside Claude CLI
        claude_cli_vars = [
            "CLAUDE_CLI_SESSION", "CLAUDE_CLI_MCP_MODE", "ANTHROPIC_CLI_SESSION"
        ]
        for var in claude_cli_vars:
            if os.environ.get(var):
                recursion_indicators.append(f"env:{var}={os.environ.get(var)}")
        
        # REMOVED: stdio check - this is normal for MCP servers and was blocking legitimate usage
        
        # Check for recursive Claude CLI calls specifically
        # Only check parent processes if we have other indicators of Claude CLI recursion
        if recursion_indicators:
            try:
                import psutil
                current_process = psutil.Process()
                parent = current_process.parent()
                if parent:
                    parent_name = parent.name().lower()
                    # Only flag if parent is specifically claude CLI (not Claude Code/Desktop)
                    if parent_name in ["claude", "claude-cli"]:
                        recursion_indicators.append(f"parent:claude_cli={parent_name}")
            except:
                pass
        
        is_recursive_context = len(recursion_indicators) > 0
        
        if is_recursive_context:
            logger.info(f"🔍 Recursive Claude CLI context detected: {recursion_indicators}")
            logger.info("🚫 Preventing recursive Claude CLI calls")
        else:
            logger.debug("✅ No recursive context detected - Claude CLI calls allowed")
        
        return is_recursive_context
    
    def execute_sync(
        self,
        prompt: str,
        task_type: str = "general",
        model: str = "sonnet"
    ) -> ClaudeCliResult:
        """
        Execute Claude CLI synchronously with directory isolation for recursion prevention.
        
        Args:
            prompt: The prompt to send to Claude CLI
            task_type: Type of task for specialized handling
            model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
            
        Returns:
            ClaudeCliResult with execution details
        """
        start_time = time.time()
        
        # NOTE: Recursion prevention now handled by directory isolation
        # Claude CLI runs from home directory which doesn't have vibe-check MCP config
        
        logger.info(f"Executing Claude CLI directly for task: {task_type}")
        
        try:
            # Build command
            claude_args = self._get_claude_args(prompt, task_type, model)
            
            logger.debug(f'[Debug] Invoking Claude CLI: {self.claude_cli_path} {" ".join(claude_args)}')
            
            # Create clean environment for internal Claude CLI calls
            clean_env = dict(os.environ)
            
            # Set a marker to indicate this is an internal vibe-check call
            clean_env["VIBE_CHECK_INTERNAL_CALL"] = "true"
            
            # Remove MCP-related variables that could cause recursion
            mcp_vars_to_remove = [
                "MCP_SERVER", "CLAUDE_CODE_MODE", "CLAUDE_CLI_SESSION", "CLAUDECODE",
                "MCP_CLAUDE_DEBUG", "ANTHROPIC_MCP_SERVERS", "MCP_CONFIG_PATH",
                "CLAUDE_MCP_CONFIG"
            ]
            for var in mcp_vars_to_remove:
                clean_env.pop(var, None)
            
            # Use regular subprocess
            command = [self.claude_cli_path] + claude_args
            logger.debug(f'[Debug] Running command: {" ".join(command)}')
            
            # Use home directory to avoid loading project's MCP config that includes vibe-check
            # This prevents recursion by ensuring Claude CLI doesn't load the vibe-check MCP server
            isolation_dir = os.path.expanduser("~")
            logger.debug(f'[Debug] Running Claude CLI from isolation directory: {isolation_dir}')
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=isolation_dir,
                env=clean_env,
                stdin=subprocess.DEVNULL
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
                
                # Check if error is related to model parameter
                if "model" in error_msg.lower() or "invalid" in error_msg.lower():
                    error_msg = f"Model '{model}' error: {error_msg}"
                
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
    
    async def execute_async(
        self,
        prompt: str,
        task_type: str = "general",
        model: str = "sonnet"
    ) -> ClaudeCliResult:
        """
        Execute Claude CLI asynchronously with directory isolation for recursion prevention.
        
        Args:
            prompt: The prompt to send to Claude CLI
            task_type: Type of task for specialized handling
            model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
            
        Returns:
            ClaudeCliResult with execution details
        """
        start_time = time.time()
        
        # NOTE: Recursion prevention now handled by directory isolation
        # Claude CLI runs from home directory which doesn't have vibe-check MCP config
        
        logger.info(f"Executing Claude CLI async for task: {task_type}")
        
        try:
            # Build command
            claude_args = self._get_claude_args(prompt, task_type, model)
            command = [self.claude_cli_path] + claude_args
            
            logger.debug(f"Executing Claude CLI directly: {' '.join(command)}")
            
            # Use home directory to avoid loading project's MCP config that includes vibe-check
            # This prevents recursion by ensuring Claude CLI doesn't load the vibe-check MCP server
            isolation_dir = os.path.expanduser("~")
            logger.debug(f'[Debug] Running Claude CLI async from isolation directory: {isolation_dir}')
            
            # Execute Claude CLI directly
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=isolation_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds + 10  # Allow extra time for process overhead
            )
            
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                # Claude CLI succeeded
                output_text = stdout.decode('utf-8').strip()
                logger.info(f"Claude CLI completed successfully in {execution_time:.2f}s")
                
                return ClaudeCliResult(
                    success=True,
                    output=output_text,
                    error=None,
                    exit_code=0,
                    execution_time=execution_time,
                    command_used="claude_cli_async",
                    task_type=task_type
                )
            else:
                # Handle error
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                
                # Check if error is related to model parameter
                if "model" in error_msg.lower() or "invalid" in error_msg.lower():
                    error_msg = f"Model '{model}' error: {error_msg}"
                
                logger.error(f"Claude CLI failed: {error_msg}")
                
                return ClaudeCliResult(
                    success=False,
                    error=f"Claude CLI error: {error_msg}",
                    exit_code=process.returncode,
                    execution_time=execution_time,
                    command_used="claude_cli_async",
                    task_type=task_type
                )
                    
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"Claude CLI async timed out after {self.timeout_seconds + 10}s")
            return ClaudeCliResult(
                success=False,
                error=f"Analysis timed out after {self.timeout_seconds + 10} seconds",
                exit_code=-1,
                execution_time=execution_time,
                command_used="claude_cli_async",
                task_type=task_type
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in Claude CLI async execution: {e}")
            return ClaudeCliResult(
                success=False,
                error=f"Integration error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                command_used="claude_cli_async",
                task_type=task_type
            )


# Circuit breaker integration (Phase 2 - Issue #102)
from .circuit_breaker import ClaudeCliCircuitBreaker, CircuitBreakerOpenError, ClaudeCliError
from .retry_logic import get_global_circuit_breaker, claude_cli_with_retry
from .health_monitor import ClaudeCliHealthMonitor

# Global health monitor instance
_global_health_monitor: Optional[ClaudeCliHealthMonitor] = None


def get_global_health_monitor() -> ClaudeCliHealthMonitor:
    """Get or create the global health monitor instance."""
    global _global_health_monitor
    
    if _global_health_monitor is None:
        circuit_breaker = get_global_circuit_breaker()
        _global_health_monitor = ClaudeCliHealthMonitor(circuit_breaker)
        logger.info("Global health monitor created")
    
    return _global_health_monitor


async def analyze_content_async_with_circuit_breaker(
    content: str,
    task_type: str = "general",
    additional_context: Optional[str] = None,
    timeout_seconds: int = 60,
    max_retries: int = 2,
    model: str = "sonnet"
) -> ClaudeCliResult:
    """
    Analyze content using Claude CLI with circuit breaker and retry logic.
    
    This is the enhanced version that implements Phase 2 (Issue #102) with:
    - Circuit breaker pattern for reliability
    - Retry logic with exponential backoff
    - Health monitoring and diagnostics
    - Graceful degradation on failures
    
    Args:
        content: Content to analyze
        task_type: Type of analysis (pr_review, code_analysis, etc.)
        additional_context: Optional additional context
        timeout_seconds: Maximum time to wait for response
        max_retries: Maximum number of retry attempts
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
    Returns:
        ClaudeCliResult with analysis
        
    Raises:
        ClaudeCliError: When analysis fails after all retries
        CircuitBreakerOpenError: When circuit breaker is open
    """
    circuit_breaker = get_global_circuit_breaker()
    health_monitor = get_global_health_monitor()
    
    # Build prompt with context and content
    prompt_parts = []
    
    if additional_context:
        prompt_parts.append(f"Context: {additional_context}")
    
    prompt_parts.append(f"Content to analyze:\n{content}")
    
    prompt = "\n\n".join(prompt_parts)
    
    async def _execute_analysis():
        """Inner function to execute the analysis."""
        executor = ClaudeCliExecutor(timeout_seconds=timeout_seconds)
        return await executor.execute_async(prompt=prompt, task_type=task_type, model=model)
    
    # Record the start time
    start_time = time.time()
    
    try:
        # Execute through circuit breaker with retry logic
        result = await claude_cli_with_retry(
            _execute_analysis,
            circuit_breaker,
            max_retries=max_retries,
            timeout=timeout_seconds
        )
        
        # Record successful call
        duration = time.time() - start_time
        health_monitor.record_call(
            success=result.success,
            duration=duration,
            timeout=False
        )
        
        return result
        
    except CircuitBreakerOpenError as e:
        # Circuit breaker is open - record as rejected call
        duration = time.time() - start_time
        health_monitor.record_call(
            success=False,
            duration=duration,
            error_type="CircuitBreakerOpen",
            error_message=str(e)
        )
        
        # Return a graceful degradation result instead of raising
        return ClaudeCliResult(
            success=False,
            error=str(e),
            exit_code=-2,
            execution_time=duration,
            command_used="circuit_breaker_blocked",
            task_type=task_type,
            sdk_metadata={
                "circuit_breaker_status": "OPEN",
                "graceful_degradation": True,
                "health_status": health_monitor.get_health_status().level
            }
        )
        
    except ClaudeCliError as e:
        # Analysis failed after retries
        duration = time.time() - start_time
        health_monitor.record_call(
            success=False,
            duration=duration,
            error_type="ClaudeCliError",
            error_message=str(e),
            timeout="timeout" in str(e).lower()
        )
        
        # Return error result instead of raising
        return ClaudeCliResult(
            success=False,
            error=str(e),
            exit_code=-1,
            execution_time=duration,
            command_used="circuit_breaker_failed",
            task_type=task_type,
            sdk_metadata={
                "circuit_breaker_status": circuit_breaker.state.value,
                "health_status": health_monitor.get_health_status().level,
                "retries_exhausted": True
            }
        )
        
    except Exception as e:
        # Unexpected error
        duration = time.time() - start_time
        health_monitor.record_call(
            success=False,
            duration=duration,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        
        logger.error(f"Unexpected error in circuit breaker analysis: {e}")
        
        return ClaudeCliResult(
            success=False,
            error=f"Unexpected error: {str(e)}",
            exit_code=-1,
            execution_time=duration,
            command_used="circuit_breaker_error",
            task_type=task_type,
            sdk_metadata={
                "circuit_breaker_status": circuit_breaker.state.value,
                "health_status": health_monitor.get_health_status().level,
                "unexpected_error": True
            }
        )


# Convenience functions for common use cases
async def analyze_content_async(
    content: str,
    task_type: str = "general",
    additional_context: Optional[str] = None,
    timeout_seconds: int = 60,
    model: str = "sonnet"
) -> ClaudeCliResult:
    """
    Analyze content using Claude CLI asynchronously.
    
    This is the legacy function maintained for backward compatibility.
    For new code, consider using analyze_content_async_with_circuit_breaker()
    which provides better reliability through circuit breaker patterns.
    
    Args:
        content: Content to analyze
        task_type: Type of analysis (pr_review, code_analysis, etc.)
        additional_context: Optional additional context
        timeout_seconds: Maximum time to wait for response
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
    Returns:
        ClaudeCliResult with analysis
    """
    # Check if circuit breaker should be used by default
    # For now, use the enhanced version for better reliability
    return await analyze_content_async_with_circuit_breaker(
        content=content,
        task_type=task_type,
        additional_context=additional_context,
        timeout_seconds=timeout_seconds,
        max_retries=2,  # Default retry behavior
        model=model
    )


def analyze_content_sync(
    content: str,
    task_type: str = "general",
    additional_context: Optional[str] = None,
    timeout_seconds: int = 60,
    model: str = "sonnet"
) -> ClaudeCliResult:
    """
    Analyze content using Claude CLI synchronously.
    
    Args:
        content: Content to analyze
        task_type: Type of analysis (pr_review, code_analysis, etc.)
        additional_context: Optional additional context
        timeout_seconds: Maximum time to wait for response
        model: Claude model to use ("sonnet", "opus", "haiku", or full model name)
        
    Returns:
        ClaudeCliResult with analysis
    """
    # Build prompt with context and content
    prompt_parts = []
    
    if additional_context:
        prompt_parts.append(f"Context: {additional_context}")
    
    prompt_parts.append(f"Content to analyze:\n{content}")
    
    prompt = "\n\n".join(prompt_parts)
    
    executor = ClaudeCliExecutor(timeout_seconds=timeout_seconds)
    return executor.execute_sync(prompt=prompt, task_type=task_type, model=model)