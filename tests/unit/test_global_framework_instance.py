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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vibe_check.tools.vibe_check_framework import get_vibe_check_framework


class TestGlobalVibeCheckFramework:
    """Test global vibe check framework instance management"""
    
    def test_get_vibe_check_framework_singleton(self):
        """Test that get_vibe_check_framework returns singleton instance"""
        with patch('vibe_check.tools.vibe_check_framework.VibeCheckFramework') as mock_framework_class:
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
        with patch('vibe_check.tools.vibe_check_framework.VibeCheckFramework') as mock_framework_class:
            mock_instance = MagicMock()
            mock_framework_class.return_value = mock_instance
            
            # Call with specific token
            framework = get_vibe_check_framework("custom_token")
            
            # Should create new instance with token
            mock_framework_class.assert_called_once_with(github_token="custom_token")
            assert framework is mock_instance
    
    def test_get_vibe_check_framework_token_override(self):
        """Test that providing token creates new instance"""
        with patch('vibe_check.tools.vibe_check_framework.VibeCheckFramework') as mock_framework_class:
            # Create different mock instances
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            mock_framework_class.side_effect = [mock_instance1, mock_instance2]
            
            # First call without token
            framework1 = get_vibe_check_framework()
            # Second call with token
            framework2 = get_vibe_check_framework("token123")
            
            # Should be different instances
            assert framework1 is not framework2
            # Should call constructor twice with different parameters
            assert mock_framework_class.call_count == 2
            calls = mock_framework_class.call_args_list
            assert calls[0][1] == {}  # No token
            assert calls[1][1] == {"github_token": "token123"}  # With token
    
    def test_get_vibe_check_framework_caching_behavior(self):
        """Test caching behavior of global framework"""
        with patch('vibe_check.tools.vibe_check_framework.VibeCheckFramework') as mock_framework_class:
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
        """Test that different configurations create separate instances"""
        with patch('vibe_check.tools.vibe_check_framework.VibeCheckFramework') as mock_framework_class:
            # Create different mock instances
            instances = [MagicMock() for _ in range(3)]
            mock_framework_class.side_effect = instances
            
            # Call with different configurations
            framework_default = get_vibe_check_framework()
            framework_token1 = get_vibe_check_framework("token1")
            framework_token2 = get_vibe_check_framework("token2")
            
            # Should be different instances
            assert framework_default is not framework_token1
            assert framework_token1 is not framework_token2
            assert framework_default is not framework_token2
            
            # Verify constructor calls
            assert mock_framework_class.call_count == 3
            calls = mock_framework_class.call_args_list
            assert calls[0][1] == {}
            assert calls[1][1] == {"github_token": "token1"}
            assert calls[2][1] == {"github_token": "token2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])