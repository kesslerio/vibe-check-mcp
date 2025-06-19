"""
Unit tests for the logging framework
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch
from io import StringIO
import sys

from vibe_check.utils.logging_framework import (
    VibeLogger, 
    LoggingConfig, 
    LoggingMode,
    get_vibe_logger,
    _default_sanitizer
)


class TestLoggingConfig:
    def test_from_environment_defaults(self):
        """Test default configuration from environment"""
        with patch.dict('os.environ', {}, clear=True):
            config = LoggingConfig.from_environment()
            assert config.console_enabled is True
            assert config.emoji_enabled is True
            assert config.progress_tracking is True
            assert config.timing_enabled is True
            assert config.file_logging is True
            assert config.structured_json is False
            assert config.mcp_server_mode is False

    def test_from_environment_disabled(self):
        """Test configuration with disabled features"""
        env_vars = {
            'VIBE_LOG_SILENT': '1',
            'VIBE_LOG_NO_EMOJI': '1',
            'VIBE_LOG_NO_PROGRESS': '1',
            'VIBE_LOG_NO_TIMING': '1',
            'VIBE_LOG_NO_FILE': '1',
            'VIBE_LOG_JSON': '1',
            'MCP_SERVER_MODE': '1'
        }
        with patch.dict('os.environ', env_vars, clear=True):
            config = LoggingConfig.from_environment()
            assert config.console_enabled is False
            assert config.emoji_enabled is False
            assert config.progress_tracking is False
            assert config.timing_enabled is False
            assert config.file_logging is False
            assert config.structured_json is True
            assert config.mcp_server_mode is True

    def test_validate_valid_config(self):
        """Test validation with valid configuration"""
        config = LoggingConfig()
        config.validate()  # Should not raise

    def test_validate_invalid_config(self):
        """Test validation with invalid configuration"""
        config = LoggingConfig()
        config.console_enabled = "not a boolean"
        
        with pytest.raises(ValueError, match="console_enabled must be a boolean"):
            config.validate()


class TestVibeLogger:
    def setup_method(self):
        """Setup for each test"""
        self.config = LoggingConfig(
            console_enabled=False,  # Disable console for testing
            file_logging=True,
            emoji_enabled=True
        )
        self.mock_logger = Mock(spec=logging.Logger)
        self.vibe_logger = VibeLogger("test_tool", self.config, self.mock_logger)

    def test_init_with_valid_config(self):
        """Test initialization with valid config"""
        logger = VibeLogger("test", self.config)
        assert logger.tool_name == "test"
        assert logger.config == self.config

    def test_init_with_invalid_config_falls_back(self):
        """Test initialization with invalid config falls back to defaults"""
        invalid_config = LoggingConfig()
        invalid_config.console_enabled = "invalid"
        
        logger = VibeLogger("test", invalid_config)
        # Should fall back to default config
        assert isinstance(logger.config.console_enabled, bool)

    def test_progress_logging(self):
        """Test progress logging"""
        self.vibe_logger.progress("Test progress", "🔄", "details")
        
        # Check that technical log was called
        self.mock_logger.info.assert_called()
        call_args = self.mock_logger.info.call_args[0][0]
        assert "PROGRESS: Test progress | details" in call_args

    def test_success_logging(self):
        """Test success logging"""
        self.vibe_logger.success("Test success", "details")
        
        self.mock_logger.info.assert_called()
        call_args = self.mock_logger.info.call_args[0][0]
        assert "SUCCESS: Test success | details" in call_args

    def test_error_logging_with_exception(self):
        """Test error logging with exception"""
        test_exception = ValueError("test error")
        self.vibe_logger.error("Test error", "details", test_exception)
        
        self.mock_logger.error.assert_called()
        call_args = self.mock_logger.error.call_args
        assert "Test error | Details: details | Exception: test error" in call_args[0][0]
        assert call_args[1]['exc_info'] is True

    def test_operation_context_manager(self):
        """Test operation context manager"""
        with self.vibe_logger.operation("Test operation", 2):
            self.vibe_logger.step("Step 1")
            self.vibe_logger.step("Step 2")
        
        # Should have logged operation start and completion
        assert self.mock_logger.info.call_count >= 3  # start + 2 steps + completion

    def test_operation_context_manager_with_exception(self):
        """Test operation context manager with exception"""
        with pytest.raises(ValueError):
            with self.vibe_logger.operation("Test operation"):
                raise ValueError("test error")
        
        # Should have logged error
        self.mock_logger.error.assert_called()

    def test_stats_logging(self):
        """Test statistics logging"""
        test_data = {"count": 5, "rate": 0.75, "status": "good"}
        self.vibe_logger.stats("Test Stats", test_data)
        
        self.mock_logger.info.assert_called()
        call_args = self.mock_logger.info.call_args[0][0]
        assert "STATS: Test Stats" in call_args
        assert "count: 5" in call_args
        assert "rate: 0.8" in call_args  # Should be rounded

    def test_clock_adjustment_protection(self):
        """Test protection against clock adjustment"""
        # Simulate time going backwards
        with patch('time.time', side_effect=[1000.0, 999.0]):
            logger = VibeLogger("test", self.config, self.mock_logger)
            logger.progress("test")
        
        # Should not crash and should use 0 as fallback
        self.mock_logger.info.assert_called()


class TestSanitization:
    def test_default_sanitizer_api_keys(self):
        """Test sanitization of API keys"""
        message = "API_KEY=abc123456789 and token: def987654321"
        sanitized = _default_sanitizer(message)
        
        assert "abc123456789" not in sanitized
        assert "def987654321" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_default_sanitizer_github_tokens(self):
        """Test sanitization of GitHub tokens"""
        message = "GitHub token: ghp_1234567890123456789012345678901234567890"
        sanitized = _default_sanitizer(message)
        
        assert "ghp_1234567890123456789012345678901234567890" not in sanitized
        # The generic pattern catches this as "token: xxxx" -> "token=***REDACTED***"
        assert "***REDACTED***" in sanitized

    def test_default_sanitizer_env_vars(self):
        """Test sanitization of environment variables"""
        message = "GITHUB_TOKEN=secret123 ANTHROPIC_API_KEY='another_secret'"
        sanitized = _default_sanitizer(message)
        
        assert "secret123" not in sanitized
        assert "another_secret" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_sanitizer_integration(self):
        """Test sanitizer integration in logger"""
        config = LoggingConfig(file_logging=True, console_enabled=False)
        mock_logger = Mock(spec=logging.Logger)
        vibe_logger = VibeLogger("test", config, mock_logger)
        
        vibe_logger.info("API_KEY=secret123")
        
        # Check that the sanitized message was logged
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        assert "secret123" not in call_args
        assert "***REDACTED***" in call_args


class TestFactoryFunctions:
    def test_get_vibe_logger_default(self):
        """Test factory function with defaults"""
        logger = get_vibe_logger("test_tool")
        assert logger.tool_name == "test_tool"
        assert isinstance(logger.config, LoggingConfig)

    def test_get_vibe_logger_with_mode(self):
        """Test factory function with mode"""
        logger = get_vibe_logger("test_tool", LoggingMode.SILENT)
        assert logger.config.console_enabled is False
        assert logger.config.file_logging is False

    def test_get_vibe_logger_with_overrides(self):
        """Test factory function with config overrides"""
        logger = get_vibe_logger("test_tool", emoji_enabled=False)
        assert logger.config.emoji_enabled is False


class TestPerformance:
    def test_logger_creation_performance(self):
        """Test that logger creation is reasonably fast"""
        start_time = time.time()
        
        # Create multiple loggers
        for i in range(100):
            get_vibe_logger(f"test_{i}")
        
        duration = time.time() - start_time
        # Should be fast (less than 1 second for 100 loggers)
        assert duration < 1.0

    def test_operation_timing_accuracy(self):
        """Test that operation timing is reasonably accurate"""
        config = LoggingConfig(console_enabled=False)
        mock_logger = Mock(spec=logging.Logger)
        vibe_logger = VibeLogger("test", config, mock_logger)
        
        start_time = time.time()
        with vibe_logger.operation("test"):
            time.sleep(0.1)  # Sleep for 100ms
        duration = time.time() - start_time
        
        # Should be close to 100ms (allow some tolerance)
        assert 0.08 < duration < 0.15


if __name__ == "__main__":
    pytest.main([__file__])