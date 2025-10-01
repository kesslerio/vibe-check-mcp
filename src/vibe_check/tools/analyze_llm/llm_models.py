"""
Pydantic models for LLM analysis tools.

Defines request and response models for external Claude CLI integration
and various analysis tool types.
"""

from typing import List, Optional
from pydantic import BaseModel


class ExternalClaudeRequest(BaseModel):
    """Request model for external Claude CLI integration."""

    content: str
    task_type: str = "general"
    additional_context: Optional[str] = None
    timeout_seconds: int = 60


class ExternalClaudeResponse(BaseModel):
    """Response model for external Claude CLI integration."""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_seconds: float
    task_type: str
    timestamp: float
    command_used: str = ""


class PullRequestAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    pr_diff: str
    pr_description: str = ""
    file_changes: Optional[List[str]] = None
    timeout_seconds: int = 90


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""

    code_content: str
    file_path: Optional[str] = None
    language: Optional[str] = None
    timeout_seconds: int = 60
