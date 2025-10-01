import logging
import time
import secrets
from typing import Optional, List, Tuple
from vibe_check.mentor.context_manager import get_context_cache, SecurityValidator

logger = logging.getLogger(__name__)


async def load_workspace_context(
    query: str,
    context: Optional[str],
    session_id: Optional[str],
    file_paths: Optional[List[str]],
    working_directory: Optional[str],
) -> Tuple[str, str, str]:
    """Loads workspace context and returns the full context, session_id, and any warnings."""

    workspace = SecurityValidator.get_workspace_directory()
    workspace_warning = ""
    if not workspace and any(
        indicator in query.lower()
        for indicator in [
            "typescript",
            "eslint",
            "any type",
            "code",
            "file",
            "function",
            "class",
            "variable",
            "import",
        ]
    ):
        logger.warning(
            "⚠️ WORKSPACE not configured - vibe_check_mentor cannot read actual code files"
        )
        logger.warning(
            '   To enable code analysis, configure with: -e WORKSPACE="/path/to/project"'
        )
        logger.warning(
            "   Currently providing generic advice without seeing your actual code"
        )
        workspace_warning = '\n\n⚠️ **Note**: WORKSPACE not configured. To enable code-specific advice, reconfigure with:\n```bash\nclaude mcp add vibe-check-local -e WORKSPACE=\\"\/path\/to\/project" ...\n```'

    # Generate session_id if not provided
    if not session_id:
        session_id = f"mentor-{int(time.time())}-{secrets.token_hex(4)}"

    # Build full context
    full_context = query
    if context:
        full_context = f"{query}\n\nAdditional Context:\n{context}"

    # Handle file paths if provided
    if file_paths and working_directory:
        full_context += f"\n\nWorking Directory: {working_directory}"
        full_context += f"\nFile Paths: {', '.join(file_paths)}"

    # Return the expected tuple
    return full_context, session_id, workspace_warning
