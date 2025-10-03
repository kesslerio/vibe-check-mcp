"""Public exports for server-side MCP tools.

This module serves two purposes:

1. **Tool Registry**: Consolidates references to every FastMCP tool callable so
   tests and diagnostics can introspect available capabilities without importing
   each module individually.

2. **Registration Helpers**: Exposes registration functions that the server uses
   to attach tools to the MCP instance based on environment configuration.

Historically the tooling module exposed a flat namespace that callers could
import from (``from vibe_check.server.tools import register_text_analysis_tools``).
The refactor that introduced the ``tools`` package required this module to surface
both the registry utilities and the registration helpers so the package behaves
like the pre-refactor module again.
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List

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
    analyze_integration_decision_text,
    integration_decision_framework,
    integration_research_with_websearch,
    analyze_integration_patterns,
    quick_tech_scan,
    analyze_integration_effort,
    register_integration_decision_tools,
)
from .mentor.core import register_mentor_tools, vibe_check_mentor
from .productivity import (
    analyze_doom_loops,
    session_health_check,
    productivity_intervention,
    reset_session_tracking,
    register_productivity_tools,
)
from .project_context import (
    detect_project_libraries,
    load_project_context,
    create_vibe_check_directory_structure,
    register_project_for_vibe_check,
    register_project_context_tools,
)
from .system import (
    register_system_tools,
    server_status,
    get_telemetry_summary,
    list_registered_tools,
)
from .text_analysis import (
    analyze_text_nollm,
    demo_analyze_text,
    demo_large_prompt_handling,
    register_text_analysis_tools,
)

# Central registry mapping tool names to their callable implementations
LOCAL_TOOL_REGISTRY: Dict[str, Callable] = {
    "server_status": server_status,
    "get_telemetry_summary": get_telemetry_summary,
    "list_tools": list_registered_tools,
    "analyze_text_nollm": analyze_text_nollm,
    "demo_analyze_text": demo_analyze_text,
    "demo_large_prompt_handling": demo_large_prompt_handling,
    "detect_project_libraries": detect_project_libraries,
    "load_project_context": load_project_context,
    "create_vibe_check_directory_structure": create_vibe_check_directory_structure,
    "register_project_for_vibe_check": register_project_for_vibe_check,
    "analyze_issue_nollm": analyze_issue_nollm,
    "analyze_pr_nollm": analyze_pr_nollm,
    "review_pr_comprehensive": review_pr_comprehensive,
    "check_integration_alternatives": check_integration_alternatives,
    "analyze_integration_decision_text": analyze_integration_decision_text,
    "integration_decision_framework": integration_decision_framework,
    "integration_research_with_websearch": integration_research_with_websearch,
    "analyze_integration_patterns": analyze_integration_patterns,
    "quick_tech_scan": quick_tech_scan,
    "analyze_integration_effort": analyze_integration_effort,
    "analyze_doom_loops": analyze_doom_loops,
    "session_health_check": session_health_check,
    "productivity_intervention": productivity_intervention,
    "reset_session_tracking": reset_session_tracking,
    "vibe_check_mentor": vibe_check_mentor,
}


def iter_local_tools() -> Iterable[Callable]:
    """Yield all server-defined MCP tool callables."""

    return LOCAL_TOOL_REGISTRY.values()


def get_local_tool_registry() -> Dict[str, Callable]:
    """Return a copy of the registry mapping tool names to callables."""

    return dict(LOCAL_TOOL_REGISTRY)


def get_local_tool_names() -> List[str]:
    """Return sorted tool names for diagnostics and testing."""

    return sorted(LOCAL_TOOL_REGISTRY.keys())


__all__ = [
    # Registry utilities (PR #273)
    "LOCAL_TOOL_REGISTRY",
    "iter_local_tools",
    "get_local_tool_registry",
    "get_local_tool_names",
    # Context7 integration (PR #272)
    "Context7Manager",
    "context7_manager",
    "register_context7_tools",
    # Registration helpers
    "register_github_tools",
    "register_integration_decision_tools",
    "register_mentor_tools",
    "register_productivity_tools",
    "register_project_context_tools",
    "register_system_tools",
    "register_text_analysis_tools",
    # Tool callables
    "analyze_issue_nollm",
    "analyze_pr_nollm",
    "review_pr_comprehensive",
    "check_integration_alternatives",
    "analyze_integration_decision_text",
    "integration_decision_framework",
    "integration_research_with_websearch",
    "analyze_integration_patterns",
    "quick_tech_scan",
    "analyze_integration_effort",
    "vibe_check_mentor",
    "analyze_doom_loops",
    "session_health_check",
    "productivity_intervention",
    "reset_session_tracking",
    "detect_project_libraries",
    "load_project_context",
    "create_vibe_check_directory_structure",
    "register_project_for_vibe_check",
    "server_status",
    "get_telemetry_summary",
    "list_registered_tools",
    "analyze_text_nollm",
    "demo_analyze_text",
    "demo_large_prompt_handling",
]
