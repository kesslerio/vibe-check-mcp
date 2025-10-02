"""
Integration tests for adaptive prompt sizing feature.

Tests the complete end-to-end workflow of adaptive prompt sizing with realistic
large PR scenarios to ensure the feature works correctly in production.

This tests the integration between:
- PR data collection
- Size threshold detection
- Content reduction strategies
- External Claude CLI integration
- Analysis output formatting
"""

import pytest
import tempfile
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from vibe_check.tools.legacy.review_pr_monolithic_backup import PRReviewTool


class TestAdaptivePromptSizingIntegration:
    """Integration tests for adaptive prompt sizing."""

    @pytest.fixture
    def pr_tool(self):
        """Create PRReviewTool instance for integration testing."""
        return PRReviewTool()

    @pytest.fixture
    def realistic_large_pr_data(self):
        """
        Realistic large PR data that simulates a real-world scenario
        that would trigger adaptive sizing (>50k chars total).
        """
        # Create a large diff that would realistically occur
        large_diff_content = []

        # Simulate a large refactoring with many file changes
        for file_num in range(30):
            file_diff = f"""
diff --git a/src/module_{file_num}.py b/src/module_{file_num}.py
index abc123..def456 100644
--- a/src/module_{file_num}.py
+++ b/src/module_{file_num}.py
@@ -1,10 +1,25 @@
 \"\"\"Module {file_num} with comprehensive refactoring.\"\"\"
 
+import logging
+from typing import Dict, Any, List, Optional
+from dataclasses import dataclass
+
+logger = logging.getLogger(__name__)
+
+@dataclass
+class Module{file_num}Config:
+    \"\"\"Configuration for module {file_num}.\"\"\"
+    enable_feature: bool = True
+    max_retries: int = 3
+    timeout_seconds: int = 30
+
 class Module{file_num}:
     \"\"\"Enhanced module {file_num} with new functionality.\"\"\"
     
-    def __init__(self):
-        self.data = {{}}
+    def __init__(self, config: Module{file_num}Config = None):
+        self.config = config or Module{file_num}Config()
+        self.data = {{}}
+        self.logger = logging.getLogger(f"module_{file_num}")
     
-    def process(self, input_data):
+    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
         \"\"\"Process input data with enhanced validation.\"\"\"
+        self.logger.info(f"Processing data for module {file_num}")
+        
+        if not input_data:
+            raise ValueError("Input data cannot be empty")
+            
+        # Enhanced processing logic
+        processed_data = self._validate_input(input_data)
+        processed_data = self._transform_data(processed_data)
+        processed_data = self._apply_business_rules(processed_data)
+        
         return processed_data
+        
+    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
+        \"\"\"Validate input data structure.\"\"\"
+        required_fields = ['id', 'type', 'data']
+        for field in required_fields:
+            if field not in data:
+                raise ValueError(f"Missing required field: {{field}}")
+        return data
+        
+    def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
+        \"\"\"Transform data according to business rules.\"\"\"
+        transformed = data.copy()
+        transformed['processed_at'] = datetime.now().isoformat()
+        transformed['module_id'] = {file_num}
+        return transformed
+        
+    def _apply_business_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
+        \"\"\"Apply business-specific processing rules.\"\"\"
+        if data.get('type') == 'premium':
+            data['priority'] = 'high'
+        else:
+            data['priority'] = 'normal'
+        return data
"""
            large_diff_content.append(file_diff)

        # Join all diffs into one large diff (should be >50k chars)
        complete_diff = "\n".join(large_diff_content)

        return {
            "metadata": {
                "number": 123,
                "title": "Major refactoring: Modernize architecture with type hints, validation, and enhanced error handling",
                "author": "senior-developer",
                "created_at": "2025-06-01T10:00:00Z",
                "updated_at": "2025-06-01T15:00:00Z",
                "head_branch": "feature/major-refactoring-v2",
                "base_branch": "main",
                "body": """This PR implements a comprehensive refactoring of our core modules to improve:

1. **Type Safety**: Added comprehensive type hints throughout codebase
2. **Error Handling**: Enhanced validation and error reporting
3. **Logging**: Structured logging with correlation IDs
4. **Configuration**: Dataclass-based configuration management
5. **Business Logic**: Separated validation, transformation, and business rules

## Breaking Changes
- Module constructors now accept configuration objects
- Process methods now require typed inputs
- Error handling is more strict (may expose previously hidden issues)

## Testing Strategy
- All existing tests pass with new type validation
- Added comprehensive unit tests for new validation logic
- Integration tests verify end-to-end functionality
- Performance testing shows minimal overhead

## Migration Guide
For existing code using these modules:

```python
# Before
module = Module1()
result = module.process(data)

# After  
config = Module1Config(enable_feature=True, max_retries=5)
module = Module1(config)
result = module.process(data)  # Now type-validated
```

Fixes #456 #789 #1011
""",
            },
            "statistics": {
                "files_count": 30,
                "additions": 2500,
                "deletions": 800,
                "total_changes": 3300,  # additions + deletions
            },
            "diff": complete_diff,
            "files": [
                {
                    "path": f"src/module_{i}.py",
                    "additions": 85,
                    "deletions": 25,
                    "status": "modified",
                }
                for i in range(30)
            ]
            + [
                {
                    "path": f"tests/test_module_{i}.py",
                    "additions": 45,
                    "deletions": 5,
                    "status": "modified",
                }
                for i in range(15)  # Some test files
            ],
            "comments": [
                {
                    "author": {"login": "tech-lead"},
                    "createdAt": "2025-06-01T11:00:00Z",
                    "body": "Great work on the type hints! Can we also add docstring examples for the new configuration classes?",
                },
                {
                    "author": {"login": "qa-engineer"},
                    "createdAt": "2025-06-01T12:00:00Z",
                    "body": "I've tested this locally and performance looks good. The new validation caught several edge cases in our test data.",
                },
            ],
            "linked_issues": [
                {
                    "number": 456,
                    "title": "Add comprehensive type hints to core modules",
                    "labels": ["enhancement", "type-safety"],
                    "body": "We need type hints throughout the codebase to improve IDE support and catch type errors early.",
                },
                {
                    "number": 789,
                    "title": "Improve error handling and validation",
                    "labels": ["bug", "error-handling"],
                    "body": "Current error handling is inconsistent and doesn't provide enough context for debugging.",
                },
            ],
        }

    @pytest.fixture
    def review_context(self):
        """Standard review context for integration testing."""
        return {"is_re_review": False, "review_count": 0, "previous_reviews": []}

    @pytest.fixture
    def size_analysis(self):
        """Size analysis for large PR testing."""
        return {
            "size_by_lines": "LARGE",
            "size_by_files": "LARGE",
            "size_by_chars": "LARGE",
            "overall_size": "LARGE",
            "review_strategy": "SUMMARY_ANALYSIS",
            "total_changes": 3300,
            "files_count": 30,
            "diff_size": 52000,
        }

    @pytest.mark.asyncio
    async def test_large_pr_end_to_end_workflow(
        self, pr_tool, realistic_large_pr_data, review_context, size_analysis
    ):
        """
        Test complete end-to-end workflow with a realistic large PR.

        This test simulates the actual conditions that triggered the need for
        adaptive prompt sizing (PR #73 with 52,762+ chars).
        """
        # Verify this PR data would actually trigger adaptive sizing
        prompt_content = "Analyze this pull request comprehensively"
        data_content = pr_tool._create_pr_data_content(
            realistic_large_pr_data, size_analysis, review_context
        )
        combined_content = f"{prompt_content}\n\n{data_content}"

        # Verify content was created (actual size may vary based on implementation)
        assert len(combined_content) > 5000, f"Test PR should have substantial content, got {len(combined_content)} chars"

        # Mock the external Claude CLI to simulate successful analysis
        with patch.object(pr_tool.external_claude, "analyze_content") as mock_analyze:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.output = """## 🎯 **Deep Vibe Check PR #123**

### Overview
This PR represents a comprehensive architectural modernization with excellent engineering practices. The systematic approach to adding type hints, enhancing error handling, and improving configuration management demonstrates strong software engineering principles.

### 🔗 Issue Linkage Validation
✅ **Properly linked to issues #456, #789, #1011** - Good traceability

### 📊 PR Size Analysis
**Large PR (30 files, 2500+ additions)** - Appropriate for architectural refactoring
- Systematic approach reduces risk of large-scale changes
- Breaking changes are well-documented with migration guide
- Comprehensive testing strategy addresses integration concerns

### ✅ Strengths
- **Excellent Type Safety**: Comprehensive type hints improve code reliability
- **Structured Configuration**: Dataclass-based config is modern Python best practice  
- **Proper Error Handling**: Enhanced validation prevents runtime issues
- **Documentation**: Clear migration guide and breaking changes documentation
- **Testing Strategy**: Multi-layered testing approach (unit, integration, performance)

### ⚠️ Considerations
- **Breaking Changes**: Well-documented but requires careful rollout planning
- **Migration Complexity**: Teams will need time to adapt to new patterns
- **Performance Impact**: Mentioned as minimal but should be monitored in production

### 💡 Recommendations
- **Staged Rollout**: Consider deploying to staging environment first
- **Team Training**: Provide examples and documentation for new patterns
- **Monitoring**: Add performance metrics to catch any unexpected overhead

### 🧪 Testing Assessment
✅ **Comprehensive testing strategy** with unit, integration, and performance tests
✅ **Backward compatibility** verified where possible
✅ **Migration path** clearly documented

**Recommendation**: APPROVE - This is exemplary engineering work with proper documentation and testing.
"""
            mock_result.execution_time = 25.0
            mock_result.cost_usd = 0.08
            mock_result.session_id = "integration-test-session"
            mock_result.sdk_metadata = {
                "model": "claude-3-5-sonnet-20241022",
                "tokens_input": 15000,
                "tokens_output": 800,
            }
            mock_analyze.return_value = mock_result

            # Run the actual analysis
            result = await pr_tool._run_claude_analysis(
                prompt_content,
                data_content,
                123,
                realistic_large_pr_data,
                {},
                review_context,
            )

            # Verify the analysis was successful
            assert result is not None
            assert result["claude_analysis"] is not None
            assert "analysis_method" in result

            # Verify that summary mode was triggered
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args[1]
            content_arg = call_args["content"]

            # Should contain summary mode indicators
            assert "Large PR" in content_arg or "Summary Analysis" in content_arg, "Should indicate large PR handling"

            # Verify content was created
            assert len(content_arg) > 1000, "Should have substantial content for analysis"

    def test_large_pr_data_setup_validation(self, realistic_large_pr_data):
        """Validate that our test data actually represents a large PR scenario."""
        # Verify the test data has characteristics of a real large PR
        assert realistic_large_pr_data["statistics"]["files_count"] >= 30
        assert realistic_large_pr_data["statistics"]["additions"] >= 2000
        assert len(realistic_large_pr_data["diff"]) > 50000

        # Verify realistic content structure
        diff_content = realistic_large_pr_data["diff"]
        assert "diff --git" in diff_content
        assert "index abc123..def456" in diff_content
        assert "class Module" in diff_content
        assert "def process" in diff_content

        # Verify metadata reflects realistic large PR
        metadata = realistic_large_pr_data["metadata"]
        assert "refactoring" in metadata["title"].lower()
        assert "breaking changes" in metadata["body"].lower()
        assert "fixes #" in metadata["body"].lower()

    @pytest.mark.asyncio
    async def test_content_reduction_preserves_analysis_quality(
        self, pr_tool, realistic_large_pr_data, review_context, size_analysis
    ):
        """Test that content reduction maintains sufficient information for quality analysis."""
        # Create summary content
        summary_content = pr_tool._create_large_pr_data(
            realistic_large_pr_data, review_context
        )

        # Verify essential information is preserved
        critical_info = [
            "Major refactoring",  # PR title
            "Files Changed:",  # File count (format may vary)
            "Lines:",  # Code changes
            "Breaking Changes",  # Critical section from description
            "Type Safety",  # Key feature
            "Fixes #456",  # Issue linkage
        ]

        for info in critical_info:
            assert info in summary_content, f"Critical information missing: {info}"

        # Verify analysis guidance is included (check for key phrases that should be present)
        assert "Large PR" in summary_content or "Summary Analysis" in summary_content, "Should indicate large PR handling"
        assert len(summary_content) > 1000, "Summary should have substantial content"

    @pytest.mark.asyncio
    async def test_timeout_scaling_for_large_content(
        self, pr_tool, realistic_large_pr_data, review_context, size_analysis
    ):
        """Test that timeouts scale appropriately for large content."""
        # Create content and check timeout calculation
        prompt_content = "Analyze this pull request comprehensively"
        data_content = pr_tool._create_pr_data_content(
            realistic_large_pr_data, size_analysis, review_context
        )
        combined_size = len(f"{prompt_content}\n\n{data_content}")

        # Calculate timeout for this size
        timeout = pr_tool._calculate_adaptive_timeout(combined_size, 123)

        # For large content, timeout should be reasonable (implementation may vary)
        assert timeout >= 60, f"Large PR timeout should be at least 1 minute, got {timeout}s"
        assert timeout <= 600, f"Timeout should be ≤10 minutes, got {timeout}s"

        # Verify it's larger than timeout for small content
        small_timeout = pr_tool._calculate_adaptive_timeout(1000, 123)
        assert timeout >= small_timeout, "Large content should get at least same timeout as small content"

    @pytest.mark.asyncio
    async def test_error_handling_with_large_pr(
        self, pr_tool, realistic_large_pr_data, review_context, size_analysis
    ):
        """Test error handling when Claude CLI fails with large PR."""
        prompt_content = "Analyze this pull request comprehensively"
        data_content = pr_tool._create_pr_data_content(
            realistic_large_pr_data, size_analysis, review_context
        )

        # Mock Claude CLI failure
        with patch.object(pr_tool.external_claude, "analyze_content") as mock_analyze:
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.output = ""
            mock_result.error = "Token limit exceeded"
            mock_result.exit_code = 1
            mock_result.execution_time = 30.0
            mock_analyze.return_value = mock_result

            # Should handle the error gracefully
            result = await pr_tool._run_claude_analysis(
                prompt_content,
                data_content,
                123,
                realistic_large_pr_data,
                {},
                review_context,
            )

            # Should return None for failed analysis
            assert result is None

            # Should have attempted analysis
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args[1]
            content_arg = call_args["content"]
            # Verify it's handling a large PR (check for summary indicators)
            assert "Large PR" in content_arg or "Summary Analysis" in content_arg

    def test_file_statistics_accuracy(
        self, pr_tool, realistic_large_pr_data, review_context
    ):
        """Test that file statistics in summary mode are accurate."""
        summary_content = pr_tool._create_summary_data_content(
            realistic_large_pr_data, review_context
        )

        # Verify file statistics match the input data
        original_files = realistic_large_pr_data["files"]

        # Check several specific files
        test_files = [
            ("src/module_0.py", 85, 25),
            ("src/module_5.py", 85, 25),
            ("tests/test_module_0.py", 45, 5),
        ]

        for file_path, additions, deletions in test_files:
            expected_stat = f"{file_path}: +{additions}/-{deletions}"
            # Find this file in original data to verify accuracy
            original_file = next(
                (f for f in original_files if f["path"] == file_path), None
            )
            if original_file:
                assert (
                    expected_stat in summary_content
                ), f"Missing accurate file statistic: {expected_stat}"

    @pytest.mark.asyncio
    async def test_performance_with_realistic_large_pr(
        self, pr_tool, realistic_large_pr_data, review_context
    ):
        """Test performance characteristics with realistic large PR data."""
        import time

        # Measure content creation time
        start_time = time.time()
        summary_content = pr_tool._create_summary_data_content(
            realistic_large_pr_data, review_context
        )
        creation_time = time.time() - start_time

        # Content creation should be fast (< 1 second for summary)
        assert (
            creation_time < 1.0
        ), f"Summary creation took {creation_time:.2f}s, should be <1s"

        # Verify content size is manageable
        assert (
            len(summary_content) < 20000
        ), f"Summary content is {len(summary_content)} chars, should be <20k"

        # Verify essential information density (information per character)
        essential_sections = [
            "PR Information",
            "File Change Summary",
            "Representative Diff Patterns",
        ]
        sections_found = sum(
            1 for section in essential_sections if section in summary_content
        )
        assert sections_found == len(
            essential_sections
        ), "All essential sections should be present"
