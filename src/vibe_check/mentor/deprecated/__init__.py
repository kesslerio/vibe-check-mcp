"""Deprecated mentor modules retained for backwards compatibility.

These helpers power the transitional compatibility layer exposed via
``vibe_check.mentor.mcp_sampling_security``.  Shipping them as a proper
package ensures editable installs include the legacy modules so that
imports like ``vibe_check.mentor.deprecated.mcp_sampling_secure`` remain
available to security regression tests and downstream extensions.
"""

from . import mcp_sampling_migration
from . import mcp_sampling_optimized
from . import mcp_sampling_patch
from . import mcp_sampling_secure
from . import mcp_sampling_ultrafast

__all__ = [
    "mcp_sampling_migration",
    "mcp_sampling_optimized",
    "mcp_sampling_patch",
    "mcp_sampling_secure",
    "mcp_sampling_ultrafast",
]
