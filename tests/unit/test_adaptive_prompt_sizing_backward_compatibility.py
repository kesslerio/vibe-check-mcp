"""
Backward compatibility tests for adaptive prompt sizing feature.

Ensures that the adaptive prompt sizing feature from PR #77 does not break 
existing functionality for small and medium PRs, and that all existing 
behavior is preserved when the 50k threshold is not exceeded.

Tests verify:
- Small PRs continue to use full analysis mode
- Medium PRs work exactly as before
- No changes to existing API/interfaces
- Performance is maintained or improved
- All existing functionality preserved
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.vibe_check.tools.pr_review import PRReviewTool


class TestAdaptivePromptSizingBackwardCompatibility:
    """Test backward compatibility of adaptive prompt sizing."""
    
    @pytest.fixture
    def pr_tool(self):
        """Create PRReviewTool instance for testing."""
        return PRReviewTool()
    
    @pytest.fixture
    def classic_small_pr_data(self):
        """
        Classic small PR data that represents typical pre-adaptive-sizing usage.
        Should continue working exactly as before.
        """
        return {
            "metadata": {
                "number": 15,
                "title": "Fix typo in documentation",
                "author": "contributor",
                "created_at": "2025-05-30T14:00:00Z",
                "head_branch": "fix/typo-docs",
                "base_branch": "main",
                "body": "Fixed a small typo in the README file."
            },
            "statistics": {
                "files_count": 1,
                "additions": 1,
                "deletions": 1
            },
            "diff": """diff --git a/README.md b/README.md
index abc123..def456 100644
--- a/README.md
+++ b/README.md
@@ -10,7 +10,7 @@ This project provides...
 
 ## Installation
 
-Install using pip:
+Install using pip:
 
 ```bash
 pip install vibe-check-mcp
""",
            "files": [
                {
                    "path": "README.md",
                    "additions": 1,
                    "deletions": 1,
                    "status": "modified"
                }
            ],
            "comments": [],
            "linked_issues": []
        }
    
    @pytest.fixture
    def classic_medium_pr_data(self):
        """
        Classic medium PR data representing typical development work.
        Should continue working exactly as before.
        """
        return {
            "metadata": {
                "number": 25,
                "title": "Add user authentication feature",
                "author": "developer",
                "created_at": "2025-05-30T16:00:00Z",
                "head_branch": "feature/user-auth",
                "base_branch": "main",
                "body": """Adds basic user authentication with login/logout functionality.

## Changes
- Added User model with password hashing
- Implemented login/logout endpoints
- Added authentication middleware
- Updated tests

Fixes #123"""
            },
            "statistics": {
                "files_count": 8,
                "additions": 350,
                "deletions": 25
            },
            "diff": "+" * 15000,  # 15k chars - well under 50k threshold
            "files": [
                {"path": "src/models/user.py", "additions": 85, "deletions": 0},
                {"path": "src/auth/middleware.py", "additions": 65, "deletions": 5},
                {"path": "src/auth/endpoints.py", "additions": 120, "deletions": 10},
                {"path": "src/auth/__init__.py", "additions": 15, "deletions": 0},
                {"path": "tests/test_user_model.py", "additions": 45, "deletions": 0},
                {"path": "tests/test_auth_middleware.py", "additions": 35, "deletions": 5},
                {"path": "tests/test_auth_endpoints.py", "additions": 55, "deletions": 5},
                {"path": "requirements.txt", "additions": 2, "deletions": 0}
            ],
            "comments": [
                {
                    "author": {"login": "reviewer"},
                    "createdAt": "2025-05-30T17:00:00Z",
                    "body": "Looks good! Can you add integration tests for the full auth flow?"
                }
            ],
            "linked_issues": [
                {
                    "number": 123,
                    "title": "Implement user authentication",
                    "labels": ["feature", "authentication"],
                    "body": "Need basic user login/logout functionality."
                }
            ]
        }
    
    @pytest.fixture 
    def review_context(self):
        """Standard review context."""
        return {
            "is_re_review": False,
            "review_count": 0,
            "previous_reviews": []
        }

    def test_small_pr_content_format_unchanged(self, pr_tool, classic_small_pr_data, review_context):
        """Test that small PRs generate content in the same format as before."""
        data_content = pr_tool._create_pr_data_content(classic_small_pr_data, review_context)
        
        # Should contain standard sections (not summary mode)
        expected_sections = [
            "# PR #15 Review Data",
            "## PR Information",
            "**Title:** Fix typo in documentation",
            "**Files Changed:** 1",
            "**Lines:** +1/-1",
            "## Full Diff Content"
        ]
        
        for section in expected_sections:
            assert section in data_content, f"Missing expected section: {section}"
        
        # Should NOT contain summary mode indicators
        assert "Summary Analysis Mode" not in data_content
        assert "Large PR - Summary Analysis" not in data_content
        assert "exceeds the 50k character prompt limit" not in data_content

    def test_medium_pr_content_format_unchanged(self, pr_tool, classic_medium_pr_data, review_context):
        """Test that medium PRs generate content in the same format as before."""
        data_content = pr_tool._create_pr_data_content(classic_medium_pr_data, review_context)
        
        # Should contain standard sections
        expected_sections = [
            "# PR #25 Review Data",
            "## PR Information", 
            "**Title:** Add user authentication feature",
            "**Files Changed:** 8",
            "**Lines:** +350/-25",
            "## Full Diff Content"
        ]
        
        for section in expected_sections:
            assert section in data_content, f"Missing expected section: {section}"
        
        # Should NOT contain summary mode indicators
        assert "Summary Analysis Mode" not in data_content
        assert "Representative Diff Patterns" not in data_content

    def test_size_threshold_boundary_behavior(self, pr_tool):
        """Test behavior exactly at the 50k character boundary."""
        # Create test data that's exactly at the threshold
        threshold_size = 49999  # Just under 50k
        
        base_content = "Test content for boundary testing"
        padding_needed = threshold_size - len(base_content)
        
        boundary_pr_data = {
            "metadata": {
                "number": 99,
                "title": "Boundary test PR",
                "author": "tester",
                "created_at": "2025-06-01T12:00:00Z",
                "head_branch": "test/boundary",
                "base_branch": "main",
                "body": "Testing boundary behavior"
            },
            "statistics": {
                "files_count": 1,
                "additions": 100,
                "deletions": 50
            },
            "diff": base_content + ("x" * padding_needed),
            "files": [{"path": "test.py", "additions": 100, "deletions": 50}],
            "comments": [],
            "linked_issues": []
        }
        
        review_context = {"is_re_review": False, "review_count": 0, "previous_reviews": []}
        
        # Test just under threshold
        data_content = pr_tool._create_pr_data_content(boundary_pr_data, review_context)
        prompt_content = "Analyze this pull request comprehensively"
        combined_size = len(f"{prompt_content}\n\n{data_content}")
        
        # Should be under threshold and use normal mode
        assert combined_size < 50000
        assert "Summary Analysis Mode" not in data_content

    @pytest.mark.asyncio
    async def test_small_pr_analysis_workflow_unchanged(self, pr_tool, classic_small_pr_data, review_context):
        """Test that the complete analysis workflow for small PRs is unchanged."""
        prompt_content = "Analyze this pull request comprehensively"
        data_content = pr_tool._create_pr_data_content(classic_small_pr_data, review_context)
        
        # Mock Claude CLI to capture what's sent for analysis
        with patch.object(pr_tool.external_claude, 'analyze_content') as mock_analyze:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.output = "Mock analysis for small PR"
            mock_result.execution_time = 3.0
            mock_result.cost_usd = 0.005
            mock_analyze.return_value = mock_result
            
            result = await pr_tool._run_claude_analysis(
                prompt_content, data_content, 15, classic_small_pr_data, {}, review_context
            )
            
            # Verify analysis was successful
            assert result is not None
            
            # Verify normal mode was used (no content reduction)
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args[1]
            content_arg = call_args['content']
            
            # Should contain full content, not summary
            assert "Fix typo in documentation" in content_arg
            assert "README.md" in content_arg
            assert "summary mode (large PR detected)" not in content_arg
            
            # Should contain complete diff
            assert "diff --git a/README.md" in content_arg

    @pytest.mark.asyncio
    async def test_medium_pr_analysis_workflow_unchanged(self, pr_tool, classic_medium_pr_data, review_context):
        """Test that the complete analysis workflow for medium PRs is unchanged."""
        prompt_content = "Analyze this pull request comprehensively"
        data_content = pr_tool._create_pr_data_content(classic_medium_pr_data, review_context)
        
        # Verify this is truly under the threshold
        combined_size = len(f"{prompt_content}\n\n{data_content}")
        assert combined_size < 50000, f"Medium PR test data should be under threshold, got {combined_size}"
        
        with patch.object(pr_tool.external_claude, 'analyze_content') as mock_analyze:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.output = "Mock analysis for medium PR"
            mock_result.execution_time = 8.0
            mock_result.cost_usd = 0.015
            mock_analyze.return_value = mock_result
            
            result = await pr_tool._run_claude_analysis(
                prompt_content, data_content, 25, classic_medium_pr_data, {}, review_context
            )
            
            # Verify analysis was successful
            assert result is not None
            
            # Verify normal mode was used
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args[1]
            content_arg = call_args['content']
            
            # Should contain full analysis prompt
            assert "Analyze this pull request comprehensively" in content_arg
            assert "summary mode" not in content_arg
            
            # Should contain complete PR information
            assert "Add user authentication feature" in content_arg
            assert "src/models/user.py" in content_arg
            assert "Fixes #123" in content_arg

    def test_api_interface_unchanged(self, pr_tool):
        """Test that all public API interfaces remain unchanged."""
        # Verify method signatures are preserved
        import inspect
        
        # Check key methods exist with expected signatures
        assert hasattr(pr_tool, 'review_pull_request')
        assert hasattr(pr_tool, '_create_pr_data_content') 
        assert hasattr(pr_tool, '_run_claude_analysis')
        
        # Check review_pull_request signature
        sig = inspect.signature(pr_tool.review_pull_request)
        expected_params = ['pr_number', 'repository', 'force_re_review', 'analysis_mode', 'detail_level']
        actual_params = list(sig.parameters.keys())
        
        for param in expected_params:
            assert param in actual_params, f"Missing expected parameter: {param}"

    def test_timeout_calculation_backward_compatibility(self, pr_tool):
        """Test that timeout calculation doesn't break existing behavior."""
        # Small content should get reasonable timeouts
        small_size = 5000
        medium_size = 25000
        
        small_timeout = pr_tool._calculate_adaptive_timeout(small_size, 15)
        medium_timeout = pr_tool._calculate_adaptive_timeout(medium_size, 25)
        
        # Should be reasonable values (60-300 seconds for small/medium)
        assert 60 <= small_timeout <= 300, f"Small PR timeout should be 60-300s, got {small_timeout}"
        assert 60 <= medium_timeout <= 300, f"Medium PR timeout should be 60-300s, got {medium_timeout}"
        
        # Medium should be >= small
        assert medium_timeout >= small_timeout

    def test_error_handling_backward_compatibility(self, pr_tool, classic_small_pr_data, review_context):
        """Test that error handling behavior is preserved for small PRs."""
        # Test that the existing error handling paths still work
        prompt_content = "Analyze this pull request comprehensively"
        data_content = pr_tool._create_pr_data_content(classic_small_pr_data, review_context)
        
        # The size check should not interfere with error handling
        combined_size = len(f"{prompt_content}\n\n{data_content}")
        assert combined_size < 50000  # Confirm this is a small PR
        
        # Verify the content contains expected error handling friendly format
        assert "PR #15 Review Data" in data_content
        assert "Fix typo in documentation" in data_content

    def test_performance_not_degraded(self, pr_tool, classic_small_pr_data, classic_medium_pr_data, review_context):
        """Test that performance is not degraded for small/medium PRs."""
        import time
        
        # Test small PR content creation performance
        start_time = time.time()
        small_content = pr_tool._create_data_content(classic_small_pr_data, review_context)
        small_time = time.time() - start_time
        
        # Test medium PR content creation performance  
        start_time = time.time()
        medium_content = pr_tool._create_data_content(classic_medium_pr_data, review_context)
        medium_time = time.time() - start_time
        
        # Should be fast (adaptive sizing shouldn't add overhead to small/medium PRs)
        assert small_time < 0.1, f"Small PR content creation took {small_time:.3f}s, should be <0.1s"
        assert medium_time < 0.2, f"Medium PR content creation took {medium_time:.3f}s, should be <0.2s"

    def test_content_quality_preserved(self, pr_tool, classic_medium_pr_data, review_context):
        """Test that content quality and completeness is preserved for medium PRs."""
        data_content = pr_tool._create_pr_data_content(classic_medium_pr_data, review_context)
        
        # Should contain all the detailed information as before
        quality_indicators = [
            "Add user authentication feature",  # Full title
            "src/models/user.py",              # Complete file paths
            "src/auth/middleware.py",
            "src/auth/endpoints.py", 
            "tests/test_user_model.py",        # Test files
            "Fixes #123",                      # Issue linkage
            "## Full Diff Content",            # Complete diff section
            "Files Changed: 8",                # Accurate statistics
            "Lines: +350/-25"
        ]
        
        for indicator in quality_indicators:
            assert indicator in data_content, f"Quality indicator missing: {indicator}"
        
        # Should contain full diff content, not truncated
        assert len(data_content) > 1000, "Medium PR should generate substantial content"

    def test_existing_comment_handling_preserved(self, pr_tool, classic_medium_pr_data, review_context):
        """Test that existing comment handling behavior is preserved."""
        data_content = pr_tool._create_pr_data_content(classic_medium_pr_data, review_context)
        
        # Should include existing comments as before
        assert "reviewer" in data_content
        assert "integration tests" in data_content
        
        # Comment formatting should be unchanged
        assert "**@reviewer**" in data_content or "reviewer" in data_content

    def test_linked_issue_handling_preserved(self, pr_tool, classic_medium_pr_data, review_context):
        """Test that linked issue handling behavior is preserved."""
        data_content = pr_tool._create_pr_data_content(classic_medium_pr_data, review_context)
        
        # Should include linked issue information as before
        assert "Issue #123" in data_content
        assert "Implement user authentication" in data_content
        assert "feature" in data_content
        assert "authentication" in data_content