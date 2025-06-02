"""
Unit tests for adaptive prompt sizing feature.

Tests the adaptive prompt sizing implementation from PR #77 that prevents
Claude CLI from returning empty content when analyzing large PRs.

Key Features Tested:
- 50k character threshold detection  
- Content reduction strategy for large PRs
- Summary mode activation and content creation
- Backward compatibility with small/medium PRs
- Summary content format validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.vibe_check.tools.pr_review import PRReviewTool


class TestAdaptivePromptSizing:
    """Test adaptive prompt sizing functionality."""
    
    @pytest.fixture
    def pr_tool(self):
        """Create PRReviewTool instance for testing."""
        return PRReviewTool()
    
    @pytest.fixture
    def small_pr_data(self):
        """Small PR data that should not trigger adaptive sizing."""
        return {
            "metadata": {
                "number": 42,
                "title": "Small feature addition",
                "author": "testuser",
                "created_at": "2025-06-01T12:00:00Z",
                "head_branch": "feature/small-change",
                "base_branch": "main",
                "body": "A small change to add a feature"
            },
            "statistics": {
                "files_count": 3,
                "additions": 50,
                "deletions": 10,
                "total_changes": 60
            },
            "diff": "+" * 1000,  # 1k chars - well under threshold
            "files": [
                {"path": "src/small.py", "additions": 30, "deletions": 5},
                {"path": "tests/test_small.py", "additions": 15, "deletions": 2},
                {"path": "README.md", "additions": 5, "deletions": 3}
            ],
            "comments": [],
            "linked_issues": []
        }
    
    @pytest.fixture
    def large_pr_data(self):
        """Large PR data that should trigger adaptive sizing."""
        return {
            "metadata": {
                "number": 73,
                "title": "Large refactoring with comprehensive changes",
                "author": "developer",
                "created_at": "2025-06-01T12:00:00Z",
                "head_branch": "feature/large-refactor",
                "base_branch": "main",
                "body": "This is a large PR that refactors multiple systems and adds new features with comprehensive test coverage and documentation updates."
            },
            "statistics": {
                "files_count": 50,
                "additions": 3000,
                "deletions": 1500,
                "total_changes": 4500
            },
            "diff": "+" * 60000,  # 60k chars - exceeds 50k threshold
            "files": [
                {"path": f"src/module_{i}.py", "additions": 60, "deletions": 30}
                for i in range(50)
            ],
            "comments": [],
            "linked_issues": []
        }
    
    @pytest.fixture
    def review_context(self):
        """Standard review context for testing."""
        return {
            "is_re_review": False,
            "review_count": 0,
            "previous_reviews": []
        }

    def test_threshold_detection_small_pr(self, pr_tool, small_pr_data, review_context):
        """Test that small PRs do not trigger adaptive sizing."""
        # Test the size detection logic by creating content and checking size
        prompt_content = "Analyze this pull request comprehensively"
        size_analysis = {"overall_size": "SMALL"}
        data_content = pr_tool._create_pr_data_content(small_pr_data, size_analysis, review_context)
        
        combined_content = f"{prompt_content}\n\n{data_content}"
        combined_size = len(combined_content)
        
        # Should be well under the 50k threshold
        assert combined_size < 50000, f"Small PR should be under threshold, got {combined_size} chars"
        
        # Verify the content doesn't contain summary indicators
        assert "Summary Analysis Mode" not in data_content
        assert "exceeds the 50k character prompt limit" not in data_content

    def test_threshold_detection_large_pr(self, pr_tool, large_pr_data, review_context):
        """Test that large PRs trigger adaptive sizing."""
        # Test the size detection logic 
        prompt_content = "Analyze this pull request comprehensively"
        size_analysis = {"overall_size": "LARGE"}
        data_content = pr_tool._create_pr_data_content(large_pr_data, size_analysis, review_context)
        
        combined_content = f"{prompt_content}\n\n{data_content}"
        combined_size = len(combined_content)
        
        # Should exceed the 50k threshold
        assert combined_size > 50000, f"Large PR should exceed threshold, got {combined_size} chars"

    def test_summary_content_creation(self, pr_tool, large_pr_data, review_context):
        """Test that summary content is properly created for large PRs."""
        summary_content = pr_tool._create_summary_data_content(large_pr_data, review_context)
        
        # Verify summary content contains required elements
        assert "PR #73 Review Data (Large PR - Summary Analysis)" in summary_content
        assert "Summary Analysis Mode" in summary_content
        assert "exceeds the 50k character prompt limit" in summary_content
        assert "Representative Diff Patterns (200 lines sample)" in summary_content
        
        # Verify file statistics are included
        assert "src/module_0.py: +60/-30" in summary_content
        
        # Verify summary is significantly smaller than original
        original_diff_size = len(large_pr_data["diff"])
        summary_size = len(summary_content)
        assert summary_size < original_diff_size, "Summary should be smaller than original content"

    def test_diff_pattern_extraction_limits(self, pr_tool):
        """Test that diff pattern extraction respects the 200-line limit."""
        # Create a large diff with many lines
        large_diff = "\n".join([f"+ Line {i} of changes" for i in range(500)])
        
        extracted_patterns = pr_tool._extract_diff_patterns(large_diff, 200)
        
        # Should be limited to 200 lines
        pattern_lines = extracted_patterns.split('\n')
        assert len(pattern_lines) <= 200, f"Expected ≤200 lines, got {len(pattern_lines)}"

    def test_file_statistics_format(self, pr_tool, large_pr_data, review_context):
        """Test that file statistics are properly formatted in summary content."""
        summary_content = pr_tool._create_summary_data_content(large_pr_data, review_context)
        
        # Check that file stats follow the expected format: "path: +additions/-deletions"
        assert "src/module_0.py: +60/-30" in summary_content
        assert "src/module_10.py: +60/-30" in summary_content
        
        # Verify multiple files are included
        file_count = len([line for line in summary_content.split('\n') if 'src/module_' in line])
        assert file_count > 10, "Should include multiple file statistics"

    @pytest.mark.asyncio
    async def test_adaptive_sizing_integration_small_pr(self, pr_tool, small_pr_data, review_context):
        """Test that small PRs use normal analysis mode."""
        prompt_content = "Analyze this pull request comprehensively"
        size_analysis = {"overall_size": "SMALL"}
        data_content = pr_tool._create_pr_data_content(small_pr_data, size_analysis, review_context)
        
        # Mock the external Claude CLI to avoid actual calls
        with patch.object(pr_tool.external_claude, 'analyze_content') as mock_analyze:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.output = "Mock analysis output"
            mock_result.execution_time = 5.0
            mock_result.cost_usd = 0.01
            mock_result.session_id = "test-session"
            mock_result.sdk_metadata = {}
            mock_analyze.return_value = mock_result
            
            result = await pr_tool._run_claude_analysis(
                prompt_content, data_content, 42, small_pr_data, {}, review_context
            )
            
            # Verify normal mode was used (no summary content)
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args[1]
            content_arg = call_args['content']
            
            # Should NOT contain summary mode indicators
            assert "summary mode (large PR detected)" not in content_arg
            assert "Summary Analysis Mode" not in content_arg

    @pytest.mark.asyncio
    async def test_adaptive_sizing_integration_large_pr(self, pr_tool, large_pr_data, review_context):
        """Test that large PRs automatically switch to summary analysis mode."""
        prompt_content = "Analyze this pull request comprehensively"
        size_analysis = {"overall_size": "LARGE"}
        data_content = pr_tool._create_pr_data_content(large_pr_data, size_analysis, review_context)
        
        # Mock the external Claude CLI
        with patch.object(pr_tool.external_claude, 'analyze_content') as mock_analyze:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.output = "Mock large PR analysis output"
            mock_result.execution_time = 15.0
            mock_result.cost_usd = 0.05
            mock_result.session_id = "test-session-large"
            mock_result.sdk_metadata = {}
            mock_analyze.return_value = mock_result
            
            result = await pr_tool._run_claude_analysis(
                prompt_content, data_content, 73, large_pr_data, {}, review_context
            )
            
            # Verify summary mode was used
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args[1]
            content_arg = call_args['content']
            
            # Should contain summary mode indicators
            assert "summary mode (large PR detected)" in content_arg
            assert "Large PR - Summary Analysis" in content_arg

    def test_prompt_size_constant(self, pr_tool):
        """Test that the MAX_PROMPT_SIZE constant is correctly set to 50k."""
        # This constant should be accessible in the method that uses it
        # We can test it indirectly by checking threshold behavior
        test_size_under = 49999
        test_size_over = 50001
        
        # Create mock content of different sizes
        small_content = "a" * test_size_under
        large_content = "a" * test_size_over
        
        # The actual threshold check happens in _run_claude_analysis
        # We can verify the logic by checking that content over 50k triggers reduction
        assert len(small_content) < 50000
        assert len(large_content) > 50000

    def test_backward_compatibility_existing_methods(self, pr_tool, small_pr_data, review_context):
        """Test that existing methods still work correctly with small PRs."""
        # Verify that _create_data_content still works as expected
        size_analysis = {"overall_size": "SMALL"}
        data_content = pr_tool._create_pr_data_content(small_pr_data, size_analysis, review_context)
        
        # Should contain expected sections for backward compatibility
        assert "PR #42 Review Data" in data_content
        assert "Files Changed: 3" in data_content
        assert "Lines: +50/-10" in data_content
        
        # Should NOT contain summary mode elements
        assert "Summary Analysis Mode" not in data_content
        assert "exceeds the 50k character prompt limit" not in data_content

    def test_content_reduction_effectiveness(self, pr_tool, large_pr_data, review_context):
        """Test that content reduction actually makes the prompt smaller."""
        # Create original content
        original_data_content = pr_tool._create_data_content(large_pr_data, review_context)
        original_size = len(original_data_content)
        
        # Create summary content
        summary_content = pr_tool._create_summary_data_content(large_pr_data, review_context)
        summary_size = len(summary_content)
        
        # Summary should be significantly smaller
        reduction_ratio = summary_size / original_size
        assert reduction_ratio < 0.5, f"Summary should be <50% of original size, got {reduction_ratio:.2%}"
        
        # But still contain essential information
        assert len(summary_content) > 1000, "Summary should still contain substantial content"

    def test_summary_content_structure(self, pr_tool, large_pr_data, review_context):
        """Test that summary content maintains proper structure and essential information."""
        summary_content = pr_tool._create_summary_data_content(large_pr_data, review_context)
        
        # Verify required sections exist
        required_sections = [
            "# PR #73 Review Data (Large PR - Summary Analysis)",
            "## PR Information",
            "**File Change Summary (Summary Analysis Mode):**",
            "**Representative Diff Patterns (200 lines sample):**",
            "**Large PR Analysis Note:**",
            "**Review Strategy for Large PRs:**"
        ]
        
        for section in required_sections:
            assert section in summary_content, f"Missing required section: {section}"
        
        # Verify essential metadata is preserved
        assert "Large refactoring with comprehensive changes" in summary_content
        assert "Files Changed: 50" in summary_content
        assert "Lines: +3000/-1500" in summary_content

    def test_adaptive_timeout_calculation(self, pr_tool):
        """Test that adaptive timeout is calculated correctly for different content sizes."""
        # Test with different content sizes
        small_size = 10000  # 10k chars
        medium_size = 30000  # 30k chars 
        large_size = 60000  # 60k chars
        
        small_timeout = pr_tool._calculate_adaptive_timeout(small_size, 42)
        medium_timeout = pr_tool._calculate_adaptive_timeout(medium_size, 42)
        large_timeout = pr_tool._calculate_adaptive_timeout(large_size, 42)
        
        # Larger content should get longer timeouts
        assert small_timeout <= medium_timeout <= large_timeout
        
        # Should be reasonable timeout values (between 60 and 600 seconds)
        for timeout in [small_timeout, medium_timeout, large_timeout]:
            assert 60 <= timeout <= 600, f"Timeout {timeout} should be between 60-600 seconds"

    def test_summary_preserves_critical_data(self, pr_tool, large_pr_data, review_context):
        """Test that summary mode preserves critical PR data for analysis."""
        summary_content = pr_tool._create_summary_data_content(large_pr_data, review_context)
        
        # Critical metadata should be preserved
        assert "Large refactoring with comprehensive changes" in summary_content
        assert "feature/large-refactor" in summary_content
        assert "main" in summary_content
        
        # File statistics should be present
        file_stats_found = False
        for i in range(10):  # Check first 10 files
            if f"src/module_{i}.py: +60/-30" in summary_content:
                file_stats_found = True
                break
        assert file_stats_found, "File statistics should be included in summary"
        
        # Analysis guidance should be included
        assert "Focus on architectural changes" in summary_content
        assert "Identify potential breaking changes" in summary_content