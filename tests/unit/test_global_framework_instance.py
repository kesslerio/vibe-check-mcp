"""
Unit Tests for Global Vibe Check Framework Instance Management

Tests the global framework instance functionality:
- Singleton pattern implementation
- Token management and configuration
- Instance reuse and isolation
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from vibe_check.tools.legacy.vibe_check_framework import get_vibe_check_framework
import vibe_check.tools.legacy.vibe_check_framework as framework_module


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton cache before each test"""
    framework_module._vibe_check_framework = None
    yield
    framework_module._vibe_check_framework = None


class TestGlobalVibeCheckFramework:
    """Test global vibe check framework instance management"""

    def test_get_vibe_check_framework_singleton(self):
        """Test that get_vibe_check_framework returns singleton instance"""
        with patch(
            "vibe_check.tools.legacy.vibe_check_framework.VibeCheckFramework"
        ) as mock_framework_class:
            mock_instance = MagicMock()
            mock_framework_class.return_value = mock_instance

            # First call
            framework1 = get_vibe_check_framework()
            # Second call
            framework2 = get_vibe_check_framework()

            # Should return same instance
            assert framework1 is framework2
            # Should only create instance once
            mock_framework_class.assert_called_once()

    def test_get_vibe_check_framework_with_token(self):
        """Test get_vibe_check_framework with specific token"""
        with patch(
            "vibe_check.tools.legacy.vibe_check_framework.VibeCheckFramework"
        ) as mock_framework_class:
            mock_instance = MagicMock()
            mock_framework_class.return_value = mock_instance

            # Call with specific token
            framework = get_vibe_check_framework("custom_token")

            # Should create new instance with token
            mock_framework_class.assert_called_once_with("custom_token")
            assert framework is mock_instance

    def test_get_vibe_check_framework_token_override(self):
        """Test that providing token on subsequent calls is ignored due to caching"""
        with patch(
            "vibe_check.tools.legacy.vibe_check_framework.VibeCheckFramework"
        ) as mock_framework_class:
            mock_instance = MagicMock()
            mock_framework_class.return_value = mock_instance

            # First call without token
            framework1 = get_vibe_check_framework()
            # Second call with token
            framework2 = get_vibe_check_framework("token123")

            # Should be the same instance due to singleton caching
            assert framework1 is framework2
            # Should only call constructor once
            mock_framework_class.assert_called_once_with(None)

    def test_get_vibe_check_framework_caching_behavior(self):
        """Test caching behavior of global framework"""
        with patch(
            "vibe_check.tools.legacy.vibe_check_framework.VibeCheckFramework"
        ) as mock_framework_class:
            mock_instance = MagicMock()
            mock_framework_class.return_value = mock_instance

            # Multiple calls without token should reuse instance
            framework1 = get_vibe_check_framework()
            framework2 = get_vibe_check_framework()
            framework3 = get_vibe_check_framework()

            # All should be same instance
            assert framework1 is framework2 is framework3
            # Should only initialize once
            mock_framework_class.assert_called_once()

    def test_get_vibe_check_framework_configuration_isolation(self):
        """Test that different configurations are ignored on subsequent calls"""
        with patch(
            "vibe_check.tools.legacy.vibe_check_framework.VibeCheckFramework"
        ) as mock_framework_class:
            mock_instance = MagicMock()
            mock_framework_class.return_value = mock_instance

            # Call with different configurations
            framework_default = get_vibe_check_framework()
            framework_token1 = get_vibe_check_framework("token1")
            framework_token2 = get_vibe_check_framework("token2")

            # Should be the same instance
            assert framework_default is framework_token1
            assert framework_token1 is framework_token2

            # Verify constructor was called only once with the first configuration
            mock_framework_class.assert_called_once_with(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
