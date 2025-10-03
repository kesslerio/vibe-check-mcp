"""Public exports for server-side MCP tools.

Historically the tooling module exposed a flat namespace that callers could
import from (``from vibe_check.server.tools import register_text_analysis_tools``).
The refactor that introduced the ``tools`` package left this file empty which in
turn caused ``AttributeError`` during star-import validation.  The utilities
below surface the key registration helpers and tool entry-points so the package
behaves like the pre-refactor module again.
"""

from .context7_integration import (
    Context7Manager,
    context7_manager,
    register_context7_tools,
)
from .github_integration import (
    register_github_tools,
    analyze_issue_nollm,
    analyze_pr_nollm,
    review_pr_comprehensive,
)
from .integration_decisions import (
    check_integration_alternatives,
    register_integration_decision_tools,
)
from .mentor.core import register_mentor_tools, vibe_check_mentor
from .productivity import (
    register_productivity_tools,
    reset_session_tracking,
)
from .project_context import (
    register_project_context_tools,
    detect_project_libraries,
    load_project_context,
    create_vibe_check_directory_structure,
    register_project_for_vibe_check,
)
from .system import register_system_tools, server_status, get_telemetry_summary
from .text_analysis import (
    register_text_analysis_tools,
    demo_large_prompt_handling,
)

__all__ = [
    "Context7Manager",
    "context7_manager",
    "register_context7_tools",
    "register_github_tools",
    "analyze_issue_nollm",
    "analyze_pr_nollm",
    "review_pr_comprehensive",
    "check_integration_alternatives",
    "register_integration_decision_tools",
    "register_mentor_tools",
    "vibe_check_mentor",
    "register_productivity_tools",
    "reset_session_tracking",
    "register_project_context_tools",
    "detect_project_libraries",
    "load_project_context",
    "create_vibe_check_directory_structure",
    "register_project_for_vibe_check",
    "register_system_tools",
    "server_status",
    "get_telemetry_summary",
    "register_text_analysis_tools",
    "demo_large_prompt_handling",
]
