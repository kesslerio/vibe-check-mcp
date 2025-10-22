"""
Backward compatibility shim for ``vibe_check.tools.vibe_check_framework``.

The modern implementation lives under ``vibe_check.tools.legacy`` to reflect its
deprecated status, but several historical tests – including ones referenced in
issue #148 – still import from the old location. Importing this module ensures
those paths keep working without forcing immediate refactors.
"""

from __future__ import annotations

import warnings

from .legacy.vibe_check_framework import (
    VibeCheckFramework as _VibeCheckFramework,
    get_vibe_check_framework as _get_vibe_check_framework,
)

warnings.warn(
    "Importing from 'vibe_check.tools.vibe_check_framework' is deprecated; "
    "use 'vibe_check.tools.legacy.vibe_check_framework' instead.",
    DeprecationWarning,
    stacklevel=2,
)

VibeCheckFramework = _VibeCheckFramework


def get_vibe_check_framework(*args, **kwargs):
    warnings.warn(
        "Calling get_vibe_check_framework from 'vibe_check.tools.vibe_check_framework' "
        "is deprecated; use 'vibe_check.tools.legacy.vibe_check_framework' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_vibe_check_framework(*args, **kwargs)


__all__ = ["VibeCheckFramework", "get_vibe_check_framework"]
