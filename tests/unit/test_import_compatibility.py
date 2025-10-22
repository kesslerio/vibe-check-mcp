"""
Regression tests for legacy import paths referenced in issue #148.

The refactor to modularize tooling relocated several modules, which briefly
caused ``ModuleNotFoundError`` during pytest collection.  These tests guarantee
the legacy import paths keep resolving so collection remains stable.
"""

from __future__ import annotations

import importlib
from typing import List

import pytest


LEGACY_IMPORTS: List[str] = [
    "vibe_check.tools.external_claude_cli",
    "vibe_check.tools.external_claude_cli.ExternalClaudeCli",
    "vibe_check.tools.external_claude_cli.ClaudeCliExecutor",
    "vibe_check.tools.vibe_check_framework",
    "vibe_check.tools.vibe_check_framework.VibeCheckFramework",
    "vibe_check.tools.pr_review.review_pull_request",
]


@pytest.mark.unit
@pytest.mark.parametrize("dotted_path", LEGACY_IMPORTS)
def test_legacy_imports_resolve(dotted_path: str) -> None:
    """
    Ensure historic dotted paths still resolve after modular refactors.

    The function supports both module-level imports and attribute lookups (by
    importing the module first and then accessing the attribute if necessary).
    """

    try:
        module_or_attr = importlib.import_module(dotted_path)
    except ModuleNotFoundError:
        module_name, _, attribute = dotted_path.rpartition(".")
        if not module_name:
            raise
        module = importlib.import_module(module_name)
        module_or_attr = getattr(module, attribute)

    assert module_or_attr is not None
