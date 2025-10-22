"""
Backward compatibility shim for ``vibe_check.tools.vibe_check_framework``.

The modern implementation lives under ``vibe_check.tools.legacy`` to reflect its
deprecated status, but several historical tests – including ones referenced in
issue #148 – still import from the old location. Importing this module ensures
those paths keep working without forcing immediate refactors.
"""

from __future__ import annotations

from .legacy.vibe_check_framework import (
    VibeCheckFramework,
    get_vibe_check_framework,
)

__all__ = ["VibeCheckFramework", "get_vibe_check_framework"]
