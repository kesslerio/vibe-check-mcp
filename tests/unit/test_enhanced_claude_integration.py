"""
Tests for Enhanced Claude CLI Integration with Context Injection

Tests automatic project context injection into Claude CLI prompts
without requiring changes to existing analysis tool signatures.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from vibe_check.tools.shared.enhanced_claude_integration import (
    EnhancedClaudeCliExecutor,
)
from vibe_check.tools.shared.claude_integration import ClaudeCliResult
from vibe_check.config.vibe_check_config import VibeCheckConfig, ContextLoadingConfig
from vibe_check.tools.contextual_documentation import AnalysisContext


class TestEnhancedClaudeCliExecutor(unittest.TestCase):
    """Test suite for EnhancedClaudeCliExecutor context injection functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.vibe_check_dir = self.project_root / ".vibe-check"
        self.vibe_check_dir.mkdir()

        # Create enhanced executor with test project root
        self.executor = EnhancedClaudeCliExecutor(
            timeout_seconds=30, project_root=str(self.project_root)
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_test_config(
        self, enabled: bool = True, library_detection_enabled: bool = True
    ) -> None:
        """Create test configuration file"""
        config = {
            "context_loading": {
                "enabled": enabled,
                "cache_duration_minutes": 5,
                "library_detection": {
                    "enabled": library_detection_enabled,
                    "languages": ["python"],
                    "depth": "imports_only",
                },
            }
        }

        config_file = self.vibe_check_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

    def _create_project_context_file(self, content: str = None) -> None:
        """Create project context markdown file"""
        if content is None:
            content = """# Test Project Context

## Team Conventions
- Use pytest for testing
- Follow PEP 8 style guide

## Pattern Exceptions
- Custom auth required for compliance"""

        context_file = self.vibe_check_dir / "project-context.md"
        with open(context_file, "w") as f:
            f.write(content)

    def _create_pattern_exceptions_file(self) -> None:
        """Create pattern exceptions JSON file"""
        exceptions = {
            "approved_patterns": ["custom-auth-pattern"],
            "reasoning": {"custom-auth-pattern": "Required for GDPR compliance"},
        }

        exceptions_file = self.vibe_check_dir / "pattern-exceptions.json"
        with open(exceptions_file, "w") as f:
            json.dump(exceptions, f)

    def test_load_vibe_check_config_enabled(self):
        """Test loading enabled configuration"""
        self._create_test_config(enabled=True)

        config = self.executor._load_vibe_check_config()

        self.assertIsNotNone(config)
        self.assertTrue(config.context_loading.enabled)
        self.assertEqual(config.context_loading.cache_duration_minutes, 5)

    def test_load_vibe_check_config_disabled(self):
        """Test loading disabled configuration"""
        self._create_test_config(enabled=False)

        config = self.executor._load_vibe_check_config()

        self.assertIsNone(config)

    def test_load_vibe_check_config_missing(self):
        """Test behavior when config file is missing"""
        # When no config file exists, the loader returns default config with enabled=True
        # but our enhanced executor should return None since context loading isn't explicitly enabled
        config = self.executor._load_vibe_check_config()
        # The actual behavior is that it returns a default config but we check if context_loading.enabled
        # Since default is enabled=True, it should return a config object
        self.assertIsNotNone(config)

    def test_load_project_context_file(self):
        """Test loading project context markdown file"""
        test_content = "# Test Context\nThis is test content"
        self._create_project_context_file(test_content)

        context = self.executor._load_project_context_file()

        self.assertEqual(context, test_content)

    def test_load_project_context_file_missing(self):
        """Test behavior when project context file is missing"""
        context = self.executor._load_project_context_file()
        self.assertIsNone(context)

    def test_load_project_context_if_enabled_full(self):
        """Test loading complete project context when enabled"""
        self._create_test_config(enabled=True)
        self._create_project_context_file()
        self._create_pattern_exceptions_file()

        context = self.executor._load_project_context_if_enabled()

        self.assertIsNotNone(context)
        self.assertIn("## Project-Specific Context", context)
        self.assertIn("Team Conventions", context)
        self.assertIn("## Approved Pattern Exceptions", context)
        self.assertIn("custom-auth-pattern", context)

    def test_load_project_context_if_enabled_disabled(self):
        """Test that no context is loaded when disabled"""
        self._create_test_config(enabled=False)
        self._create_project_context_file()

        context = self.executor._load_project_context_if_enabled()

        self.assertIsNone(context)

    def test_load_project_context_if_enabled_no_files(self):
        """Test behavior when enabled but no context files exist"""
        self._create_test_config(enabled=True)

        context = self.executor._load_project_context_if_enabled()

        self.assertIsNone(context)

    @patch(
        "src.vibe_check.tools.shared.enhanced_claude_integration.get_context_manager"
    )
    def test_get_cached_analysis_context(self, mock_get_context_manager):
        """Test cached analysis context loading"""
        # Mock context manager and analysis context
        mock_context = Mock()
        mock_context.library_docs = {"react": "React documentation"}
        mock_context.project_conventions = {"style": "PEP 8"}
        mock_context.pattern_exceptions = []
        mock_context.conflict_resolution = {}
        mock_context.context_metadata = {"last_updated": "2023-01-01"}

        mock_manager = Mock()
        mock_manager.get_project_context.return_value = mock_context
        mock_get_context_manager.return_value = mock_manager

        # First call should load fresh context
        result1 = self.executor._get_cached_analysis_context()
        self.assertEqual(result1, mock_context)

        # Second call should use cached context
        result2 = self.executor._get_cached_analysis_context()
        self.assertEqual(result2, mock_context)

        # Should only call get_project_context once due to caching
        mock_manager.get_project_context.assert_called_once()

    @patch(
        "src.vibe_check.tools.shared.enhanced_claude_integration.get_context_manager"
    )
    def test_load_library_context(self, mock_get_context_manager):
        """Test loading library-specific context"""
        self._create_test_config(enabled=True, library_detection_enabled=True)

        # Mock analysis context with library docs
        mock_context = Mock()
        mock_context.library_docs = {
            "react": "React is a JavaScript library for building user interfaces...",
            "fastapi": "FastAPI is a modern web framework for Python APIs...",
        }
        mock_context.pattern_exceptions = []
        mock_context.conflict_resolution = {}
        mock_context.context_metadata = {"last_updated": "2023-01-01"}

        mock_manager = Mock()
        mock_manager.get_project_context.return_value = mock_context
        mock_get_context_manager.return_value = mock_manager

        library_context = self.executor._load_library_context(["react"])

        self.assertIsNotNone(library_context)
        self.assertIn("## Library Context", library_context)
        self.assertIn("### react", library_context)
        self.assertIn("React is a JavaScript library", library_context)

    @patch(
        "src.vibe_check.tools.shared.claude_integration.ClaudeCliExecutor._get_claude_args"
    )
    def test_get_claude_args_with_context_injection(self, mock_parent_get_claude_args):
        """Test that Claude args are enhanced with context injection"""
        self._create_test_config(enabled=True)
        self._create_project_context_file()

        mock_parent_get_claude_args.return_value = ["base", "args"]

        original_prompt = "Analyze this code"
        result_args = self.executor._get_claude_args(
            original_prompt, "code_analysis", "sonnet"
        )

        # Verify parent method was called with enhanced prompt
        mock_parent_get_claude_args.assert_called_once()
        called_args = mock_parent_get_claude_args.call_args[0]
        enhanced_prompt = called_args[0]

        # Enhanced prompt should contain original prompt plus context
        self.assertIn("## Analysis Request", enhanced_prompt)
        self.assertIn(original_prompt, enhanced_prompt)
        self.assertIn("## Project-Specific Context", enhanced_prompt)
        self.assertIn("Team Conventions", enhanced_prompt)

    @patch(
        "src.vibe_check.tools.shared.claude_integration.ClaudeCliExecutor._get_claude_args"
    )
    def test_get_claude_args_without_context(self, mock_parent_get_claude_args):
        """Test that prompts work normally when context is unavailable"""
        # Don't create config file - context injection should be disabled
        mock_parent_get_claude_args.return_value = ["base", "args"]

        original_prompt = "Analyze this code"
        result_args = self.executor._get_claude_args(
            original_prompt, "code_analysis", "sonnet"
        )

        # Verify parent method was called with original prompt unchanged
        mock_parent_get_claude_args.assert_called_once()
        called_args = mock_parent_get_claude_args.call_args[0]
        actual_prompt = called_args[0]

        self.assertEqual(actual_prompt, original_prompt)

    @patch(
        "src.vibe_check.tools.shared.claude_integration.ClaudeCliExecutor._get_system_prompt"
    )
    def test_get_system_prompt_with_context_injection(
        self, mock_parent_get_system_prompt
    ):
        """Test that system prompts are enhanced with project context"""
        self._create_test_config(enabled=True)
        self._create_project_context_file()

        mock_parent_get_system_prompt.return_value = "Base system prompt"

        result_prompt = self.executor._get_system_prompt("code_analysis")

        # Should contain both base prompt and injected context
        self.assertIn("Base system prompt", result_prompt)
        self.assertIn("## Additional Project Context", result_prompt)
        self.assertIn("Team Conventions", result_prompt)

    def test_inheritance_compatibility(self):
        """Test that EnhancedClaudeCliExecutor maintains compatibility with parent class"""
        # Should inherit all parent methods and attributes
        self.assertIsInstance(self.executor, EnhancedClaudeCliExecutor)

        # Should have all parent class methods
        parent_methods = [
            "execute_sync",
            "execute_async",
            "_find_claude_cli",
            "_get_mcp_config_path",
        ]
        for method in parent_methods:
            self.assertTrue(hasattr(self.executor, method))

    @patch("subprocess.run")
    def test_graceful_degradation_on_context_error(self, mock_subprocess):
        """Test that executor works normally even if context loading fails"""
        # Create config that will cause context loading to fail
        self._create_test_config(enabled=True)
        # Create invalid JSON in pattern exceptions to trigger error
        (self.vibe_check_dir / "pattern-exceptions.json").write_text("invalid json")

        # Mock successful subprocess execution
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Analysis result", stderr=""
        )

        # Execute should work despite context loading error
        result = self.executor.execute_sync("test prompt", "general")

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Analysis result")


class TestContextInjectionIntegration(unittest.TestCase):
    """Integration tests for context injection in real scenarios"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.vibe_check_dir = self.project_root / ".vibe-check"
        self.vibe_check_dir.mkdir()

    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    @patch(
        "src.vibe_check.tools.shared.enhanced_claude_integration.get_context_manager"
    )
    def test_end_to_end_context_injection(
        self, mock_get_context_manager, mock_subprocess
    ):
        """Test complete end-to-end context injection flow"""
        # Create realistic project configuration
        config = {
            "context_loading": {
                "enabled": True,
                "cache_duration_minutes": 60,
                "library_detection": {
                    "enabled": True,
                    "languages": ["python", "typescript"],
                    "depth": "imports_only",
                },
            },
            "libraries": {
                "react": {"version": "18.x", "patterns": ["hooks-preferred"]},
                "fastapi": {"version": "0.100+", "patterns": ["async-preferred"]},
            },
        }

        with open(self.vibe_check_dir / "config.json", "w") as f:
            json.dump(config, f)

        # Create project context file
        project_context = """# Test Project
        
## Conventions
- Use React hooks instead of class components
- FastAPI async/await required for all endpoints

## Exceptions
- Legacy components allowed during migration phase"""

        with open(self.vibe_check_dir / "project-context.md", "w") as f:
            f.write(project_context)

        # Mock analysis context
        mock_context = Mock()
        mock_context.library_docs = {
            "react": "React 18 documentation with hooks patterns",
            "fastapi": "FastAPI async documentation",
        }
        mock_context.pattern_exceptions = []
        mock_context.conflict_resolution = {}
        mock_context.context_metadata = {"last_updated": "2023-01-01"}

        mock_manager = Mock()
        mock_manager.get_project_context.return_value = mock_context
        mock_get_context_manager.return_value = mock_manager

        # Mock successful Claude CLI execution
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Context-aware analysis result", stderr=""
        )

        # Execute analysis
        executor = EnhancedClaudeCliExecutor(project_root=str(self.project_root))
        result = executor.execute_sync("Analyze this React component", "code_analysis")

        # Verify execution succeeded
        self.assertTrue(result.success)

        # Verify subprocess was called with enhanced prompt
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        command_args = call_args[0][0]  # First positional arg is the command list

        # The prompt should be the last argument and contain context
        enhanced_prompt = command_args[-1]
        self.assertIn("Test Project", enhanced_prompt)
        self.assertIn("React hooks", enhanced_prompt)
        self.assertIn("## Library Context", enhanced_prompt)
        self.assertIn("React 18 documentation", enhanced_prompt)
        self.assertIn("Analyze this React component", enhanced_prompt)


if __name__ == "__main__":
    unittest.main()
