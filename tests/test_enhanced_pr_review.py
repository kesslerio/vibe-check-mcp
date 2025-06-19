"""
Test Enhanced PR Review Features

Tests for the enhanced PR review tool with file type analysis,
author awareness, and model selection capabilities.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.vibe_check.tools.pr_review.main import review_pull_request
from src.vibe_check.tools.pr_review.file_type_analyzer import FileTypeAnalyzer


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
            {"filename": "migrations/001_init.sql"}
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
        with patch('src.vibe_check.tools.pr_review.main.PRDataCollector') as mock_collector, \
             patch('src.vibe_check.tools.pr_review.main.ClaudeIntegration') as mock_claude:
            
            # Setup mocks
            mock_collector_instance = Mock()
            mock_collector_instance.collect_pr_data.return_value = {
                "metadata": {"author_association": "FIRST_TIME_CONTRIBUTOR"},
                "files": [],
                "statistics": {"files_count": 1, "additions": 10, "deletions": 5}
            }
            mock_collector.return_value = mock_collector_instance
            
            mock_claude_instance = Mock()
            mock_claude_instance.check_claude_availability.return_value = False
            mock_claude.return_value = mock_claude_instance
            
            # Test with opus model
            result = await review_pull_request(
                pr_number=123,
                model="opus"
            )
            
            assert result["model_used"] == "opus"
    
    @pytest.mark.asyncio 
    async def test_first_time_contributor_detection(self):
        """Test that first-time contributors are properly detected."""
        with patch('src.vibe_check.tools.pr_review.main.PRDataCollector') as mock_collector, \
             patch('src.vibe_check.tools.pr_review.main.ClaudeIntegration') as mock_claude:
            
            # Setup mocks for first-time contributor
            mock_collector_instance = Mock()
            mock_collector_instance.collect_pr_data.return_value = {
                "metadata": {
                    "author": "newcontributor",
                    "author_association": "FIRST_TIME_CONTRIBUTOR",
                    "title": "Fix typo in README"
                },
                "files": [{"filename": "README.md"}],
                "statistics": {"files_count": 1, "additions": 1, "deletions": 1}
            }
            mock_collector.return_value = mock_collector_instance
            
            mock_claude_instance = Mock()
            mock_claude_instance.check_claude_availability.return_value = True
            mock_claude_instance.run_claude_analysis = AsyncMock(return_value={
                "analysis": "Welcome to the project!",
                "recommendation": "APPROVE"
            })
            mock_claude.return_value = mock_claude_instance
            
            result = await review_pull_request(
                pr_number=456,
                model="sonnet"
            )
            
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
                    "common_issues": ["Missing types", "Any usage"]
                },
                "api": {
                    "files": ["src/api/routes.py"],
                    "count": 1,
                    "focus_areas": ["Security", "Input validation"],
                    "common_issues": ["SQL injection", "Missing auth"]
                }
            },
            "priority_checks": [
                {"type": "api", "reason": "Security-sensitive file type", "files": ["src/api/routes.py"]}
            ]
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
            'typescript', 'javascript', 'python', 'api', 
            'react', 'test', 'config', 'sql'
        ]
        
        for file_type in expected_types:
            assert file_type in analyzer.REVIEW_GUIDELINES
            guidelines = analyzer.REVIEW_GUIDELINES[file_type]
            assert 'focus_areas' in guidelines
            assert 'common_issues' in guidelines
            assert len(guidelines['focus_areas']) > 0
            assert len(guidelines['common_issues']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])