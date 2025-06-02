"""
LLM-powered analysis tools.

This module provides comprehensive LLM-powered analysis capabilities using Claude CLI
for anti-pattern detection, code review, and engineering guidance.
"""

from .tool_registry import register_llm_analysis_tools
from .llm_models import (
    ExternalClaudeRequest,
    ExternalClaudeResponse,
    PullRequestAnalysisRequest,
    CodeAnalysisRequest
)

__all__ = [
    "register_llm_analysis_tools",
    "ExternalClaudeRequest", 
    "ExternalClaudeResponse",
    "PullRequestAnalysisRequest",
    "CodeAnalysisRequest"
]