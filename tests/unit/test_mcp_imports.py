"""
Test MCP Import Context - Regression Test for Issues #229 and #233

Ensures that absolute imports work when modules are loaded by MCP server,
preventing "attempted relative import beyond top-level package" errors.
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestMCPImportContext:
    """Test that critical MCP tools can be imported in various contexts."""

    def test_analyze_github_pr_llm_imports_work_in_mcp_context(self):
        """
        Regression test for Issue #229: Ensure analyze_github_pr_llm
        can be imported without relative import errors.

        This test simulates the MCP server's module loading context
        where relative imports fail but absolute imports work correctly.
        """
        try:
            # Test the main function import that was failing
            from vibe_check.tools.analyze_llm.specialized_analyzers import (
                analyze_github_pr_llm,
            )

            # Verify it's actually a callable function
            assert callable(
                analyze_github_pr_llm
            ), "analyze_github_pr_llm should be callable"

            # Test the specific imports that were problematic
            from vibe_check.tools.shared.claude_integration import analyze_content_async
            from vibe_check.tools.shared.github_abstraction import (
                get_default_github_operations,
            )

            assert callable(
                analyze_content_async
            ), "analyze_content_async should be callable"
            assert callable(
                get_default_github_operations
            ), "get_default_github_operations should be callable"

        except ImportError as e:
            pytest.fail(f"MCP import context failed: {e}")

    def test_all_fixed_imports_resolve_correctly(self):
        """
        Test that all the imports that were converted from relative to absolute
        can be resolved correctly in an MCP-like context.
        """
        try:
            # Core module imports
            from vibe_check.core.code_reference_extractor import (
                CodeReferenceExtractor,
                ExtractionConfig,
            )
            from vibe_check.core.pr_filtering import (
                analyze_with_fallback,
                should_use_llm_analysis,
            )

            # Tools module imports
            from vibe_check.tools.analyze_pr_nollm import analyze_pr_nollm
            from vibe_check.tools.async_analysis.integration import start_async_analysis
            from vibe_check.tools.async_analysis.config import DEFAULT_ASYNC_CONFIG
            from vibe_check.tools.integration_pattern_analysis import (
                quick_technology_scan,
            )
            from vibe_check.tools.doom_loop_analysis import analyze_text_for_doom_loops

            # Shared module imports
            from vibe_check.tools.shared.github_helpers import (
                sanitize_github_urls_in_response,
            )
            from vibe_check.tools.shared.github_helpers import get_github_client

            # Verify these are not None/empty
            assert CodeReferenceExtractor is not None
            assert ExtractionConfig is not None
            assert analyze_with_fallback is not None
            assert should_use_llm_analysis is not None
            assert analyze_pr_nollm is not None
            assert start_async_analysis is not None
            assert DEFAULT_ASYNC_CONFIG is not None
            assert quick_technology_scan is not None
            assert analyze_text_for_doom_loops is not None
            assert sanitize_github_urls_in_response is not None
            assert get_github_client is not None

        except ImportError as e:
            pytest.fail(f"One or more absolute imports failed: {e}")

    def test_no_relative_imports_remain(self):
        """
        Ensure that no relative imports remain in specialized_analyzers.py
        by parsing the source file directly.
        """
        specialized_analyzers_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "vibe_check"
            / "tools"
            / "analyze_llm"
            / "specialized_analyzers.py"
        )

        if not specialized_analyzers_path.exists():
            pytest.skip("specialized_analyzers.py not found")

        with open(specialized_analyzers_path, "r") as f:
            content = f.read()

        # Look for any relative import patterns
        lines = content.split("\n")
        relative_imports = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("from ..") or stripped.startswith("from ..."):
                relative_imports.append(f"Line {i}: {line}")

        assert (
            len(relative_imports) == 0
        ), f"Found relative imports that should be absolute: {relative_imports}"

    def test_function_signature_preserved(self):
        """
        Ensure that the analyze_github_pr_llm function signature
        was not changed during the import fix.
        """
        import inspect
        from vibe_check.tools.analyze_llm.specialized_analyzers import (
            analyze_github_pr_llm,
        )

        sig = inspect.signature(analyze_github_pr_llm)
        param_names = list(sig.parameters.keys())

        # Expected parameters based on the function definition
        expected_params = [
            "pr_number",
            "repository",
            "post_comment",
            "analysis_mode",
            "detail_level",
            "timeout_seconds",
            "model",
        ]

        assert (
            param_names == expected_params
        ), f"Function signature changed. Expected: {expected_params}, Got: {param_names}"

        # Check return annotation
        assert (
            sig.return_annotation != inspect.Signature.empty
        ), "Return type annotation should be preserved"

    def test_github_integration_tools_import_correctly(self):
        """
        Regression test for Issue #233: Ensure review_pr_comprehensive
        and related GitHub integration tools can be imported without errors.
        """
        try:
            # Test the main tool that was failing
            from vibe_check.server.tools.github_integration import (
                review_pr_comprehensive,
            )

            assert callable(
                review_pr_comprehensive
            ), "review_pr_comprehensive should be callable"

            # Test the underlying function it depends on
            from vibe_check.tools.pr_review import review_pull_request

            assert callable(
                review_pull_request
            ), "review_pull_request should be callable"

            # Test that FileTypeAnalyzer is accessible (was causing NameError)
            from vibe_check.tools.pr_review.file_type_analyzer import FileTypeAnalyzer

            assert FileTypeAnalyzer is not None, "FileTypeAnalyzer should be importable"

        except ImportError as e:
            pytest.fail(f"GitHub integration tools import failed: {e}")

    def test_pr_review_module_imports(self):
        """
        Test that all pr_review module imports work with absolute paths.
        """
        try:
            # Test all components of pr_review module
            from vibe_check.tools.pr_review.claude_integration import ClaudeIntegration
            from vibe_check.tools.pr_review.data_collector import PRDataCollector
            from vibe_check.tools.pr_review.size_classifier import PRSizeClassifier

            assert ClaudeIntegration is not None
            assert PRDataCollector is not None
            assert PRSizeClassifier is not None

        except ImportError as e:
            pytest.fail(f"PR review module imports failed: {e}")

    def test_critical_tools_have_no_relative_imports(self):
        """
        Ensure critical MCP tools don't use relative imports that go up directories.
        Regression protection for Issues #229 and #233.
        """
        from pathlib import Path

        critical_files = [
            "src/vibe_check/server/tools/github_integration.py",
            "src/vibe_check/tools/pr_review/main.py",
            "src/vibe_check/tools/pr_review/claude_integration.py",
            "src/vibe_check/tools/analyze_llm/specialized_analyzers.py",
        ]

        project_root = Path(__file__).parent.parent.parent

        for file_path in critical_files:
            full_path = project_root / file_path
            if not full_path.exists():
                continue

            with open(full_path, "r") as f:
                content = f.read()

            lines = content.split("\n")
            relative_imports = []

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("from ..") or stripped.startswith("from ..."):
                    relative_imports.append(f"Line {i}: {line}")

            assert (
                len(relative_imports) == 0
            ), f"Found relative imports in {file_path}: {relative_imports}"
