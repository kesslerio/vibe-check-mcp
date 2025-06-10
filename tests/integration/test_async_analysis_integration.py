"""
Integration Tests for Async Analysis System

Tests the complete async processing pipeline from PR analysis
request through queue management, worker processing, and status tracking.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch

from src.vibe_check.tools.async_analysis.config import AsyncAnalysisConfig
from src.vibe_check.tools.async_analysis.integration import start_async_analysis, check_analysis_status


class TestAsyncAnalysisIntegration:
    """Test complete async analysis integration."""
    
    @pytest.mark.asyncio
    async def test_large_pr_async_flow(self):
        """Test complete flow for large PR requiring async processing."""
        # Large PR that should trigger async processing
        large_pr_data = {
            "title": "Massive refactoring - V2 architecture",
            "additions": 3000,
            "deletions": 1500,
            "changed_files": 45
        }
        
        # Test that large PR is correctly identified for async processing
        config = AsyncAnalysisConfig()
        assert config.should_use_async_processing(large_pr_data)
        
        # Mock successful async analysis start
        with patch('src.vibe_check.tools.async_analysis.integration.get_global_queue') as mock_queue:
            mock_queue_instance = Mock()
            mock_queue_instance.queue_analysis = Mock(return_value="async-job-123")
            mock_queue.return_value = mock_queue_instance
            
            with patch('src.vibe_check.tools.async_analysis.integration._status_tracker') as mock_tracker:
                mock_tracker.get_comprehensive_status.return_value = {
                    "job_id": "async-job-123",
                    "status": "queued",
                    "progress_percent": 0,
                    "timing": {"estimated_completion_timestamp": 1234567890}
                }
                
                # Start async analysis
                result = await start_async_analysis(
                    pr_number=660,
                    repository="owner/repo", 
                    pr_data=large_pr_data
                )
                
                # Verify async processing was started
                assert result["status"] == "queued_for_async_analysis"
                assert result["job_id"] == "async-job-123"
                assert "immediate_analysis" in result
                assert "instructions" in result
                
                # Check that immediate analysis provides useful insights
                immediate = result["immediate_analysis"]
                assert immediate["size_analysis"]["category"] in ["very_large", "massive"]
                assert "recommendations" in immediate
                assert len(immediate["immediate_recommendations"]) > 0
    
    @pytest.mark.asyncio 
    async def test_small_pr_rejection(self):
        """Test that small PRs are rejected for async processing."""
        # Small PR that should NOT trigger async processing
        small_pr_data = {
            "title": "Small bug fix",
            "additions": 50,
            "deletions": 20,
            "changed_files": 3
        }
        
        result = await start_async_analysis(
            pr_number=123,
            repository="owner/repo",
            pr_data=small_pr_data
        )
        
        # Should be rejected
        assert result["status"] == "not_suitable"
        assert "not large enough" in result["message"]
        assert "pr_size_info" in result
    
    @pytest.mark.asyncio
    async def test_status_checking_flow(self):
        """Test status checking for async analysis."""
        # Mock status checking
        with patch('src.vibe_check.tools.async_analysis.integration.get_global_queue') as mock_queue:
            mock_queue_instance = Mock()
            mock_queue.return_value = mock_queue_instance
            
            with patch('src.vibe_check.tools.async_analysis.integration._status_tracker') as mock_tracker:
                # Test job in progress
                mock_tracker.get_comprehensive_status.return_value = {
                    "job_id": "test-job-456",
                    "status": "processing",
                    "progress_percent": 65,
                    "phase": "analyzing",
                    "message": "Analyzing code changes (65%)",
                    "timing": {
                        "time_remaining_seconds": 180,
                        "processing_duration_seconds": 300
                    },
                    "pr_info": {
                        "title": "Large refactoring PR",
                        "additions": 2500,
                        "changed_files": 30
                    }
                }
                
                result = await check_analysis_status("test-job-456")
                
                assert result["status"] == "status_retrieved"
                job_status = result["job_status"]
                assert job_status["job_id"] == "test-job-456"
                assert job_status["progress_percent"] == 65
                assert job_status["phase"] == "analyzing"
                assert "time_remaining_seconds" in job_status["timing"]
    
    def test_pr_size_thresholds(self):
        """Test PR size threshold logic for async processing."""
        config = AsyncAnalysisConfig()
        
        test_cases = [
            # (additions, deletions, files, expected_async)
            (500, 200, 10, False),      # Too small
            (1200, 400, 15, True),      # Large enough by lines
            (800, 300, 35, True),       # Large enough by files
            (2000, 1000, 50, True),     # Definitely large
            (100, 50, 5, False),        # Definitely small
        ]
        
        for additions, deletions, files, expected in test_cases:
            pr_data = {
                "additions": additions,
                "deletions": deletions,
                "changed_files": files
            }
            result = config.should_use_async_processing(pr_data)
            assert result == expected, f"Failed for {additions}+{deletions} lines, {files} files"
    
    def test_duration_estimation_scaling(self):
        """Test that duration estimation scales reasonably with PR size."""
        config = AsyncAnalysisConfig()
        
        # Test various PR sizes
        small_pr = {"additions": 500, "deletions": 200, "changed_files": 10}
        medium_pr = {"additions": 1500, "deletions": 800, "changed_files": 25}
        large_pr = {"additions": 3000, "deletions": 1500, "changed_files": 50}
        
        small_duration = config.estimate_duration(small_pr)
        medium_duration = config.estimate_duration(medium_pr)
        large_duration = config.estimate_duration(large_pr)
        
        # Durations should increase with PR size
        assert small_duration < medium_duration < large_duration
        
        # But all should be reasonable (not too long)
        assert large_duration <= config.max_analysis_duration
        assert small_duration >= 180  # At least base time
    
    def test_immediate_analysis_quality(self):
        """Test quality of immediate analysis for large PRs."""
        from src.vibe_check.tools.async_analysis.integration import _generate_immediate_analysis
        
        # Test massive PR
        massive_pr = {
            "title": "Complete V2 rewrite", 
            "additions": 8000,
            "deletions": 3000,
            "changed_files": 75
        }
        
        analysis = _generate_immediate_analysis(massive_pr)
        
        # Should categorize as massive
        assert analysis["size_analysis"]["category"] == "massive"
        assert "architectural changes" in analysis["size_analysis"]["complexity_note"]
        
        # Should have practical recommendations
        recommendations = analysis["immediate_recommendations"]
        assert len(recommendations) >= 3
        assert any("review time" in rec for rec in recommendations)
        assert any("testing" in rec for rec in recommendations)
        
        # Should have review strategy
        strategy = analysis["review_strategy"]
        assert strategy["approach"] == "architectural_first"
        assert "breaking_changes" in strategy["focus_areas"]
        assert "security_implications" in strategy["focus_areas"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])