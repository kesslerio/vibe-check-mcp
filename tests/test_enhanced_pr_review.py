"""
Test Enhanced PR Review Features

Tests for the enhanced PR review tool with file type analysis,
author awareness, and model selection capabilities.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from vibe_check.tools.pr_review.main import review_pull_request
from vibe_check.tools.pr_review.file_type_analyzer import FileTypeAnalyzer


class TestEnhancedPRReview:
    """Test suite for enhanced PR review features."""

    @pytest.mark.asyncio
    async def test_file_type_analysis(self):
        """Test that file type analysis correctly categorizes files."""
        analyzer = FileTypeAnalyzer()

        test_files = [
            {"filename": "src/components/Button.tsx"},
            {"filename": "src/api/routes.py"},
            {"filename": "tests/test_button.spec.ts"},
            {"filename": "src/utils/helpers.js"},
            {"filename": "config/database.json"},
            {"filename": "migrations/001_init.sql"},
        ]

        result = analyzer.analyze_files(test_files)

        assert "typescript" in result["type_specific_analysis"]
        assert "react" in result["type_specific_analysis"]
        assert "api" in result["type_specific_analysis"]
        assert "test" in result["type_specific_analysis"]
        assert "config" in result["type_specific_analysis"]
        assert "sql" in result["type_specific_analysis"]

        # Check priority security checks
        assert len(result["priority_checks"]) > 0
        priority_types = [check["type"] for check in result["priority_checks"]]
        assert "api" in priority_types
        assert "config" in priority_types
        assert "sql" in priority_types

    @pytest.mark.asyncio
    async def test_model_parameter_support(self):
        """Test that model parameter is properly passed through the system."""
        with patch(
            "src.vibe_check.tools.pr_review.main.PRDataCollector"
        ) as mock_collector, patch(
            "src.vibe_check.tools.pr_review.main.ClaudeIntegration"
        ) as mock_claude:

            # Setup mocks
            mock_collector_instance = Mock()
            mock_collector_instance.collect_pr_data.return_value = {
                "metadata": {"author_association": "FIRST_TIME_CONTRIBUTOR"},
                "files": [],
                "statistics": {"files_count": 1, "additions": 10, "deletions": 5},
            }
            mock_collector.return_value = mock_collector_instance

            mock_claude_instance = Mock()
            mock_claude_instance.check_claude_availability.return_value = False
            mock_claude.return_value = mock_claude_instance

            # Test with opus model
            result = await review_pull_request(pr_number=123, model="opus")

            assert result["model_used"] == "opus"

    @pytest.mark.asyncio
    async def test_first_time_contributor_detection(self):
        """Test that first-time contributors are properly detected."""
        with patch(
            "src.vibe_check.tools.pr_review.main.PRDataCollector"
        ) as mock_collector, patch(
            "src.vibe_check.tools.pr_review.main.ClaudeIntegration"
        ) as mock_claude:

            # Setup mocks for first-time contributor
            mock_collector_instance = Mock()
            mock_collector_instance.collect_pr_data.return_value = {
                "metadata": {
                    "author": "newcontributor",
                    "author_association": "FIRST_TIME_CONTRIBUTOR",
                    "title": "Fix typo in README",
                },
                "files": [{"filename": "README.md"}],
                "statistics": {"files_count": 1, "additions": 1, "deletions": 1},
            }
            mock_collector.return_value = mock_collector_instance

            mock_claude_instance = Mock()
            mock_claude_instance.check_claude_availability.return_value = True
            mock_claude_instance.run_claude_analysis = AsyncMock(
                return_value={
                    "analysis": "Welcome to the project!",
                    "recommendation": "APPROVE",
                }
            )
            mock_claude.return_value = mock_claude_instance

            result = await review_pull_request(pr_number=456, model="sonnet")

            # Verify the prompt included first-time contributor context
            calls = mock_claude_instance.run_claude_analysis.call_args_list
            assert len(calls) > 0
            call_kwargs = calls[0][1]
            prompt = call_kwargs.get("prompt_content", "")

            # Should include encouraging context for first-time contributors
            assert "FIRST-TIME CONTRIBUTOR" in prompt or "encouraging" in prompt.lower()

    def test_file_type_prompt_generation(self):
        """Test that file type analysis generates appropriate prompts."""
        analyzer = FileTypeAnalyzer()

        test_analysis = {
            "type_specific_analysis": {
                "typescript": {
                    "files": ["src/app.ts", "src/types.ts"],
                    "count": 2,
                    "focus_areas": ["Type safety", "Interface usage"],
                    "common_issues": ["Missing types", "Any usage"],
                },
                "api": {
                    "files": ["src/api/routes.py"],
                    "count": 1,
                    "focus_areas": ["Security", "Input validation"],
                    "common_issues": ["SQL injection", "Missing auth"],
                },
            },
            "priority_checks": [
                {
                    "type": "api",
                    "reason": "Security-sensitive file type",
                    "files": ["src/api/routes.py"],
                }
            ],
        }

        prompt = analyzer.generate_file_type_prompt(test_analysis)

        assert "TYPESCRIPT" in prompt
        assert "API" in prompt
        assert "Type safety" in prompt
        assert "Security" in prompt
        assert "Priority Security Checks" in prompt

    def test_review_guidelines_completeness(self):
        """Test that all major file types have review guidelines."""
        analyzer = FileTypeAnalyzer()

        expected_types = [
            "typescript",
            "javascript",
            "python",
            "api",
            "react",
            "test",
            "config",
            "sql",
        ]

        for file_type in expected_types:
            assert file_type in analyzer.REVIEW_GUIDELINES
            guidelines = analyzer.REVIEW_GUIDELINES[file_type]
            assert "focus_areas" in guidelines
            assert "common_issues" in guidelines
            assert len(guidelines["focus_areas"]) > 0
            assert len(guidelines["common_issues"]) > 0

    def test_file_type_detection_edge_cases(self):
        """Test file type detection with edge cases."""
        analyzer = FileTypeAnalyzer()

        # Test edge cases
        assert analyzer._detect_file_type("file.") == "other"  # Empty extension
        assert analyzer._detect_file_type("file") == "other"  # No extension
        assert (
            analyzer._detect_file_type("file.unknown") == "other"
        )  # Unknown extension
        assert analyzer._detect_file_type("test.spec.js") == "test"  # Multiple dots
        assert (
            analyzer._detect_file_type("src/api/routes.py") == "api"
        )  # Path-based detection

    @pytest.mark.asyncio
    async def test_claude_integration_error_handling(self):
        """Test Claude integration error handling."""
        with patch(
            "vibe_check.tools.pr_review.claude_integration.ClaudeCliExecutor"
        ) as mock_executor:
            # Setup mock to simulate failure
            mock_instance = Mock()
            mock_instance.claude_cli_path = "claude"
            mock_instance.timeout_seconds = 60
            mock_executor.return_value = mock_instance

            from vibe_check.tools.pr_review.claude_integration import ClaudeIntegration

            integration = ClaudeIntegration()

            # Test timeout scenario
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = Mock()
                mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
                mock_process.kill = Mock()
                mock_process.wait = AsyncMock()
                mock_subprocess.return_value = mock_process

                result = await integration._execute_with_model(
                    "test prompt", "pr_review", "sonnet"
                )

                assert not result.success
                assert "timed out" in result.error
                assert result.exit_code == -1

    def test_security_priority_detection(self):
        """Test that security-sensitive files are properly prioritized."""
        analyzer = FileTypeAnalyzer()

        security_files = [
            {"filename": "src/api/auth.py"},
            {"filename": "config/database.json"},
            {"filename": "migrations/create_users.sql"},
            {"filename": ".env"},
            {"filename": "secrets.yaml"},
        ]

        result = analyzer.analyze_files(security_files)

        # Should have priority checks for security-sensitive files
        assert len(result["priority_checks"]) > 0

        priority_types = [check["type"] for check in result["priority_checks"]]
        assert "api" in priority_types
        assert "config" in priority_types
        assert "sql" in priority_types

    def test_missing_filename_key_handling(self):
        """Test that analyzer handles missing 'filename' key gracefully."""
        analyzer = FileTypeAnalyzer()

        # Test files with various key configurations
        test_files = [
            {"filename": "src/components/Button.tsx"},  # Normal case
            {"name": "src/api/routes.py"},  # Uses 'name' instead of 'filename'
            {"path": "tests/test_button.spec.ts"},  # Neither 'filename' nor 'name'
            {},  # Empty dict
            {
                "filename": "config/database.json",
                "name": "db.json",
            },  # Both keys (filename takes precedence)
        ]

        # Should not raise KeyError
        result = analyzer.analyze_files(test_files)

        # Verify the analysis completed successfully
        assert "type_specific_analysis" in result
        assert "review_focus_summary" in result
        assert "priority_checks" in result

        # Check that files were processed with appropriate fallbacks
        all_files = []
        for file_type_data in result["type_specific_analysis"].values():
            all_files.extend(file_type_data["files"])

        # Should have processed all files with appropriate names
        assert "src/components/Button.tsx" in all_files  # Normal filename
        assert "src/api/routes.py" in all_files  # Used 'name' fallback
        assert "unknown" in all_files  # Used 'unknown' fallback for missing keys
        assert "config/database.json" in all_files  # Used 'filename' when both present

        # Verify priority checks also handle missing keys gracefully
        for check in result["priority_checks"]:
            assert isinstance(check["files"], list)
            for filename in check["files"]:
                assert isinstance(filename, str)  # All filenames should be strings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
