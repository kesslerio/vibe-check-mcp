"""
Claude Integration

Handles external Claude CLI integration for PR analysis.
This module extracts Claude CLI functionality from the monolithic PRReviewTool.
"""

import asyncio
import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..shared.claude_integration import analyze_content_async, ClaudeCliExecutor, ClaudeCliResult
from ...utils.token_utils import get_token_counter, analyze_content_size

logger = logging.getLogger(__name__)


class ClaudeIntegration:
    """
    Manages external Claude CLI integration for PR analysis.
    
    Responsibilities:
    - Check Claude CLI availability
    - Execute Claude analysis with adaptive sizing
    - Handle timeout and content size limits
    - Parse Claude output into structured format
    - Save debug information and metadata
    """
    
    # Token-based limits for MCP protocol
    MAX_TOKEN_LIMIT = 25000  # MCP token limit
    FILE_MODE_THRESHOLD = 20000  # Switch to file mode early
    CHUNKED_MODE_THRESHOLD = 50000  # Use chunking for very large content
    
    # Legacy character limit for backward compatibility
    MAX_PROMPT_SIZE = 50000  # 50k character threshold (deprecated)
    
    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize Claude integration.
        
        Args:
            timeout_seconds: Default timeout for Claude CLI operations
        """
        self.external_claude = ClaudeCliExecutor(timeout_seconds=timeout_seconds)
        self.logger = logger
        self.model = None  # Will be set per analysis
        self.token_counter = get_token_counter()  # Initialize token counter
    
    def check_claude_availability(self) -> bool:
        """
        Check if external Claude CLI integration is available.
        
        Returns:
            True if Claude CLI is available and functional
        """
        self.logger.info("🔍 Checking external Claude CLI integration availability...")
        
        try:
            # Check environment for Docker
            docker_env_exists = os.path.exists("/.dockerenv")
            docker_env_var = os.environ.get("RUNNING_IN_DOCKER")
            
            if docker_env_exists or docker_env_var:
                self.logger.info("🐳 Running in Docker container - external Claude CLI not available, using fallback analysis")
                return False
            
            # Use our external Claude CLI integration to check availability
            claude_path = self.external_claude._find_claude_cli()
            
            if claude_path and claude_path != "claude":
                self.logger.info(f"✅ External Claude CLI integration available at {claude_path}")
                return True
            elif claude_path == "claude":
                # Test if default claude command works
                try:
                    result = subprocess.run(
                        ["claude", "--version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0:
                        self.logger.info("✅ External Claude CLI integration available (default claude command)")
                        return True
                except Exception:
                    pass
            
            self.logger.warning("⚠️ External Claude CLI integration not available - will use fallback analysis")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Claude CLI check failed with exception: {e}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False
    
    async def _execute_with_model(
        self,
        prompt: str,
        task_type: str = "pr_review",
        model: str = "sonnet"
    ) -> Any:
        """
        Execute Claude CLI with specific model support using secure subprocess execution.
        
        Args:
            prompt: The prompt to send to Claude
            task_type: Type of task for specialized handling
            model: Claude model to use
            
        Returns:
            ClaudeCliResult with execution details
        """
        self.logger.info(f"🔍 Running Claude analysis with model: {model}")
        start_time = time.time()
        
        # Build command arguments securely - no shell execution needed
        command_args = [
            self.external_claude.claude_cli_path,
            "--model", model,
            "-p", prompt
        ]
        
        try:
            # Execute Claude CLI directly with argument list (no shell)
            process = await asyncio.create_subprocess_exec(
                *command_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.expanduser("~")
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.external_claude.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ClaudeCliResult(
                    success=False,
                    error=f"Claude CLI timed out after {self.external_claude.timeout_seconds} seconds",
                    exit_code=-1,
                    execution_time=time.time() - start_time,
                    command_used=f"claude --model {model} -p [PROMPT]",
                    task_type=task_type
                )
            
            success = process.returncode == 0
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            error = stderr.decode('utf-8', errors='replace') if stderr else ""
            execution_time = time.time() - start_time
            
            return ClaudeCliResult(
                success=success,
                output=output,
                error=error,
                exit_code=process.returncode,
                execution_time=execution_time,
                command_used=f"claude --model {model} -p [PROMPT]",
                task_type=task_type
            )
            
        except Exception as e:
            self.logger.error(f"❌ Claude CLI execution failed: {e}")
            return ClaudeCliResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                exit_code=-1,
                execution_time=time.time() - start_time,
                command_used=f"claude --model {model} -p [PROMPT]",
                task_type=task_type
            )
    
    async def analyze_with_file_mode(
        self, 
        content: str, 
        context: str = "",
        model: str = "sonnet"
    ) -> Optional[ClaudeCliResult]:
        """
        Execute analysis using temporary files for large content.
        
        Args:
            content: Large content to analyze
            context: Additional context for analysis
            model: Claude model to use
            
        Returns:
            ClaudeCliResult with analysis or None if failed
        """
        self.logger.info("🗂️ Using file-based analysis for large content")
        
        try:
            # Create temporary file with the content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            # Build command arguments using file input
            command_args = [
                self.external_claude.claude_cli_path,
                "--model", model,
                "--file", temp_path
            ]
            
            # Add context as additional prompt if provided
            if context:
                command_args.extend(["-p", context])
            
            try:
                # Execute Claude CLI with file input
                process = await asyncio.create_subprocess_exec(
                    *command_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.path.expanduser("~")
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.external_claude.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return ClaudeCliResult(
                        success=False,
                        error=f"File-based analysis timed out after {self.external_claude.timeout_seconds} seconds",
                        exit_code=-1,
                        execution_time=0,
                        command_used=f"claude --model {model} --file [TEMP_FILE]",
                        task_type="pr_review_file_mode"
                    )
                
                success = process.returncode == 0
                output = stdout.decode('utf-8', errors='replace') if stdout else ""
                error = stderr.decode('utf-8', errors='replace') if stderr else ""
                
                self.logger.info(f"🗂️ File-based analysis completed: {'success' if success else 'failed'}")
                
                return ClaudeCliResult(
                    success=success,
                    output=output,
                    error=error,
                    exit_code=process.returncode,
                    execution_time=0,  # Not tracking execution time for file mode
                    command_used=f"claude --model {model} --file [TEMP_FILE]",
                    task_type="pr_review_file_mode"
                )
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to clean up temp file {temp_path}: {cleanup_error}")
                    
        except Exception as e:
            self.logger.error(f"❌ File-based analysis failed: {e}")
            return ClaudeCliResult(
                success=False,
                error=f"File-based analysis error: {str(e)}",
                exit_code=-1,
                execution_time=0,
                command_used="file_mode_error",
                task_type="pr_review_file_mode"
            )
    
    async def run_claude_analysis(
        self, 
        prompt_content: str, 
        data_content: str, 
        pr_number: int,
        pr_data: Dict[str, Any],
        summary_content_generator = None,
        model: str = "sonnet"
    ) -> Optional[Dict[str, Any]]:
        """
        Run Claude analysis using external Claude CLI with adaptive prompt sizing.
        
        Args:
            prompt_content: Main analysis prompt
            data_content: PR data content
            pr_number: PR number for logging
            pr_data: Full PR data for summary generation
            summary_content_generator: Function to generate summary content for large PRs
            model: Claude model to use - "sonnet" (default), "opus", or "haiku"
            
        Returns:
            Structured analysis results or None if failed
        """
        self.logger.info(f"🔍 Starting external Claude analysis for PR #{pr_number}")
        self.logger.info(f"🔍 Prompt content size: {len(prompt_content)} chars")
        self.logger.info(f"🔍 Data content size: {len(data_content)} chars")
        
        try:
            # Create initial combined content for size check
            combined_content = f"{prompt_content}\n\n{data_content}"
            combined_size = len(combined_content)
            
            # TOKEN-AWARE ANALYSIS: Check token count and determine mode
            token_analysis = analyze_content_size(combined_content, f"PR #{pr_number}")
            token_count = token_analysis["token_count"]
            analysis_mode = token_analysis["analysis_mode"]
            
            self.logger.info(f"🔍 Combined content: {combined_size} chars, {token_count} tokens")
            self.logger.info(f"🔄 Analysis mode: {analysis_mode}")
            
            # INTELLIGENT MODE SELECTION based on token count
            if analysis_mode == "file_based":
                self.logger.info(f"🗂️ Large content detected ({token_count} tokens > {self.FILE_MODE_THRESHOLD}) - using file-based analysis")
                
                # Try file-based analysis first
                file_result = await self.analyze_with_file_mode(
                    content=combined_content,
                    context=f"Analyze this Pull Request #{pr_number}",
                    model=model
                )
                
                if file_result and file_result.success:
                    self.logger.info("✅ File-based analysis completed successfully")
                    # Parse and return the result similar to standard mode
                    parsed_result = self._parse_claude_output(file_result.output, pr_number)
                    if parsed_result:
                        parsed_result["analysis_method"] = "file_based"
                        parsed_result["token_count"] = token_count
                        parsed_result["analysis_mode"] = analysis_mode
                        return parsed_result
                else:
                    self.logger.warning("⚠️ File-based analysis failed, falling back to content reduction")
            
            elif analysis_mode == "chunked":
                self.logger.warning(f"🧩 Very large content detected ({token_count} tokens > {self.CHUNKED_MODE_THRESHOLD})")
                self.logger.info("🔀 This content should use chunked analysis - please use ChunkedAnalyzer instead")
                # For now, fall back to summary mode
                analysis_mode = "file_based"
            
            # LEGACY FALLBACK: Character-based sizing for backward compatibility
            if combined_size > self.MAX_PROMPT_SIZE or analysis_mode in ["file_based", "chunked"]:
                self.logger.warning(f"⚠️ Large prompt detected ({combined_size} chars > {self.MAX_PROMPT_SIZE}) - switching to summary analysis")
                
                if summary_content_generator:
                    # Create reduced data content for large PRs
                    reduced_data_content = summary_content_generator(pr_data, {})
                    combined_content = f"{prompt_content}\n\n{reduced_data_content}"
                    new_size = len(combined_content)
                    
                    self.logger.info(f"🔍 Reduced content size: {new_size} chars (reduction: {combined_size - new_size} chars)")
                    combined_size = new_size
                    
                    # Update the prompt to indicate summary mode
                    prompt_content = prompt_content.replace(
                        "Analyze this pull request comprehensively",
                        "Analyze this pull request using summary mode (large PR detected)"
                    )
                    combined_content = f"{prompt_content}\n\n{reduced_data_content}"
            
            # Set adaptive timeout based on token count and content
            timeout_seconds = self._calculate_adaptive_timeout(combined_content, pr_number)
            
            # Update external Claude CLI timeout dynamically
            self.external_claude.timeout_seconds = timeout_seconds
            
            self.logger.info(f"🔍 Using external Claude CLI integration with {timeout_seconds}s timeout...")
            
            # Use external Claude CLI for PR review analysis with model support
            result = await self._execute_with_model(
                prompt=combined_content,
                task_type="pr_review",
                model=model
            )
            
            # Log execution details
            self.logger.info(f"🔍 External Claude analysis completed in {result.execution_time:.2f}s")
            
            if result.success and result.output:
                output_size = len(result.output)
                self.logger.info(f"🔍 Claude output preview: {result.output[:200]}{'...' if len(result.output) > 200 else ''}")
                
                # Log SDK metadata if available
                if result.cost_usd:
                    self.logger.info(f"💰 Analysis cost: ${result.cost_usd:.4f}")
                if result.session_id:
                    self.logger.info(f"🔗 Session ID: {result.session_id}")
                if result.num_turns:
                    self.logger.info(f"🔄 Number of turns: {result.num_turns}")
                
                # Save debug information
                self._save_debug_information(result, combined_content, pr_number, timeout_seconds)
                
                if output_size < 50:
                    self.logger.warning(f"⚠️ Generated review content seems too short ({output_size} chars)")
                    self.logger.info(f"🔍 Full short output: {result.output}")
                    return None
                    
                self.logger.info(f"✅ External Claude analysis completed successfully ({output_size} chars)")
                
                # Parse Claude output into structured format
                self.logger.info("🔍 Parsing Claude output into structured format...")
                parsed_result = self._parse_claude_output(result.output, pr_number)
                
                # Add SDK metadata to parsed result
                if parsed_result and result.sdk_metadata:
                    parsed_result["sdk_metadata"] = result.sdk_metadata
                    parsed_result["cost_usd"] = result.cost_usd
                    parsed_result["session_id"] = result.session_id
                    parsed_result["execution_time"] = result.execution_time
                    parsed_result["analysis_method"] = "external-claude-cli"
                
                if parsed_result:
                    self.logger.info("✅ Claude output parsed successfully")
                    return parsed_result
                else:
                    self.logger.error("❌ Failed to parse Claude output")
                    return None
                    
            else:
                self.logger.error(f"❌ External Claude analysis failed: {result.error}")
                self.logger.info(f"🔍 Exit code: {result.exit_code}")
                self.logger.info(f"🔍 Execution time: {result.execution_time:.2f}s")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ External Claude analysis failed with exception: {e}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")
            return None
    
    def _calculate_adaptive_timeout(self, content: str, pr_number: int) -> int:
        """
        Calculate adaptive timeout based on token count and content complexity.
        
        Args:
            content: Content to analyze (for token counting)
            pr_number: PR number for logging
            
        Returns:
            Appropriate timeout in seconds
        """
        # Get token count for more accurate timeout calculation
        token_count = self.token_counter.count_tokens(content)
        content_size = len(content)
        
        # Base timeout
        base_timeout = 60
        
        # Token-based timeout calculation (more accurate than character-based)
        # Roughly 1 second per 500 tokens for complex analysis
        token_factor = token_count // 500
        token_timeout = min(token_factor, 400)  # Cap at 6.5 minutes for token processing
        
        # Character-based fallback for backward compatibility
        char_factor = content_size // 2000  # More conservative than before
        char_timeout = min(char_factor, 300)  # Cap at 5 minutes for character processing
        
        # Use the higher of token-based or character-based calculation
        size_timeout = max(token_timeout, char_timeout)
        
        # Add buffer for complex analysis
        buffer_timeout = 60
        
        total_timeout = base_timeout + size_timeout + buffer_timeout
        
        # Ensure reasonable bounds
        final_timeout = max(60, min(total_timeout, 600))  # Between 1-10 minutes
        
        self.logger.info(f"🕐 Calculated adaptive timeout: {final_timeout}s for {content_size} chars, {token_count} tokens")
        
        return final_timeout
    
    def _save_debug_information(self, result, combined_content: str, pr_number: int, timeout_seconds: int):
        """Save debug information to temporary files."""
        try:
            timestamp = int(time.time())
            debug_file = f"/tmp/claude_external_pr_{pr_number}_{timestamp}.log"
            prompt_file = f"/tmp/claude_prompt_pr_{pr_number}_{timestamp}.md"
            
            # Save debug output with SDK metadata
            with open(debug_file, 'w') as f:
                f.write("=== External Claude CLI Analysis Session ===\n")
                f.write(f"Command: {result.command_used}\n")
                f.write(f"Exit code: {result.exit_code}\n")
                f.write(f"Execution time: {result.execution_time:.2f}s\n")
                f.write(f"Cost: ${result.cost_usd or 0:.4f}\n")
                f.write(f"Session ID: {result.session_id or 'N/A'}\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Timeout: {timeout_seconds} seconds\n")
                f.write(f"Prompt file: {prompt_file}\n")
                f.write("\n=== SDK METADATA ===\n")
                f.write(json.dumps(result.sdk_metadata, indent=2))
                f.write("\n\n=== OUTPUT ===\n")
                f.write(result.output)
                if result.error:
                    f.write("\n\n=== ERROR ===\n")
                    f.write(result.error)
            
            # Save the prompt content
            with open(prompt_file, 'w') as f:
                f.write(combined_content)
            
            self.logger.info(f"🔍 External Claude debug output saved to: {debug_file}")
            self.logger.info(f"🔍 Prompt content saved to: {prompt_file}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save debug output: {e}")
    
    def _parse_claude_output(self, claude_output: str, pr_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Parse Claude output into structured analysis format with categorized feedback.
        
        Args:
            claude_output: Raw output from Claude CLI
            pr_number: PR number for context
            
        Returns:
            Structured analysis data following CLAUDE.md categorization
        """
        # Enhanced parsing for categorized feedback
        return {
            "raw_analysis": claude_output,
            "overview": self._extract_section(claude_output, "overview"),
            "strengths": self._extract_section(claude_output, "strengths"),
            
            # Categorized feedback sections
            "categorized_feedback": {
                "critical_issues": self._extract_categorized_section(claude_output, "CRITICAL Issues"),
                "important_suggestions": self._extract_categorized_section(claude_output, "IMPORTANT Suggestions"),
                "nice_to_have": self._extract_categorized_section(claude_output, "NICE-TO-HAVE"),
                "overengineering_concerns": self._extract_categorized_section(claude_output, "OVERENGINEERING Concerns")
            },
            
            # Legacy fields for backward compatibility
            "critical_issues": self._extract_categorized_section(claude_output, "CRITICAL Issues"),
            "suggestions": self._extract_categorized_section(claude_output, "IMPORTANT Suggestions"),
            
            "recommendation": self._extract_recommendation(claude_output),
            "pr_number": pr_number,
            "analysis_timestamp": datetime.now().isoformat(),
            "categorization_format": "CLAUDE.md_v1"
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from Claude output."""
        # Simple extraction - can be enhanced with more sophisticated parsing
        import re
        
        patterns = [
            fr"## .*{section_name}.*\n(.*?)(?=\n##|\Z)",
            fr"# .*{section_name}.*\n(.*?)(?=\n#|\Z)",
            fr"\*\*{section_name}.*?\*\*\n(.*?)(?=\n\*\*|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_categorized_section(self, text: str, category_name: str) -> str:
        """Extract categorized feedback sections with emoji indicators."""
        # Patterns for categorized sections with emojis
        emoji_patterns = {
            "CRITICAL Issues": r"### ⚠️.*?CRITICAL.*?\n(.*?)(?=\n###|\n##|\Z)",
            "IMPORTANT Suggestions": r"### 📋.*?IMPORTANT.*?\n(.*?)(?=\n###|\n##|\Z)",
            "NICE-TO-HAVE": r"### 💡.*?NICE-TO-HAVE.*?\n(.*?)(?=\n###|\n##|\Z)",
            "OVERENGINEERING Concerns": r"### ❌.*?OVERENGINEERING.*?\n(.*?)(?=\n###|\n##|\Z)"
        }
        
        # Try emoji pattern first
        if category_name in emoji_patterns:
            pattern = emoji_patterns[category_name]
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Fallback to simple text pattern
        fallback_patterns = [
            fr"### .*{category_name}.*\n(.*?)(?=\n###|\n##|\Z)",
            fr"## .*{category_name}.*\n(.*?)(?=\n##|\Z)",
            fr"\*\*{category_name}.*?\*\*\n(.*?)(?=\n\*\*|\Z)"
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from Claude output."""
        # Look for recommendation patterns
        recommendation_patterns = [
            r"Recommendation:\s*(APPROVE|REJECT|REQUEST_CHANGES)",
            r"Overall:\s*(APPROVE|REJECT|REQUEST_CHANGES)",
            r"Status:\s*(APPROVE|REJECT|REQUEST_CHANGES)"
        ]
        
        for pattern in recommendation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return "UNKNOWN"