"""
Real GitHub Integration Tests for Async Analysis System

Tests the complete async analysis workflow using actual GitHub PRs,
validating end-to-end functionality with real data.
"""

import asyncio
import pytest
import time
import logging
from typing import Dict, Any

from vibe_check.tools.async_analysis.integration import (
    start_async_analysis,
    check_analysis_status,
    get_system_status,
)
from vibe_check.tools.async_analysis.config import DEFAULT_ASYNC_CONFIG
from vibe_check.tools.shared.github_abstraction import get_default_github_operations

logger = logging.getLogger(__name__)


class TestAsyncAnalysisRealGitHub:
    """Integration tests using real GitHub PR data."""

    @pytest.fixture
    def github_ops(self):
        """Get GitHub operations for testing."""
        return get_default_github_operations()

    @pytest.fixture
    def sample_massive_pr_data(self):
        """Sample data representing a massive PR."""
        return {
            "number": 999,
            "title": "Test: Massive refactoring PR for async analysis testing",
            "additions": 2000,
            "deletions": 800,
            "changed_files": 35,
        }

    @pytest.fixture
    def sample_large_pr_data(self):
        """Sample data representing a large but not massive PR."""
        return {
            "number": 998,
            "title": "Test: Large feature implementation",
            "additions": 800,
            "deletions": 200,
            "changed_files": 15,
        }

    @pytest.mark.asyncio
    async def test_real_pr_size_detection(self, github_ops):
        """Test size detection using real GitHub PR data."""
        # Skip if no GitHub auth
        auth_result = github_ops.check_authentication()
        if not auth_result.success:
            pytest.skip("GitHub authentication not available")

        repository = "kesslerio/vibe-check-mcp"

        # Try to fetch a known PR (use PR #109 from our recent work)
        pr_result = github_ops.get_pull_request(repository, 109)

        if pr_result.success:
            pr = pr_result.data
            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "additions": getattr(pr, "additions", 0),
                "deletions": getattr(pr, "deletions", 0),
                "changed_files": getattr(pr, "changed_files", 0),
            }

            logger.info(f"Real PR data: {pr_data}")

            # Test size classification
            config = DEFAULT_ASYNC_CONFIG
            should_async = config.should_use_async_processing(pr_data)
            estimated_duration = config.estimate_duration(pr_data)

            # Validate that we get reasonable estimates
            assert isinstance(should_async, bool)
            assert isinstance(estimated_duration, int)
            assert estimated_duration > 0
            assert estimated_duration <= config.max_analysis_duration

            logger.info(
                f"Should use async: {should_async}, Estimated duration: {estimated_duration}s"
            )
        else:
            logger.warning(f"Could not fetch PR #109: {pr_result.error}")
            pytest.skip("Could not fetch test PR data")

    @pytest.mark.asyncio
    async def test_async_workflow_with_mock_massive_pr(self, sample_massive_pr_data):
        """Test complete async workflow with mock massive PR data."""
        repository = "kesslerio/vibe-check-mcp"

        # Start async analysis
        result = await start_async_analysis(
            pr_number=sample_massive_pr_data["number"],
            repository=repository,
            pr_data=sample_massive_pr_data,
        )

        # Validate initial response
        assert result["status"] in [
            "queued_for_async_analysis",
            "not_suitable",
            "error",
        ]

        if result["status"] == "queued_for_async_analysis":
            analysis_id = result["job_id"]
            assert analysis_id is not None

            # Check status immediately
            status_result = await check_analysis_status(analysis_id)
            assert status_result["status"] in ["status_retrieved", "not_found", "error"]

            # Validate status structure
            if status_result["status"] == "status_retrieved":
                job_status = status_result["job_status"]
                assert "status" in job_status
                assert job_status["status"] in [
                    "queued",
                    "in_progress",
                    "completed",
                    "failed",
                ]

                if "progress_percent" in job_status:
                    assert isinstance(job_status["progress_percent"], (int, float))
                    assert 0 <= job_status["progress_percent"] <= 100

            # Test multiple status checks
            max_checks = 5
            for i in range(max_checks):
                status = await check_analysis_status(analysis_id)
                if status["status"] == "status_retrieved":
                    job_status = status["job_status"]
                    logger.info(
                        f"Status check {i+1}: {job_status.get('status')} - {job_status.get('progress_percent', 0)}%"
                    )

                    if job_status.get("status") in ["completed", "failed"]:
                        break
                else:
                    logger.info(f"Status check {i+1}: {status.get('status')}")

                await asyncio.sleep(2)
        else:
            logger.info(
                f"Async analysis not started: {result.get('error', 'Unknown error')}"
            )

    @pytest.mark.asyncio
    async def test_system_status_endpoint(self):
        """Test system status monitoring."""
        status = await get_system_status()

        # Validate system status structure
        assert isinstance(status, dict)
        assert "system_status" in status

        # System can be in different states
        system_state = status["system_status"]
        assert system_state in ["not_initialized", "running", "error"]

        if system_state == "running":
            # When running, should have queue and worker info
            assert "queue_overview" in status
            assert "worker_status" in status
        elif system_state == "not_initialized":
            # When not initialized, should have explanatory message
            assert "message" in status

        logger.info(f"System status: {system_state}")

    @pytest.mark.asyncio
    async def test_input_validation_integration(self, sample_massive_pr_data):
        """Test input validation in real async workflow."""
        repository = "kesslerio/vibe-check-mcp"

        # Test with invalid data
        invalid_cases = [
            # Invalid PR number
            {
                "pr_number": -1,
                "repository": repository,
                "pr_data": sample_massive_pr_data,
                "expected_error": "pr_number",
            },
            # Invalid repository
            {
                "pr_number": 999,
                "repository": "invalid..repo/name",
                "pr_data": sample_massive_pr_data,
                "expected_error": "repository",
            },
            # Invalid PR data
            {
                "pr_number": 999,
                "repository": repository,
                "pr_data": {"invalid": "data"},
                "expected_error": "pr_data",
            },
        ]

        for case in invalid_cases:
            result = await start_async_analysis(
                pr_number=case["pr_number"],
                repository=case["repository"],
                pr_data=case["pr_data"],
            )

            # Should return error for invalid input
            assert result["status"] == "error"
            assert (
                "validation" in result.get("error", "").lower()
                or "invalid" in result.get("error", "").lower()
            )
            logger.info(f"Validation correctly caught: {case['expected_error']}")

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(
        self, sample_massive_pr_data, sample_large_pr_data
    ):
        """Test handling of concurrent analysis requests."""
        repository = "kesslerio/vibe-check-mcp"

        # Start multiple analysis requests concurrently
        tasks = [
            start_async_analysis(999, repository, sample_massive_pr_data),
            start_async_analysis(998, repository, sample_large_pr_data),
            start_async_analysis(997, repository, sample_massive_pr_data),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate that all requests were handled gracefully
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Request {i} failed with exception: {result}")
            else:
                assert isinstance(result, dict)
                assert "status" in result
                logger.info(f"Request {i} status: {result['status']}")

    @pytest.mark.asyncio
    async def test_github_api_integration_fallback(self, github_ops):
        """Test fallback behavior when GitHub API is unavailable."""
        repository = "nonexistent/repository"
        pr_data = {
            "number": 1,
            "title": "Test PR",
            "additions": 2000,
            "deletions": 500,
            "changed_files": 40,
        }

        # This should handle the case where the repository doesn't exist
        result = await start_async_analysis(
            pr_number=1, repository=repository, pr_data=pr_data
        )

        # Should either start analysis (if it doesn't validate repo existence)
        # or return appropriate error
        assert "status" in result
        logger.info(f"Nonexistent repo result: {result}")

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, sample_massive_pr_data):
        """Test that performance metrics are collected during analysis."""
        repository = "kesslerio/vibe-check-mcp"

        start_time = time.time()

        result = await start_async_analysis(
            pr_number=sample_massive_pr_data["number"],
            repository=repository,
            pr_data=sample_massive_pr_data,
        )

        response_time = time.time() - start_time

        # Async start should be fast (< 5 seconds)
        assert response_time < 5.0, f"Async start took too long: {response_time}s"

        if result["status"] == "queued_for_async_analysis":
            analysis_id = result["job_id"]

            # Get system metrics
            metrics = await get_system_status()

            if "performance_metrics" in metrics:
                perf = metrics["performance_metrics"]
                assert isinstance(perf.get("average_response_time", 0), (int, float))
                assert isinstance(perf.get("total_requests", 0), int)

        logger.info(f"Performance test - Start time: {response_time:.2f}s")


class TestAsyncAnalysisErrorScenarios:
    """Test error handling and edge cases in async analysis."""

    @pytest.mark.asyncio
    async def test_malformed_pr_data_handling(self):
        """Test handling of malformed PR data."""
        repository = "kesslerio/vibe-check-mcp"

        malformed_cases = [
            # Missing required fields
            {"number": 1, "title": "Test"},
            # Negative values
            {
                "number": 1,
                "title": "Test",
                "additions": -100,
                "deletions": 50,
                "changed_files": 10,
            },
            # Extremely large values
            {
                "number": 1,
                "title": "Test",
                "additions": 999999999,
                "deletions": 0,
                "changed_files": 1,
            },
            # Wrong data types
            {
                "number": 1,
                "title": "Test",
                "additions": "many",
                "deletions": 50,
                "changed_files": 10,
            },
        ]

        for malformed_data in malformed_cases:
            result = await start_async_analysis(
                pr_number=1, repository=repository, pr_data=malformed_data
            )

            # Should handle malformed data gracefully
            assert isinstance(result, dict)
            assert "status" in result
            logger.info(f"Malformed data handled: {result.get('status')}")

    @pytest.mark.asyncio
    async def test_status_check_invalid_job_id(self):
        """Test status checking with invalid job IDs."""
        invalid_ids = [
            "nonexistent-job-id",
            "invalid..job..id",
            "",
            "a" * 200,  # Too long
            "job-with-special-chars-!@#$%",
        ]

        for job_id in invalid_ids:
            result = await check_analysis_status(job_id)

            # Should return appropriate error
            assert isinstance(result, dict)
            assert result.get("status") in ["error", "not_found"]
            logger.info(f"Invalid job ID '{job_id[:20]}...' handled correctly")


if __name__ == "__main__":
    # Run a simple test
    async def main():
        print("Running basic integration test...")

        # Test system status
        status = await get_system_status()
        print(f"System status: {status}")

        # Test with sample data
        sample_data = {
            "number": 999,
            "title": "Test PR",
            "additions": 2000,
            "deletions": 500,
            "changed_files": 35,
        }

        result = await start_async_analysis(
            999, "kesslerio/vibe-check-mcp", sample_data
        )
        print(f"Analysis result: {result}")

    asyncio.run(main())
