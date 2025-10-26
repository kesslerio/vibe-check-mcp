"""Compatibility shims for external MCP clients."""

from __future__ import annotations

from typing import Literal, get_args, get_origin

# Guard against concurrent patching in multi-threaded contexts
_legacy_compat_patched = False


def enable_legacy_initialized_notification() -> bool:
    """Allow older clients that send ``"initialized"`` notifications.

    Codex CLI (versions ≤0.48) emits the pre-1.0 MCP notification method value
    ``"initialized"`` instead of the spec-compliant ``"notifications/initialized"``
    during the handshake. The upstream ``mcp`` package enforces the Literal constraint,
    so the legacy value is rejected before FastMCP can complete initialization.

    This function patches the Pydantic field annotation at runtime to accept both
    method values, ensuring compatibility during the Codex transition period.

    Returns:
        ``True`` if the patch was applied, ``False`` when already compatible or patched.

    See Also:
        - Codex issue #5044: RMCP transport sends legacy initialized notification
        - Codex issue #5208: Streamable HTTP MCP server handshaking failed
    """
    global _legacy_compat_patched

    if _legacy_compat_patched:
        return False

    # Import locally to avoid pulling heavy dependencies for callers that do not
    # need stdio transport.
    from mcp import types

    field = types.InitializedNotification.model_fields.get("method")
    if field is None:
        return False

    annotation = field.annotation
    origin = get_origin(annotation)
    allowed = set(get_args(annotation)) if origin else {annotation}

    if "initialized" in allowed:
        # Already compatible (patch may have been applied elsewhere).
        _legacy_compat_patched = True
        return False

    # TODO: Remove when Codex CLI v0.49+ ships with fixed RMCP transport
    # Codex issues #5044 #5208 track the internal RMCP client bug
    field.annotation = Literal["notifications/initialized", "initialized"]  # type: ignore[assignment]

    # Rebuild the models so Pydantic picks up the updated field definition.
    types.InitializedNotification.model_rebuild(force=True)
    types.ClientNotification.model_rebuild(force=True)

    _legacy_compat_patched = True
    return True
