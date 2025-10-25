"""
Compatibility layer for the historic ``review_pull_request`` import path.

Before the modular PR review refactor, tests imported the reviewer function via
``vibe_check.tools.pr_review.review_pull_request``.  The refactor consolidated
the logic into ``main.py`` which broke collection for any code relying on the
old module path.  Re-exporting the function here keeps those imports working
while nudging call sites toward ``vibe_check.tools.pr_review``.
"""

from __future__ import annotations

import warnings

from .main import review_pull_request as _review_pull_request

warnings.warn(
    "Importing from 'vibe_check.tools.pr_review.review_pull_request' is deprecated; "
    "use 'vibe_check.tools.pr_review' instead.",
    DeprecationWarning,
    stacklevel=2,
)


def review_pull_request(*args, **kwargs):
    warnings.warn(
        "Calling review_pull_request from 'vibe_check.tools.pr_review.review_pull_request' "
        "is deprecated; import from 'vibe_check.tools.pr_review' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _review_pull_request(*args, **kwargs)


__all__ = ["review_pull_request"]
