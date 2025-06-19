"""
Comprehensive Logging Framework for MCP Tools

Provides dual-channel logging with user-friendly console output and technical file logging.
Matches shell script UX quality with emoji-based progress indicators and clear status updates.

Issue #45 implementation: Bridge the UX gap between excellent shell scripts and silent MCP tools.
"""

import json
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable
import re


def _default_sanitizer(message: str) -> str:
    """Default sanitization for sensitive data patterns"""
    # Pattern for API keys and tokens
    message = re.sub(r'(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[\w\-]{8,}["\']?', 
                     r'\1=***REDACTED***', message, flags=re.IGNORECASE)
    
    # Pattern for GitHub personal access tokens
    message = re.sub(r'ghp_[\w]{36}', 'ghp_***REDACTED***', message)
    
    # Pattern for common secrets in environment variables
    message = re.sub(r'(GITHUB_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY)\s*[:=]\s*["\']?[\w\-]{8,}["\']?',
                     r'\1=***REDACTED***', message, flags=re.IGNORECASE)
    
    return message


class LoggingMode(Enum):
    """Logging output modes for different contexts"""
    CONSOLE = "console"  # User-friendly console output + technical file logging
    FILE_ONLY = "file_only"  # Technical file logging only
    SILENT = "silent"  # Minimal logging for CI/CD contexts
    DEBUG = "debug"  # Verbose console + file logging


@dataclass
class LoggingConfig:
    """Configuration for VibeLogger behavior"""
    console_enabled: bool = True
    emoji_enabled: bool = True  # Disable for environments without emoji support
    progress_tracking: bool = True
    timing_enabled: bool = True
    file_logging: bool = True
    structured_json: bool = False  # For monitoring systems
    mcp_server_mode: bool = field(default_factory=lambda: bool(os.environ.get('MCP_SERVER_MODE')))
    sanitizer: Optional[Callable[[str], str]] = field(default_factory=lambda: _default_sanitizer)
    
    @classmethod
    def from_environment(cls) -> 'LoggingConfig':
        """Create config from environment variables"""
        return cls(
            console_enabled=not bool(os.environ.get('VIBE_LOG_SILENT')),
            emoji_enabled=not bool(os.environ.get('VIBE_LOG_NO_EMOJI')),
            progress_tracking=not bool(os.environ.get('VIBE_LOG_NO_PROGRESS')),
            timing_enabled=not bool(os.environ.get('VIBE_LOG_NO_TIMING')),
            file_logging=not bool(os.environ.get('VIBE_LOG_NO_FILE')),
            structured_json=bool(os.environ.get('VIBE_LOG_JSON')),
            mcp_server_mode=bool(os.environ.get('MCP_SERVER_MODE'))
        )
    
    def validate(self) -> None:
        """Validate configuration settings"""
        if not isinstance(self.console_enabled, bool):
            raise ValueError("console_enabled must be a boolean")
        if not isinstance(self.emoji_enabled, bool):
            raise ValueError("emoji_enabled must be a boolean")
        if not isinstance(self.progress_tracking, bool):
            raise ValueError("progress_tracking must be a boolean")
        if not isinstance(self.timing_enabled, bool):
            raise ValueError("timing_enabled must be a boolean")
        if not isinstance(self.file_logging, bool):
            raise ValueError("file_logging must be a boolean")
        if not isinstance(self.structured_json, bool):
            raise ValueError("structured_json must be a boolean")
        if not isinstance(self.mcp_server_mode, bool):
            raise ValueError("mcp_server_mode must be a boolean")


@dataclass
class OperationContext:
    """Context for multi-step operations"""
    name: str
    total_steps: Optional[int] = None
    current_step: int = 0
    start_time: float = field(default_factory=time.time)
    step_times: List[float] = field(default_factory=list)


class VibeLogger:
    """
    Dual-channel logging with user-friendly progress and technical debugging.
    
    Provides shell-script-quality UX for MCP tools:
    - Rich visual indicators: 🤖📋📊⚠️❌✅
    - Progress tracking: "Starting automated review for PR #123..."
    - Context-rich messages: "📊 Analysis complete: 15 patterns detected"
    - Clear error handling: "❌ GitHub API error: Authentication failed"
    - Status updates: "⚠️ Falling back to offline analysis"
    """
    
    def __init__(
        self, 
        tool_name: str, 
        config: Optional[LoggingConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.tool_name = tool_name
        self.config = config or LoggingConfig.from_environment()
        
        # Validate configuration
        try:
            self.config.validate()
        except ValueError as e:
            # Fall back to safe defaults if config is invalid
            self.config = LoggingConfig()
            
        self.logger = logger or logging.getLogger(f"vibe_check.{tool_name}")
        
        # Operation state
        self.current_operation: Optional[OperationContext] = None
        self.session_start_time = time.time()
        
        # Console output safety for MCP server mode
        self._console_enabled = (
            self.config.console_enabled and 
            not self.config.mcp_server_mode
        )
    
    def progress(self, message: str, emoji: str = "🔄", details: Optional[str] = None) -> None:
        """User-visible progress updates with optional technical details"""
        display_message = f"{emoji} {message}" if self.config.emoji_enabled else f"[PROGRESS] {message}"
        
        if self._console_enabled:
            print(display_message)
        
        # Always log to file with technical details
        technical_msg = f"{message} | {details}" if details else message
        self._technical_log("INFO", f"PROGRESS: {technical_msg}")
    
    def success(self, message: str, details: Optional[str] = None) -> None:
        """Success indicators with optional technical context"""
        emoji = "✅" if self.config.emoji_enabled else "[SUCCESS]"
        display_message = f"{emoji} {message}"
        
        if self._console_enabled:
            print(display_message)
        
        technical_msg = f"SUCCESS: {message} | {details}" if details else f"SUCCESS: {message}"
        self._technical_log("INFO", technical_msg)
    
    def warning(self, message: str, details: Optional[str] = None) -> None:
        """Warning messages with optional technical context"""
        emoji = "⚠️" if self.config.emoji_enabled else "[WARNING]"
        display_message = f"{emoji} {message}"
        
        if self._console_enabled:
            print(display_message)
        
        technical_msg = f"{message} | {details}" if details else message
        self._technical_log("WARNING", technical_msg)
    
    def error(self, message: str, details: Optional[str] = None, exception: Optional[Exception] = None) -> None:
        """Error messages with optional technical details and exception info"""
        emoji = "❌" if self.config.emoji_enabled else "[ERROR]"
        display_message = f"{emoji} {message}"
        
        if self._console_enabled:
            print(display_message)
        
        # Enhanced technical logging for errors
        technical_parts = [message]
        if details:
            technical_parts.append(f"Details: {details}")
        if exception:
            technical_parts.append(f"Exception: {str(exception)}")
        
        technical_msg = " | ".join(technical_parts)
        self._technical_log("ERROR", technical_msg, exc_info=exception is not None)
    
    def step(self, step_name: str, current_step: Optional[int] = None, total_steps: Optional[int] = None) -> None:
        """Progress steps matching shell script style"""
        if self.current_operation and self.config.progress_tracking:
            if current_step is not None:
                self.current_operation.current_step = current_step
            else:
                self.current_operation.current_step += 1
            
            if total_steps is not None:
                self.current_operation.total_steps = total_steps
            
            step_num = self.current_operation.current_step
            total = self.current_operation.total_steps or "?"
            
            emoji = "📋" if self.config.emoji_enabled else "[STEP]"
            display_message = f"{emoji} Step {step_num}/{total}: {step_name}"
            
            if self._console_enabled:
                print(display_message)
            
            # Track step timing
            current_time = time.time()
            self.current_operation.step_times.append(current_time)
            
            self._technical_log("INFO", f"STEP {step_num}/{total}: {step_name}")
        else:
            # Fallback when no operation context
            self.progress(f"Step: {step_name}", "📋")
    
    def info(self, message: str, emoji: str = "💡", details: Optional[str] = None) -> None:
        """Informational messages with custom emoji"""
        display_emoji = emoji if self.config.emoji_enabled else "[INFO]"
        display_message = f"{display_emoji} {message}"
        
        if self._console_enabled:
            print(display_message)
        
        technical_msg = f"{message} | {details}" if details else message
        self._technical_log("INFO", technical_msg)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Debug messages (only in debug mode)"""
        if self.config.structured_json and data:
            debug_msg = f"{message} | Data: {json.dumps(data, default=str)}"
        else:
            debug_msg = message
        
        self._technical_log("DEBUG", debug_msg)
    
    @contextmanager
    def operation(self, operation_name: str, total_steps: Optional[int] = None):
        """Context manager for multi-step operations with timing"""
        self.start_operation(operation_name, total_steps)
        try:
            yield self
        except Exception as e:
            self.error(f"Operation '{operation_name}' failed", exception=e)
            raise
        finally:
            self.complete_operation()
    
    def start_operation(self, operation_name: str, total_steps: Optional[int] = None) -> None:
        """Start a multi-step operation with timing"""
        self.current_operation = OperationContext(
            name=operation_name,
            total_steps=total_steps
        )
        
        emoji = "🚀" if self.config.emoji_enabled else "[START]"
        display_message = f"{emoji} Starting {operation_name}..."
        
        if self._console_enabled:
            print(display_message)
        
        self._technical_log("INFO", f"OPERATION_START: {operation_name}")
    
    def complete_operation(self, success_message: Optional[str] = None) -> None:
        """Complete the current operation with timing summary"""
        if not self.current_operation:
            return
        
        # Protect against clock adjustment vulnerabilities
        try:
            operation_time = max(0, time.time() - self.current_operation.start_time)
        except (TypeError, ValueError):
            operation_time = 0  # Fallback if time calculation fails
        
        if success_message:
            final_message = success_message
        else:
            final_message = f"{self.current_operation.name} complete"
        
        if self.config.timing_enabled:
            final_message += f" ({operation_time:.1f}s)"
        
        self.success(final_message)
        
        # Technical logging with operation summary
        step_count = self.current_operation.current_step
        technical_summary = (
            f"OPERATION_COMPLETE: {self.current_operation.name} | "
            f"Steps: {step_count} | Duration: {operation_time:.2f}s"
        )
        self._technical_log("INFO", technical_summary)
        
        self.current_operation = None
    
    def stats(self, title: str, data: Dict[str, Union[int, float, str]], emoji: str = "📊") -> None:
        """Display statistics in shell script style"""
        display_emoji = emoji if self.config.emoji_enabled else "[STATS]"
        
        # Format stats for console
        stats_parts = []
        for key, value in data.items():
            if isinstance(value, float):
                stats_parts.append(f"{key}: {value:.1f}")
            else:
                stats_parts.append(f"{key}: {value}")
        
        stats_str = ", ".join(stats_parts)
        display_message = f"{display_emoji} {title}: {stats_str}"
        
        if self._console_enabled:
            print(display_message)
        
        # Technical logging with structured data
        if self.config.structured_json:
            technical_data = {"title": title, "stats": data}
            self._technical_log("INFO", f"STATS: {json.dumps(technical_data)}")
        else:
            self._technical_log("INFO", f"STATS: {title} | {stats_str}")
    
    def fallback(self, primary_action: str, fallback_action: str, reason: Optional[str] = None) -> None:
        """Indicate fallback behavior like shell scripts"""
        reason_text = f" - {reason}" if reason else ""
        message = f"{primary_action} not available{reason_text} - using {fallback_action}"
        self.warning(message)
    
    def _technical_log(self, level: str, message: str, exc_info: bool = False) -> None:
        """Bridge to existing logging infrastructure"""
        if not self.config.file_logging:
            return
        
        # Add tool context and session timing - protect against clock adjustment
        try:
            session_time = max(0, time.time() - self.session_start_time)
        except (TypeError, ValueError):
            session_time = 0  # Fallback if time calculation fails
        # Apply sanitization if configured
        sanitized_message = message
        if self.config.sanitizer:
            try:
                sanitized_message = self.config.sanitizer(message)
            except Exception:
                # If sanitization fails, use original message
                sanitized_message = message
        
        context_msg = f"[{self.tool_name}:{session_time:.1f}s] {sanitized_message}"
        
        # Use existing logger infrastructure
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(context_msg, exc_info=exc_info)
        
        # Structured JSON logging for monitoring if enabled
        if self.config.structured_json:
            structured_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tool": self.tool_name,
                "level": level,
                "message": message,
                "session_time": session_time
            }
            
            if self.current_operation:
                structured_data["operation"] = {
                    "name": self.current_operation.name,
                    "step": self.current_operation.current_step,
                    "total_steps": self.current_operation.total_steps
                }
            
            # Could be sent to monitoring system here
            self.logger.info(f"STRUCTURED: {json.dumps(structured_data)}")


# Factory functions for easy integration

def get_vibe_logger(
    tool_name: str, 
    mode: Optional[LoggingMode] = None,
    **config_overrides
) -> VibeLogger:
    """
    Factory function for creating VibeLogger instances.
    
    Args:
        tool_name: Name of the MCP tool (e.g., "issue_analyzer", "pr_review")
        mode: Logging mode override
        **config_overrides: Additional configuration overrides
    
    Returns:
        Configured VibeLogger instance
    
    Example:
        # Standard usage
        vibe_logger = get_vibe_logger("issue_analyzer")
        
        # Silent mode for CI/CD
        vibe_logger = get_vibe_logger("issue_analyzer", LoggingMode.SILENT)
        
        # Custom configuration
        vibe_logger = get_vibe_logger("issue_analyzer", emoji_enabled=False)
    """
    config = LoggingConfig.from_environment()
    
    # Apply mode-specific overrides
    if mode == LoggingMode.FILE_ONLY:
        config.console_enabled = False
    elif mode == LoggingMode.SILENT:
        config.console_enabled = False
        config.file_logging = False
    elif mode == LoggingMode.DEBUG:
        config.structured_json = True
    
    # Apply custom overrides
    for key, value in config_overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return VibeLogger(tool_name, config)


def create_migration_logger(existing_logger: logging.Logger) -> VibeLogger:
    """
    Create VibeLogger that integrates with existing Python logger.
    
    Useful for gradual migration of existing MCP tools.
    
    Args:
        existing_logger: Existing Python logger instance
    
    Returns:
        VibeLogger that forwards to existing logger
    
    Example:
        # Existing code
        logger = logging.getLogger(__name__)
        
        # Migration
        vibe_logger = create_migration_logger(logger)
        vibe_logger.progress("Starting analysis", "🤖")
    """
    tool_name = existing_logger.name.split('.')[-1] if '.' in existing_logger.name else existing_logger.name
    return VibeLogger(tool_name, logger=existing_logger)


# Global configuration
_global_config: Optional[LoggingConfig] = None


def configure_global_logging(config: LoggingConfig) -> None:
    """Configure global logging settings for all VibeLogger instances"""
    global _global_config
    _global_config = config


def get_global_config() -> LoggingConfig:
    """Get global logging configuration"""
    global _global_config
    return _global_config or LoggingConfig.from_environment()


# Example usage patterns for documentation
if __name__ == "__main__":
    # Example 1: Basic usage
    logger = get_vibe_logger("example_tool")
    
    with logger.operation("Example analysis", 3):
        logger.step("Fetching data")
        time.sleep(0.1)  # Simulate work
        
        logger.step("Processing patterns")
        time.sleep(0.1)  # Simulate work
        
        logger.step("Generating report")
        time.sleep(0.1)  # Simulate work
    
    logger.stats("Analysis Results", {
        "patterns_detected": 5,
        "confidence": 0.87,
        "processing_time": 2.3
    })
    
    logger.success("Analysis complete! 🎉")