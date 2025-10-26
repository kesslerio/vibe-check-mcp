"""Compatibility shims for external MCP clients."""

from __future__ import annotations

from typing import Literal, get_args, get_origin


def enable_legacy_initialized_notification() -> bool:
    """Allow older clients that send ``"initialized"`` notifications.

    Codex still emits the pre-1.0 MCP notification method value ``"initialized"``
    during the handshake. The upstream ``mcp`` package now enforces
    ``"notifications/initialized"`` via ``Literal`` validation, so the legacy
    value is rejected before FastMCP gets a chance to finish the handshake. We
    patch the Pydantic field annotation at runtime to accept both values.

    Returns:
        ``True`` if the patch was applied, ``False`` when already compatible.
    """

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
        # Already patched (or upstream added support); nothing to do.
        return False

    # TODO(#5044): Remove once Codex fixes RMCP initialized notification
    # https://github.com/openai/codex/issues/5044
    field.annotation = Literal["notifications/initialized", "initialized"]  # type: ignore[assignment]

    # Rebuild the models so Pydantic picks up the updated field definition.
    types.InitializedNotification.model_rebuild(force=True)
    types.ClientNotification.model_rebuild(force=True)

    return True
