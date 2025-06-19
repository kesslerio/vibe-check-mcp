"""
Tests for configuration validation functionality.

Tests the configuration validation module to ensure proper validation
of Claude CLI and MCP setup. Part of issue #98 implementation.
"""

import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.vibe_check.tools.config_validation import (
    ConfigurationValidator,
    ValidationLevel,
    validate_configuration,
    format_validation_results
)


class TestConfigurationValidator:
    """Test the ConfigurationValidator class."""
    
    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = ConfigurationValidator()
        assert validator.results == []
        assert validator.home_dir == Path.home()
    
    def test_validate_all_returns_results(self):
        """Test that validate_all returns expected structure."""
        validator = ConfigurationValidator()
        can_start, results = validator.validate_all()
        
        assert isinstance(can_start, bool)
        assert isinstance(results, list)
        assert len(results) > 0  # Should have some validation results
        
        # Check that all results have expected structure
        for result in results:
            assert hasattr(result, 'check_name')
            assert hasattr(result, 'level')
            assert hasattr(result, 'success')
            assert hasattr(result, 'message')
    
    def test_claude_cli_availability_detection(self):
        """Test Claude CLI availability detection."""
        validator = ConfigurationValidator()
        
        with patch('subprocess.run') as mock_run:
            # Mock Claude CLI not found
            mock_run.return_value = MagicMock(returncode=1, stderr="command not found")
            validator._validate_claude_cli_availability()
            
            # Should have one result about Claude CLI availability
            claude_results = [r for r in validator.results if "claude_cli" in r.check_name]
            assert len(claude_results) >= 1
            
            # Find the availability check
            availability_result = next(
                (r for r in claude_results if "availability" in r.check_name), 
                None
            )
            assert availability_result is not None
            assert availability_result.level == ValidationLevel.WARNING
            assert not availability_result.success
    
    def test_claude_cli_available_case(self):
        """Test when Claude CLI is available."""
        validator = ConfigurationValidator()
        
        with patch('subprocess.run') as mock_run:
            # Mock Claude CLI found and working
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="/usr/local/bin/claude"),  # which claude
                MagicMock(returncode=0, stdout="claude version 1.0.0", stderr="")  # version check
            ]
            
            validator._validate_claude_cli_availability()
            
            availability_result = next(
                (r for r in validator.results if "availability" in r.check_name), 
                None
            )
            assert availability_result is not None
            assert availability_result.success
            assert "available and working" in availability_result.message.lower()
    
    def test_mcp_configuration_validation(self):
        """Test MCP configuration file validation."""
        validator = ConfigurationValidator()
        
        # Create a temporary MCP config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "mcpServers": {
                    "vibe-check": {
                        "command": "python",
                        "args": ["-m", "vibe_check.server"]
                    }
                }
            }
            json.dump(config, f)
            temp_config_path = f.name
        
        try:
            # Patch the config paths to include our temporary file
            with patch.object(validator, '_validate_mcp_config_file') as mock_validate:
                validator._validate_mcp_configuration_files()
                # Since we're not using the actual config paths, this just tests the structure
                
            # Test the individual config file validation directly
            validator._validate_mcp_config_file(Path(temp_config_path))
            
            # Should have results about MCP configuration
            mcp_results = [r for r in validator.results if "mcp" in r.check_name.lower()]
            assert len(mcp_results) >= 1
            
        finally:
            os.unlink(temp_config_path)
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in MCP config."""
        validator = ConfigurationValidator()
        
        # Create invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            temp_config_path = f.name
        
        try:
            validator._validate_mcp_config_file(Path(temp_config_path))
            
            # Should have an error result
            json_errors = [r for r in validator.results if "json" in r.check_name.lower()]
            assert len(json_errors) >= 1
            assert json_errors[0].level == ValidationLevel.CRITICAL
            assert not json_errors[0].success
            
        finally:
            os.unlink(temp_config_path)
    
    def test_environment_validation(self):
        """Test environment variable validation."""
        validator = ConfigurationValidator()
        
        # Test without PYTHONPATH set
        with patch.dict(os.environ, {}, clear=True):
            validator._validate_environment_setup()
            
            env_results = [r for r in validator.results if "environment" in r.check_name]
            assert len(env_results) >= 1
            
            # Should warn about missing PYTHONPATH
            assert any("PYTHONPATH" in r.message for r in env_results)
    
    def test_dependency_validation(self):
        """Test critical dependency validation."""
        validator = ConfigurationValidator()
        
        # This should pass in normal test environment since we have the dependencies
        validator._validate_critical_dependencies()
        
        dep_results = [r for r in validator.results if "dependencies" in r.check_name]
        assert len(dep_results) >= 1
        
        # Should find fastmcp and other dependencies
        dep_result = dep_results[0]
        assert dep_result.level == ValidationLevel.CRITICAL


class TestValidationResultFormatting:
    """Test validation result formatting functions."""
    
    def test_format_validation_results(self):
        """Test formatting of validation results."""
        # Create some sample results
        from src.vibe_check.tools.config_validation import ValidationResult
        
        results = [
            ValidationResult(
                check_name="test_critical",
                level=ValidationLevel.CRITICAL,
                success=False,
                message="Critical test failed",
                suggestion="Fix critical issue"
            ),
            ValidationResult(
                check_name="test_warning",
                level=ValidationLevel.WARNING,
                success=False,
                message="Warning test failed"
            ),
            ValidationResult(
                check_name="test_info",
                level=ValidationLevel.INFO,
                success=True,
                message="Info test passed"
            )
        ]
        
        formatted = format_validation_results(results)
        
        assert "Configuration Validation Results:" in formatted
        assert "CRITICAL:" in formatted
        assert "WARNING:" in formatted
        assert "INFO:" in formatted
        assert "❌ Critical test failed" in formatted
        assert "❌ Warning test failed" in formatted
        assert "✅ Info test passed" in formatted
        assert "💡 Fix critical issue" in formatted


class TestValidationIntegration:
    """Test integration with main validation function."""
    
    def test_validate_configuration_entry_point(self):
        """Test the main validate_configuration function."""
        can_start, results = validate_configuration()
        
        assert isinstance(can_start, bool)
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Should have various types of validation results
        check_names = [r.check_name for r in results]
        assert any("claude_cli" in name for name in check_names)
        assert any("dependencies" in name for name in check_names)
    
    def test_critical_failure_blocks_startup(self):
        """Test that critical failures prevent server startup."""
        validator = ConfigurationValidator()
        
        # Mock a critical dependency failure
        with patch('src.vibe_check.tools.config_validation.ConfigurationValidator._validate_critical_dependencies') as mock_deps:
            def add_critical_failure():
                from src.vibe_check.tools.config_validation import ValidationResult, ValidationLevel
                validator.results.append(ValidationResult(
                    check_name="critical_test_failure",
                    level=ValidationLevel.CRITICAL,
                    success=False,
                    message="Simulated critical failure"
                ))
            
            mock_deps.side_effect = add_critical_failure
            
            can_start, results = validator.validate_all()
            
            # Should not be able to start with critical failure
            assert not can_start
            
            # Should have the critical failure in results
            critical_failures = [r for r in results if r.level == ValidationLevel.CRITICAL and not r.success]
            assert len(critical_failures) >= 1


if __name__ == "__main__":
    pytest.main([__file__])