"""
Text Analysis using Claude CLI

Core text analysis functionality using external Claude CLI for comprehensive
LLM-powered analysis with full reasoning capabilities.
"""

import asyncio
import logging
import tempfile
import time
from typing import Optional

from vibe_check.tools.shared.claude_integration import analyze_content_async
from .llm_models import ExternalClaudeResponse

logger = logging.getLogger(__name__)


async def analyze_text_llm(
    content: str,
    task_type: str = "general",
    additional_context: Optional[str] = None,
    timeout_seconds: int = 60,
    model: str = "sonnet",
) -> ExternalClaudeResponse:
    """
    Deep text analysis using Claude CLI reasoning.
    Docs: https://github.com/kesslerio/vibe-check-mcp/blob/main/data/tool_descriptions.json
    """
    logger.info(f"Starting external Claude analysis for task type: {task_type}")

    try:
        # Prepare the full content
        if additional_context:
            full_content = f"{additional_context}\n\n{content}"
        else:
            full_content = content

        # Create temporary file for large content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write(full_content)
            temp_file_path = temp_file.name

        try:
            # Use the shared Claude CLI executor to properly handle environment isolation
            result = await analyze_content_async(
                content=full_content,
                task_type=task_type,
                timeout_seconds=timeout_seconds,
                model=model,
            )

            # Convert ClaudeCliResult to ExternalClaudeResponse
            return ExternalClaudeResponse(
                success=result.success,
                output=result.output,
                error=result.error,
                exit_code=result.exit_code or 0,
                execution_time_seconds=result.execution_time,
                task_type=result.task_type,
                timestamp=time.time(),
                command_used=result.command_used,
            )

        finally:
            # Clean up temporary file
            try:
                import os

                os.unlink(temp_file_path)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Error in external Claude analysis: {e}")
        return ExternalClaudeResponse(
            success=False,
            error=f"Integration error: {str(e)}",
            exit_code=-1,
            execution_time_seconds=0.0,
            task_type=task_type,
            timestamp=time.time(),
            command_used="claude_cli_executor",
        )
