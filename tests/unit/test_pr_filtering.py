"""
Tests for PR Filtering Module (Issue #101)

Tests the intelligent pre-filtering logic that determines when to use
LLM analysis vs fast analysis based on PR size and complexity.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from vibe_check.core.pr_filtering import (
    should_use_llm_analysis,
    create_large_pr_response, 
    analyze_with_fallback,
    PRFilterResult,
    _generate_splitting_guidance
)


class TestShouldUseLLMAnalysis:
    """Test the core filtering logic."""
    
    def test_small_pr_uses_llm(self):
        """Small PRs should use LLM analysis."""
        pr_data = {
            'additions': 50,
            'deletions': 20, 
            'changed_files': 3
        }
        
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        
        assert result.should_use_llm is True
        assert "Suitable for LLM" in result.reason
        assert result.fallback_strategy == "not_needed"
        assert result.size_metrics['total_changes'] == 70
    
    def test_large_pr_lines_skips_llm(self):
        """PRs with >1000 lines should skip LLM analysis."""
        from vibe_check.core.pr_filtering import FilteringConfig
        
        pr_data = {
            'additions': 800,
            'deletions': 300,  # Total: 1100
            'changed_files': 15
        }
        
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        
        assert result.should_use_llm is False
        assert f"Large PR: 1100 lines changed (threshold: {FilteringConfig.MAX_LINES_FOR_LLM})" in result.reason
        assert result.fallback_strategy == "fast_analysis_with_guidance"
    
    def test_many_files_skips_llm(self):
        """PRs with >20 files should skip LLM analysis."""
        pr_data = {
            'additions': 400,
            'deletions': 200, 
            'changed_files': 25
        }
        
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        
        assert result.should_use_llm is False
        assert "Many files changed: 25 files (threshold: 20)" in result.reason
        assert result.fallback_strategy == "fast_analysis_with_guidance"
    
    def test_wide_changes_skips_llm(self):
        """PRs with many files and moderate lines should skip LLM (refactoring pattern)."""
        pr_data = {
            'additions': 400,
            'deletions': 200,  # Total: 600
            'changed_files': 18  # 18 files > 15 threshold
        }
        
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        
        assert result.should_use_llm is False
        assert "Wide changes" in result.reason
        assert "refactoring pattern" in result.reason
        assert result.fallback_strategy == "fast_analysis_with_guidance"
    
    def test_edge_case_exact_thresholds(self):
        """Test behavior exactly at thresholds."""
        # Exactly at line threshold
        pr_data = {
            'additions': 500,
            'deletions': 500,  # Exactly 1000
            'changed_files': 10
        }
        
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        assert result.should_use_llm is True  # Should use LLM at threshold
        
        # Just over line threshold
        pr_data['additions'] = 501  # Now 1001 total
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        assert result.should_use_llm is False  # Should skip LLM
    
    def test_missing_data_defaults(self):
        """Test handling of missing PR data."""
        pr_data = {}  # Empty data
        
        result = should_use_llm_analysis(pr_data, track_metrics=False)
        
        assert result.should_use_llm is True  # Defaults should allow LLM
        assert result.size_metrics['total_changes'] == 0
        assert result.size_metrics['changed_files'] == 0


class TestCreateLargePRResponse:
    """Test large PR response generation."""
    
    def test_large_pr_response_structure(self):
        """Test the structure of large PR responses."""
        pr_data = {
            'number': 123,
            'title': 'Large refactoring PR'
        }
        
        filter_result = PRFilterResult(
            should_use_llm=False,
            reason="Large PR: 1500 lines changed (threshold: 1000)",
            fallback_strategy="fast_analysis_with_guidance",
            size_metrics={
                'total_changes': 1500,
                'changed_files': 30,
                'additions': 1000,
                'deletions': 500
            }
        )
        
        response = create_large_pr_response(pr_data, filter_result)
        
        assert response['status'] == "large_pr_detected"
        assert response['analysis_mode'] == "pattern_detection_only"
        assert response['large_pr_detected'] is True
        assert filter_result.reason in response['filter_reason']
        assert "Large PR detected" in response['message']
        assert "Consider splitting into smaller PRs" in response['recommendation']
        assert 'guidance' in response
        assert 'size_metrics' in response
    
    def test_splitting_guidance_generation(self):
        """Test generation of specific splitting guidance."""
        # Test guidance for many files
        size_metrics = {
            'total_changes': 800,
            'changed_files': 25,
            'files_per_change_ratio': 0.03
        }
        
        guidance = _generate_splitting_guidance(size_metrics)
        
        assert "Split by functional area" in guidance[0]
        assert "Separate refactoring changes" in guidance[1]
        
        # Test guidance for many changes
        size_metrics = {
            'total_changes': 1500,
            'changed_files': 10,
            'files_per_change_ratio': 0.007
        }
        
        guidance = _generate_splitting_guidance(size_metrics)
        
        assert any("logical commits" in g for g in guidance)
        assert any("feature flags" in g for g in guidance)


class TestAnalyzeWithFallback:
    """Test the core orchestration function with graceful degradation."""
    
    @pytest.mark.asyncio
    async def test_small_pr_uses_llm_successfully(self):
        """Small PRs should use LLM analysis when it succeeds."""
        pr_data = {
            'additions': 100,
            'deletions': 50,
            'changed_files': 5
        }
        
        llm_result = {"status": "success", "analysis": "LLM analysis"}
        fast_result = {"status": "success", "analysis": "Fast analysis"}
        
        llm_func = AsyncMock(return_value=llm_result)
        fast_func = Mock(return_value=fast_result)
        
        result = await analyze_with_fallback(
            pr_data=pr_data,
            llm_analyzer_func=llm_func,
            fast_analyzer_func=fast_func
        )
        
        # Should use LLM and add filtering context
        assert result['analysis'] == "LLM analysis"
        assert result['analysis_method'] == "llm_analysis"
        assert 'filter_result' in result
        llm_func.assert_called_once()
        fast_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_large_pr_skips_llm(self):
        """Large PRs should skip LLM analysis entirely."""
        pr_data = {
            'additions': 800,
            'deletions': 400,  # 1200 total > threshold
            'changed_files': 15
        }
        
        llm_result = {"status": "success", "analysis": "LLM analysis"}
        fast_result = {"status": "success", "analysis": "Fast analysis"}
        
        llm_func = AsyncMock(return_value=llm_result)
        fast_func = Mock(return_value=fast_result)
        
        result = await analyze_with_fallback(
            pr_data=pr_data,
            llm_analyzer_func=llm_func,
            fast_analyzer_func=fast_func
        )
        
        # Should skip LLM and enhance fast result
        assert result['analysis'] == "Fast analysis"
        assert result['status'] == "large_pr_detected"
        assert result['large_pr_detected'] is True
        llm_func.assert_not_called()
        fast_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_llm_failure_fallback(self):
        """When LLM fails, should fall back to fast analysis."""
        pr_data = {
            'additions': 200,
            'deletions': 100,
            'changed_files': 8
        }
        
        fast_result = {"status": "success", "analysis": "Fast analysis"}
        
        llm_func = AsyncMock(side_effect=Exception("Claude CLI timeout"))
        fast_func = Mock(return_value=fast_result)
        
        result = await analyze_with_fallback(
            pr_data=pr_data,
            llm_analyzer_func=llm_func,
            fast_analyzer_func=fast_func
        )
        
        # Should fall back gracefully
        assert result['analysis'] == "Fast analysis"
        assert result['status'] == "partial_analysis"
        assert result['analysis_mode'] == "pattern_detection_only"
        assert "Claude CLI timeout" in result['llm_analysis_error']
        assert result['fallback_reason'] == "LLM analysis failed, using fast analysis"
        llm_func.assert_called_once()
        fast_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_failure_graceful_degradation(self):
        """When everything fails, should still return useful response."""
        pr_data = {
            'additions': 200,
            'deletions': 100,
            'changed_files': 8,
            'number': 123,
            'title': 'Test PR'
        }
        
        llm_func = AsyncMock(side_effect=Exception("LLM failure"))
        fast_func = Mock(side_effect=Exception("Fast analysis failure"))
        
        result = await analyze_with_fallback(
            pr_data=pr_data,
            llm_analyzer_func=llm_func,
            fast_analyzer_func=fast_func
        )
        
        # Should provide minimal fallback
        assert result['status'] == "error_fallback"
        assert result['analysis_mode'] == "minimal_fallback"
        assert 'error' in result
        assert result['fallback_data']['pr_number'] == 123
        assert result['fallback_data']['title'] == 'Test PR'
        assert "Manual review recommended" in result['fallback_data']['recommendation']
        assert "graceful degradation" in result['note']


class TestPRFilterResult:
    """Test the PRFilterResult dataclass."""
    
    def test_filter_result_creation(self):
        """Test creation and properties of PRFilterResult."""
        size_metrics = {'total_changes': 500, 'changed_files': 10}
        
        result = PRFilterResult(
            should_use_llm=True,
            reason="Small PR suitable for analysis",
            fallback_strategy="not_needed",
            size_metrics=size_metrics
        )
        
        assert result.should_use_llm is True
        assert result.reason == "Small PR suitable for analysis"
        assert result.fallback_strategy == "not_needed"
        assert result.size_metrics == size_metrics


if __name__ == "__main__":
    pytest.main([__file__])