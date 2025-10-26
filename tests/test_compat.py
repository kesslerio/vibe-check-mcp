"""Regression tests for compatibility shims."""

from mcp.types import InitializedNotification

from vibe_check.server.compat import enable_legacy_initialized_notification


def test_legacy_initialized_notification_accepted() -> None:
    """The shim should allow the legacy "initialized" method value."""

    enable_legacy_initialized_notification()

    message = InitializedNotification(method="initialized")

    assert message.method == "initialized"
