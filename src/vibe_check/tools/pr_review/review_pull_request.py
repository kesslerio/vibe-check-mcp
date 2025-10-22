"""
Compatibility layer for the historic ``review_pull_request`` import path.

Before the modular PR review refactor, tests imported the reviewer function via
``vibe_check.tools.pr_review.review_pull_request``.  The refactor consolidated
the logic into ``main.py`` which broke collection for any code relying on the
old module path.  Re-exporting the function here keeps those imports working
while nudging call sites toward ``vibe_check.tools.pr_review``.
"""

from __future__ import annotations

from .main import review_pull_request

__all__ = ["review_pull_request"]
