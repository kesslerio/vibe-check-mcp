"""Regression tests for compatibility shims."""

import pytest
from pydantic import ValidationError

from mcp.types import InitializedNotification

from vibe_check.server import compat
from vibe_check.server.compat import enable_legacy_initialized_notification


@pytest.fixture(autouse=True)
def reset_compat_state() -> None:
    """Reset global state before each test for isolation."""
    # Reset the patch guard so each test starts fresh
    compat._legacy_compat_patched = False
    yield


def test_legacy_initialized_notification_accepted() -> None:
    """The shim should allow the legacy "initialized" method value."""

    enable_legacy_initialized_notification()

    message = InitializedNotification(method="initialized")

    assert message.method == "initialized"


def test_spec_compliant_notification_still_works() -> None:
    """Verify the patch doesn't break spec-compliant clients."""

    enable_legacy_initialized_notification()

    # Spec-compliant clients sending the correct method should continue working
    message = InitializedNotification(method="notifications/initialized")

    assert message.method == "notifications/initialized"


def test_idempotent_patching() -> None:
    """Calling enable_legacy multiple times should be safe and idempotent."""

    # Calling the function multiple times should not error, even if already patched
    result1 = enable_legacy_initialized_notification()
    result2 = enable_legacy_initialized_notification()

    # At least one call should succeed (return True) or both could return False if
    # already patched from previous tests. The key is no exceptions are raised.
    assert isinstance(result1, bool), "Should return a boolean"
    assert isinstance(result2, bool), "Should return a boolean"

    # Verify both methods work after multiple calls
    msg1 = InitializedNotification(method="initialized")
    assert msg1.method == "initialized"

    msg2 = InitializedNotification(method="notifications/initialized")
    assert msg2.method == "notifications/initialized"


def test_invalid_methods_still_rejected() -> None:
    """Ensure arbitrary invalid methods are still rejected by validation."""

    enable_legacy_initialized_notification()

    # Only "initialized" and "notifications/initialized" are valid
    with pytest.raises(ValidationError) as exc_info:
        InitializedNotification(method="garbage/value")  # type: ignore[arg-type]

    assert "literal_error" in str(exc_info.value).lower()
