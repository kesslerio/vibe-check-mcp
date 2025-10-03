#!/usr/bin/env python3
"""Validate import surfaces for the Vibe Check MCP package."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Map of module name to the attributes that should be publicly available.
MODULE_EXPORTS: Dict[str, Tuple[str, ...]] = {
    "vibe_check.server": (
        "run_server",
        "main",
        "app",
        "mcp",
        "FastMCP",
        "get_mcp_instance",
        "register_all_tools",
        "detect_transport_mode",
        "analyze_text_demo",
        "demo_analyze_text",
        "server_status",
        "get_telemetry_summary",
        "check_integration_alternatives",
        "vibe_check_mentor",
        "get_mentor_engine",
    ),
    "vibe_check.server.tools": (
        "register_text_analysis_tools",
        "demo_large_prompt_handling",
        "register_productivity_tools",
        "reset_session_tracking",
        "register_system_tools",
        "server_status",
        "get_telemetry_summary",
        "register_context7_tools",
        "context7_manager",
        "register_github_tools",
        "analyze_issue_nollm",
        "analyze_pr_nollm",
        "review_pr_comprehensive",
        "register_integration_decision_tools",
        "check_integration_alternatives",
        "register_project_context_tools",
        "detect_project_libraries",
        "load_project_context",
        "create_vibe_check_directory_structure",
        "register_project_for_vibe_check",
        "register_mentor_tools",
        "vibe_check_mentor",
    ),
    "vibe_check.server.tools.mentor": (
        "register_mentor_tools",
        "vibe_check_mentor",
        "load_workspace_context",
        "analyze_query_and_context",
        "get_reasoning_engine",
        "generate_response",
    ),
    "vibe_check.mentor": (
        "PersonaData",
        "CollaborativeReasoningSession",
        "ContributionData",
        "DisagreementData",
        "ConfidenceScores",
        "ExperienceStrings",
    ),
    "vibe_check.tools": (
        "analyze_text_demo",
        "demo_analyze_text",
    ),
}


@dataclass
class ModuleReport:
    """Represents the validation result for a single module."""

    name: str
    import_error: str | None
    missing_attributes: List[str]
    missing_in_all: List[str]

    @property
    def ok(self) -> bool:
        return (
            not self.import_error
            and not self.missing_attributes
            and not self.missing_in_all
        )


def validate_module(module_name: str, expected_exports: Iterable[str]) -> ModuleReport:
    """Import a module and confirm the expected exports are present."""

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - defensive guard for CI output
        return ModuleReport(
            name=module_name,
            import_error=str(exc),
            missing_attributes=list(expected_exports),
            missing_in_all=list(expected_exports),
        )

    missing_attributes = [
        attr for attr in expected_exports if not hasattr(module, attr)
    ]

    module_all = getattr(module, "__all__", None)
    if module_all is None:
        missing_in_all = list(expected_exports)
    else:
        exported = set(module_all)
        missing_in_all = [attr for attr in expected_exports if attr not in exported]

    return ModuleReport(
        name=module_name,
        import_error=None,
        missing_attributes=missing_attributes,
        missing_in_all=missing_in_all,
    )


def main() -> int:
    reports = [
        validate_module(module_name, expected)
        for module_name, expected in MODULE_EXPORTS.items()
    ]

    exit_code = 0
    for report in reports:
        if report.ok:
            print(f"✅ {report.name} imports and exports verified")
            continue

        exit_code = 1
        print(f"❌ {report.name} failed validation")
        if report.import_error:
            print(f"   Import error: {report.import_error}")
        if report.missing_attributes:
            print(f"   Missing attributes: {', '.join(report.missing_attributes)}")
        if report.missing_in_all:
            print(
                "   Missing from __all__: "
                + ", ".join(report.missing_in_all)
            )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
