"""
Unit tests for PR review external Claude CLI integration.

Tests the integration of external Claude CLI with PR review functionality including:
- PR review tool initialization with external Claude CLI
- Async method conversion validation
- External Claude CLI availability checking
- Analysis execution and result parsing
- SDK metadata integration and cost tracking
- Error handling and fallback behavior
"""

import asyncio
import json
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime
from pathlib import Path

import pytest

# Import the classes under test
from vibe_check.tools.legacy.review_pr_monolithic_backup import PRReviewTool
from vibe_check.tools.analyze_llm_backup import ExternalClaudeCli, ClaudeCliResult


class TestPRReviewExternalClaude:
    """Test suite for PR review external Claude CLI integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pr_tool = PRReviewTool()
        
        # Mock PR data for testing
        self.mock_pr_data = {
            "metadata": {
                "number": 42,
                "title": "Test PR",
                "body": "Test PR description\nFixes #123",
                "author": "testuser",
                "created_at": "2023-01-01T00:00:00Z",
                "base_branch": "main",
                "head_branch": "feature/test"
            },
            "statistics": {
                "files_count": 3,
                "additions": 150,
                "deletions": 50,
                "total_changes": 200
            },
            "files": [
                {"path": "src/test.py", "additions": 100, "deletions": 25},
                {"path": "tests/test_test.py", "additions": 50, "deletions": 25}
            ],
            "diff": "diff --git a/src/test.py b/src/test.py\n+new code here",
            "comments": [],
            "linked_issues": [
                {
                    "number": 123,
                    "action": "Fixes",
                    "title": "Test issue",
                    "body": "Issue description",
                    "labels": ["bug", "P1"],
                    "state": "open"
                }
            ]
        }

    def test_pr_tool_initialization(self):
        """Test that PRReviewTool initializes with external Claude CLI."""
        assert hasattr(self.pr_tool, 'external_claude')
        assert isinstance(self.pr_tool.external_claude, ExternalClaudeCli)
        assert self.pr_tool.external_claude.timeout_seconds == 300  # 5 min timeout

    def test_pr_tool_directories_creation(self):
        """Test that review directories are created."""
        assert self.pr_tool.reviews_dir.exists()
        assert self.pr_tool.reviews_dir.name == "pr-reviews"

    def test_size_classification_small_pr(self):
        """Test PR size classification for small PR."""
        # Small PR data
        small_pr_data = self.mock_pr_data.copy()
        small_pr_data["statistics"]["total_changes"] = 100
        small_pr_data["statistics"]["files_count"] = 2
        
        size_analysis = self.pr_tool._classify_pr_size(small_pr_data)
        
        assert size_analysis["size_by_lines"] == "SMALL"
        assert size_analysis["size_by_files"] == "SMALL"
        assert size_analysis["overall_size"] == "SMALL"
        assert size_analysis["review_strategy"] == "FULL_ANALYSIS"

    def test_size_classification_large_pr(self):
        """Test PR size classification for large PR."""
        # Large PR data
        large_pr_data = self.mock_pr_data.copy()
        large_pr_data["statistics"]["total_changes"] = 3000
        large_pr_data["statistics"]["files_count"] = 15
        
        size_analysis = self.pr_tool._classify_pr_size(large_pr_data)
        
        assert size_analysis["overall_size"] == "LARGE"
        assert size_analysis["review_strategy"] == "SUMMARY_ANALYSIS"

    def test_size_classification_test_pr_lenient(self):
        """Test that test PRs get more lenient size classification."""
        # Test PR data with large diff but mostly test files
        test_pr_data = self.mock_pr_data.copy()
        test_pr_data["files"] = [
            {"path": "tests/test_large.py", "additions": 1000, "deletions": 0},
            {"path": "tests/test_another.py", "additions": 500, "deletions": 0}
        ]
        test_pr_data["diff"] = "x" * 150000  # 150k chars (would be LARGE for normal PRs)
        
        size_analysis = self.pr_tool._classify_pr_size(test_pr_data)
        
        # Should get more lenient treatment for test files
        assert size_analysis["size_by_chars"] in ["SMALL", "LARGE"]  # Not VERY_LARGE

    def test_detect_re_review_no_previous(self):
        """Test re-review detection with no previous reviews."""
        review_context = self.pr_tool._detect_re_review(self.mock_pr_data, False)
        
        assert review_context["is_re_review"] is False
        assert review_context["review_count"] == 0
        assert review_context["previous_reviews"] == []

    def test_detect_re_review_with_previous(self):
        """Test re-review detection with previous automated reviews."""
        pr_data_with_comments = self.mock_pr_data.copy()
        pr_data_with_comments["comments"] = [
            {
                "body": "## 🎯 Overview\nAutomated PR Review results...",
                "author": {"login": "bot"}
            }
        ]
        
        review_context = self.pr_tool._detect_re_review(pr_data_with_comments, False)
        
        assert review_context["is_re_review"] is True
        assert review_context["review_count"] == 1

    def test_detect_re_review_forced(self):
        """Test forced re-review mode."""
        review_context = self.pr_tool._detect_re_review(self.mock_pr_data, True)
        
        assert review_context["is_re_review"] is True

    def test_check_claude_availability_docker_environment(self):
        """Test Claude availability check in Docker environment."""
        with patch('os.path.exists', return_value=True):  # Simulate /.dockerenv exists
            result = self.pr_tool._check_claude_availability()
            assert result is False

    def test_check_claude_availability_docker_env_var(self):
        """Test Claude availability check with Docker environment variable."""
        with patch('os.environ.get', return_value="true"):  # RUNNING_IN_DOCKER=true
            result = self.pr_tool._check_claude_availability()
            assert result is False

    @patch('subprocess.run')
    def test_check_claude_availability_success(self, mock_run):
        """Test successful Claude availability check."""
        # Mock environment checks
        with patch('os.path.exists', return_value=False):
            with patch('os.environ.get', return_value=None):
                # Mock external Claude CLI finding claude
                with patch.object(self.pr_tool.external_claude, '_find_claude_cli', return_value="/usr/local/bin/claude"):
                    result = self.pr_tool._check_claude_availability()
                    assert result is True

    @patch('subprocess.run')
    def test_check_claude_availability_default_command(self, mock_run):
        """Test Claude availability check with default command."""
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('os.path.exists', return_value=False):
            with patch('os.environ.get', return_value=None):
                with patch.object(self.pr_tool.external_claude, '_find_claude_cli', return_value="claude"):
                    result = self.pr_tool._check_claude_availability()
                    assert result is True

    def test_adaptive_timeout_calculation(self):
        """Test adaptive timeout calculation based on content size."""
        # Small content
        timeout = self.pr_tool._calculate_adaptive_timeout(5000, 42)
        assert timeout == 60  # Should use base timeout

        # Medium content
        timeout = self.pr_tool._calculate_adaptive_timeout(20000, 42)
        assert timeout == 60

        # Large content
        timeout = self.pr_tool._calculate_adaptive_timeout(50000, 42)
        assert timeout == 90

        # Very large content
        timeout = self.pr_tool._calculate_adaptive_timeout(150000, 42)
        assert timeout == 120

        # Massive content
        timeout = self.pr_tool._calculate_adaptive_timeout(250000, 42)
        assert timeout == 180

    @pytest.mark.asyncio
    async def test_run_claude_analysis_success(self):
        """Test successful Claude analysis execution."""
        mock_result = ClaudeCliResult(
            success=True,
            output="Comprehensive PR analysis result",
            cost_usd=0.25,
            duration_ms=2500,
            session_id="test-session-456",
            num_turns=1,
            execution_time=27.5,
            task_type="pr_review",
            sdk_metadata={"model": "claude-3-sonnet", "provider": "anthropic"}
        )

        with patch.object(self.pr_tool.external_claude, 'analyze_content', return_value=mock_result):
            result = await self.pr_tool._run_claude_analysis(
                prompt_content="Test prompt",
                data_content="Test data",
                pr_number=42
            )

        assert result is not None
        assert result["claude_analysis"] == "Comprehensive PR analysis result"
        assert result["analysis_method"] == "external-claude-cli"
        assert result["cost_usd"] == 0.25
        assert result["session_id"] == "test-session-456"
        assert result["execution_time"] == 27.5

    @pytest.mark.asyncio
    async def test_run_claude_analysis_failure(self):
        """Test Claude analysis execution failure."""
        mock_result = ClaudeCliResult(
            success=False,
            error="Claude CLI execution failed",
            exit_code=1,
            execution_time=5.0,
            task_type="pr_review"
        )

        with patch.object(self.pr_tool.external_claude, 'analyze_content', return_value=mock_result):
            result = await self.pr_tool._run_claude_analysis(
                prompt_content="Test prompt",
                data_content="Test data",
                pr_number=42
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_run_claude_analysis_short_output(self):
        """Test Claude analysis with unexpectedly short output."""
        mock_result = ClaudeCliResult(
            success=True,
            output="OK",  # Very short output
            execution_time=1.0,
            task_type="pr_review"
        )

        with patch.object(self.pr_tool.external_claude, 'analyze_content', return_value=mock_result):
            result = await self.pr_tool._run_claude_analysis(
                prompt_content="Test prompt",
                data_content="Test data",
                pr_number=42
            )

        assert result is None  # Should reject short output

    @pytest.mark.asyncio
    async def test_run_claude_analysis_exception(self):
        """Test Claude analysis with exception."""
        with patch.object(self.pr_tool.external_claude, 'analyze_content', side_effect=Exception("Network error")):
            result = await self.pr_tool._run_claude_analysis(
                prompt_content="Test prompt",
                data_content="Test data",
                pr_number=42
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_comprehensive_analysis_with_claude(self):
        """Test comprehensive analysis generation using Claude."""
        size_analysis = {
            "overall_size": "MEDIUM",
            "review_strategy": "FULL_ANALYSIS"
        }
        review_context = {"is_re_review": False, "review_count": 0}

        mock_claude_result = ClaudeCliResult(
            success=True,
            output="Detailed PR analysis with recommendations",
            cost_usd=0.30,
            execution_time=25.0,
            task_type="pr_review"
        )

        with patch.object(self.pr_tool, '_check_claude_availability', return_value=True):
            with patch.object(self.pr_tool.external_claude, 'analyze_content', return_value=mock_claude_result):
                result = await self.pr_tool._generate_comprehensive_analysis(
                    self.mock_pr_data,
                    size_analysis,
                    review_context,
                    "comprehensive",
                    "standard"
                )

        assert result["claude_analysis"] == "Detailed PR analysis with recommendations"
        assert result["analysis_method"] == "external-claude-cli"
        assert result["cost_usd"] == 0.30

    @pytest.mark.asyncio
    async def test_generate_comprehensive_analysis_fallback(self):
        """Test comprehensive analysis with fallback when Claude unavailable."""
        size_analysis = {
            "overall_size": "MEDIUM",
            "review_strategy": "FULL_ANALYSIS"
        }
        review_context = {"is_re_review": False, "review_count": 0}

        with patch.object(self.pr_tool, '_check_claude_availability', return_value=False):
            result = await self.pr_tool._generate_comprehensive_analysis(
                self.mock_pr_data,
                size_analysis,
                review_context,
                "comprehensive",
                "standard"
            )

        assert result["analysis_method"] == "fallback"
        assert "clear_thought_summary" in result

    def test_create_comprehensive_prompt(self):
        """Test comprehensive prompt creation."""
        size_analysis = {"overall_size": "MEDIUM"}
        review_context = {"is_re_review": False, "review_count": 0}

        prompt = self.pr_tool._create_comprehensive_prompt(
            self.mock_pr_data,
            size_analysis,
            review_context,
            "standard"
        )

        assert "expert code reviewer" in prompt.lower()
        assert "anti-pattern detection" in prompt.lower()
        assert "mcp github tools" in prompt.lower()
        assert "clear-thought" in prompt.lower()
        assert str(self.mock_pr_data["statistics"]["additions"]) in prompt
        assert str(self.mock_pr_data["statistics"]["deletions"]) in prompt

    def test_create_pr_data_content_standard(self):
        """Test PR data content creation for standard PR."""
        size_analysis = {"overall_size": "SMALL"}
        review_context = {"is_re_review": False, "review_count": 0}

        content = self.pr_tool._create_pr_data_content(
            self.mock_pr_data,
            size_analysis,
            review_context
        )

        assert f"PR #{self.mock_pr_data['metadata']['number']}" in content
        assert self.mock_pr_data["metadata"]["title"] in content
        assert self.mock_pr_data["metadata"]["author"] in content
        assert "Complete Diff:" in content

    def test_create_pr_data_content_large(self):
        """Test PR data content creation for large PR."""
        size_analysis = {"overall_size": "LARGE"}
        review_context = {"is_re_review": False, "review_count": 0}
        
        # Create large PR data
        large_pr_data = self.mock_pr_data.copy()
        large_pr_data["diff"] = "x" * 60000  # 60k chars

        content = self.pr_tool._create_pr_data_content(
            large_pr_data,
            size_analysis,
            review_context
        )

        assert "Large PR - Summary Analysis" in content
        assert "Key Diff Patterns" in content

    def test_create_pr_data_content_very_large(self):
        """Test PR data content creation for very large PR."""
        size_analysis = {"overall_size": "VERY_LARGE"}
        review_context = {"is_re_review": False, "review_count": 0}
        
        # Create very large PR data
        very_large_pr_data = self.mock_pr_data.copy()
        very_large_pr_data["statistics"]["total_changes"] = 15000

        content = self.pr_tool._create_pr_data_content(
            very_large_pr_data,
            size_analysis,
            review_context
        )

        assert "Very Large PR - File Summary Analysis" in content
        assert "Sample Code Changes" in content

    def test_parse_claude_output(self):
        """Test Claude output parsing."""
        claude_output = "Detailed analysis with recommendations"
        
        result = self.pr_tool._parse_claude_output(claude_output, 42)
        
        assert result["claude_analysis"] == claude_output
        assert result["analysis_method"] == "claude-cli"
        assert result["pr_number"] == 42
        assert "timestamp" in result

    def test_fallback_analysis_generation(self):
        """Test fallback analysis generation."""
        size_analysis = {"overall_size": "MEDIUM"}
        review_context = {"is_re_review": False, "review_count": 0}

        result = self.pr_tool._generate_fallback_analysis(
            self.mock_pr_data,
            size_analysis,
            review_context
        )

        assert result["analysis_method"] == "fallback"
        assert result["pr_number"] == 42
        assert "issue_linkage" in result
        assert "strengths" in result
        assert "critical_issues" in result
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_full_review_pull_request_workflow(self):
        """Test the complete review_pull_request workflow."""
        # Mock all the subprocess calls for PR data collection
        mock_pr_result = MagicMock()
        mock_pr_result.stdout = json.dumps({
            "title": "Test PR",
            "body": "Test description\nFixes #123",
            "author": {"login": "testuser"},
            "createdAt": "2023-01-01T00:00:00Z",
            "baseRefName": "main",
            "headRefName": "feature/test",
            "additions": 100,
            "deletions": 50,
            "files": []
        })

        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 0
        mock_diff_result.stdout = "diff --git a/test.py"

        mock_comment_result = MagicMock()
        mock_comment_result.stdout = "Comment posted"

        with patch('subprocess.run', side_effect=[mock_pr_result, mock_diff_result, mock_comment_result]):
            with patch.object(self.pr_tool, '_check_claude_availability', return_value=False):
                result = await self.pr_tool.review_pull_request(
                    pr_number=42,
                    repository="test/repo",
                    analysis_mode="comprehensive"
                )

        assert result["pr_number"] == 42
        assert "analysis" in result
        assert "github_integration" in result
        assert "logging" in result

    def test_save_permanent_log(self):
        """Test permanent log saving."""
        analysis = {"test": "data"}
        review_context = {"is_re_review": False}

        with patch('builtins.open', mock_open()) as mock_file:
            result = self.pr_tool._save_permanent_log(42, analysis, review_context)

        assert result["log_saved"] is True
        assert "pr-42-review-" in result["log_file"]
        mock_file.assert_called_once()

    def test_save_permanent_log_error(self):
        """Test permanent log saving with error."""
        analysis = {"test": "data"}
        review_context = {"is_re_review": False}

        with patch('builtins.open', side_effect=Exception("Write error")):
            result = self.pr_tool._save_permanent_log(42, analysis, review_context)

        assert "error" in result
        assert "Write error" in result["error"]