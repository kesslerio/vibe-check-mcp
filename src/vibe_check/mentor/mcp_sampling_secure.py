"""Backward-compatible alias for :mod:`vibe_check.mentor.mcp_sampling_security`.

Historically callers imported the hardened MCP sampling helpers from
``mcp_sampling_secure``.  During the ongoing refactor the implementation was
moved into the deprecated namespace and the public shim was accidentally
removed.  Re-introducing this alias keeps existing imports working while
pointing everything to :mod:`mcp_sampling_security` where the compatibility
layer lives.
"""

from __future__ import annotations

from .mcp_sampling_security import *  # noqa: F401,F403
from .mcp_sampling_security import __all__ as _security_all

__all__ = list(_security_all)
