# Utils module for Vibe Check MCP

# Global config for Claude CLI debug/verbose flags
CLAUDE_CLI_DEBUG = True  # Set to True to enable --debug for Claude CLI
CLAUDE_CLI_VERBOSE = True  # Set to True to enable --verbose for Claude CLI

# Token utilities for MCP limit bypass
from .token_utils import get_token_counter, count_tokens, analyze_content_size

__all__ = [
    "get_token_counter",
    "count_tokens", 
    "analyze_content_size",
    "CLAUDE_CLI_DEBUG",
    "CLAUDE_CLI_VERBOSE"
]