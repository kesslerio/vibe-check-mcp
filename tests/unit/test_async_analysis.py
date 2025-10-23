"""
Tests for Async Analysis System (Issue #104)

Comprehensive tests for Phase 4 async processing queue implementation
including queue management, worker processing, status tracking, and integration.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from vibe_check.tools.async_analysis.config import (
    AsyncAnalysisConfig,
    AsyncAnalysisMetrics,
)
from vibe_check.tools.async_analysis.queue_manager import (
    AsyncAnalysisQueue,
    AnalysisJob,
    JobStatus,
)
from vibe_check.tools.async_analysis.worker import (
    AsyncAnalysisWorker,
    AsyncWorkerManager,
    WorkerResult,
)
from vibe_check.tools.async_analysis.status_tracker import (
    StatusTracker,
    AnalysisPhase,
    AnalysisStatus,
)
from vibe_check.tools.async_analysis.integration import (
    start_async_analysis,
    check_analysis_status,
    get_system_status,
)
from vibe_check.tools.async_analysis.worker import shutdown_global_workers
from vibe_check.tools.async_analysis.queue_manager import shutdown_global_queue
from vibe_check.tools.async_analysis.resource_monitor import shutdown_global_resource_monitor


@pytest.fixture(autouse=True)
async def cleanup_async_globals():
    """
    Automatically cleanup global async analysis system between tests.

    This prevents worker loops from previous tests interfering with current tests,
    which was causing "unsupported operand type(s) for +: 'coroutine' and 'coroutine'"
    errors when workers tried to process jobs with mocked or corrupted pr_data.
    """
    yield  # Let test run first

    # Cleanup after each test
    try:
        await shutdown_global_workers()
    except Exception:
        pass  # Ignore if workers not initialized

    try:
        await shutdown_global_queue()
    except Exception:
        pass  # Ignore if queue not initialized

    try:
        shutdown_global_resource_monitor()
    except Exception:
        pass  # Ignore if monitor not initialized


class TestAsyncAnalysisConfig:
    """Test async analysis configuration."""

    def test_config_initialization(self):
        """Test config initializes with correct defaults."""
        config = AsyncAnalysisConfig()

        assert config.max_queue_size == 50
        assert config.max_concurrent_workers == 2
        assert config.chunk_timeout_seconds == 300
        assert config.large_pr_chunk_size == 1000
        assert config.async_threshold_lines == 1500
        assert config.async_threshold_files == 30

    def test_duration_estimation(self):
        """Test PR duration estimation."""
        config = AsyncAnalysisConfig()

        # Small PR
        small_pr = {"additions": 500, "deletions": 200, "changed_files": 5}
        duration = config.estimate_duration(small_pr)
        assert 180 <= duration <= 400  # Base + small overhead

        # Large PR
        large_pr = {"additions": 3000, "deletions": 1000, "changed_files": 40}
        duration = config.estimate_duration(large_pr)
        assert duration > 400  # Should be higher
        assert duration <= config.max_analysis_duration  # Capped

    def test_async_processing_decision(self):
        """Test async processing threshold logic."""
        config = AsyncAnalysisConfig()

        # Should use async - many lines
        large_lines_pr = {"additions": 2000, "deletions": 500, "changed_files": 10}
        assert config.should_use_async_processing(large_lines_pr)

        # Should use async - many files
        many_files_pr = {"additions": 500, "deletions": 200, "changed_files": 35}
        assert config.should_use_async_processing(many_files_pr)

        # Should NOT use async
        small_pr = {"additions": 500, "deletions": 200, "changed_files": 10}
        assert not config.should_use_async_processing(small_pr)


class TestAnalysisJob:
    """Test analysis job data structure."""

    def test_job_creation(self):
        """Test creating analysis job."""
        pr_data = {
            "title": "Test PR",
            "additions": 1000,
            "deletions": 500,
            "changed_files": 25,
        }

        job = AnalysisJob(
            job_id="test-job-123",
            pr_number=123,
            repository="owner/repo",
            pr_data=pr_data,
        )

        assert job.job_id == "test-job-123"
        assert job.pr_number == 123
        assert job.repository == "owner/repo"
        assert job.status == JobStatus.QUEUED
        assert job.progress == 0

    def test_job_serialization(self):
        """Test job to_dict conversion."""
        pr_data = {"title": "Test PR", "additions": 100, "deletions": 50}
        job = AnalysisJob("job-1", 1, "repo", pr_data)

        job_dict = job.to_dict()

        assert job_dict["job_id"] == "job-1"
        assert job_dict["pr_number"] == 1
        assert job_dict["status"] == "queued"
        assert job_dict["pr_info"]["title"] == "Test PR"
        assert job_dict["pr_info"]["additions"] == 100


class TestAsyncAnalysisQueue:
    """Test async analysis queue management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AsyncAnalysisConfig(
            max_queue_size=5, max_concurrent_workers=2, result_retention_hours=1
        )
        self.queue = AsyncAnalysisQueue(self.config)

    @pytest.mark.asyncio
    async def test_queue_initialization(self):
        """Test queue initializes correctly."""
        await self.queue.start()
        try:
            assert self.queue.config == self.config
            assert self.queue.job_queue.maxsize == 5
            assert len(self.queue.active_jobs) == 0
        finally:
            await self.queue.stop()

    @pytest.mark.asyncio
    async def test_queue_analysis(self):
        """Test queuing an analysis job."""
        await self.queue.start()
        try:
            # Mock resource monitor to allow jobs regardless of system load
            with patch(
                "vibe_check.tools.async_analysis.resource_monitor.get_global_resource_monitor"
            ) as mock_monitor:
                mock_monitor.return_value.should_accept_new_job.return_value = (
                    True,
                    "",
                )

                pr_data = {
                    "title": "Test PR",
                    "additions": 2000,
                    "deletions": 500,
                    "changed_files": 30,
                }

                job_id = await self.queue.queue_analysis(123, "owner/repo", pr_data)

            assert job_id.startswith("owner/repo#123#")
            assert job_id in self.queue.active_jobs
            assert self.queue.job_queue.qsize() == 1

            # Check job details
            job = self.queue.active_jobs[job_id]
            assert job.pr_number == 123
            assert job.repository == "owner/repo"
            assert job.status == JobStatus.QUEUED
        finally:
            await self.queue.stop()

    @pytest.mark.asyncio
    async def test_get_next_job(self):
        """Test getting next job from queue."""
        await self.queue.start()
        try:
            # Mock resource monitor to allow jobs regardless of system load
            with patch(
                "vibe_check.tools.async_analysis.resource_monitor.get_global_resource_monitor"
            ) as mock_monitor:
                mock_monitor.return_value.should_accept_new_job.return_value = (
                    True,
                    "",
                )

                pr_data = {"title": "Test", "additions": 1000, "deletions": 500}
                job_id = await self.queue.queue_analysis(1, "repo", pr_data)

            # Get next job
            job = await self.queue.get_next_job(timeout=1)

            assert job is not None
            assert job.job_id == job_id
            assert job.status == JobStatus.PROCESSING
            assert job.started_at is not None
        finally:
            await self.queue.stop()

    @pytest.mark.asyncio
    async def test_no_job_timeout(self):
        """Test timeout when no jobs available."""
        await self.queue.start()
        try:
            # Should timeout quickly with no jobs
            job = await self.queue.get_next_job(timeout=0.1)
            assert job is None
        finally:
            await self.queue.stop()

    def test_job_completion(self):
        """Test completing a job."""
        # Create and track a job
        pr_data = {"title": "Test"}
        job = AnalysisJob("job-1", 1, "repo", pr_data)
        self.queue.active_jobs["job-1"] = job

        # Complete the job
        result = {"analysis": "completed", "patterns": ["test"]}
        self.queue.complete_job("job-1", result)

        # Check job is completed
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.progress == 100
        assert self.queue.job_results["job-1"] == result

    def test_job_failure(self):
        """Test failing a job."""
        pr_data = {"title": "Test"}
        job = AnalysisJob("job-1", 1, "repo", pr_data)
        self.queue.active_jobs["job-1"] = job

        # Fail the job
        self.queue.fail_job("job-1", "Analysis error")

        # Check job is failed
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Analysis error"
        assert job.completed_at is not None

    def test_get_job_status(self):
        """Test getting job status."""
        pr_data = {"title": "Test PR"}
        job = AnalysisJob("job-1", 1, "repo", pr_data)
        self.queue.active_jobs["job-1"] = job

        status = self.queue.get_job_status("job-1")

        assert status is not None
        assert status["job_id"] == "job-1"
        assert status["status"] == "queued"
        assert status["pr_info"]["title"] == "Test PR"

    def test_queue_status(self):
        """Test getting overall queue status."""
        status = self.queue.get_queue_status()

        assert "queue_size" in status
        assert "active_jobs" in status
        assert "metrics" in status
        assert "config" in status
        assert status["max_queue_size"] == 5


class TestAsyncAnalysisWorker:
    """Test async analysis worker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AsyncAnalysisConfig(
            chunk_timeout_seconds=30, max_concurrent_workers=1
        )
        self.queue = AsyncAnalysisQueue(self.config)
        self.worker = AsyncAnalysisWorker(self.queue, "test-worker", self.config)

    @pytest.mark.asyncio
    async def test_worker_initialization(self):
        """Test worker initializes correctly."""
        assert self.worker.worker_id == "test-worker"
        assert self.worker.config == self.config
        assert not self.worker.running
        assert self.worker.current_job is None

    @pytest.mark.asyncio
    async def test_worker_process_job_success(self):
        """Test successful job processing."""
        # Create a test job
        pr_data = {
            "title": "Test",
            "additions": 1000,
            "deletions": 500,
            "changed_files": 20,
        }
        job = AnalysisJob("job-1", 1, "owner/repo", pr_data)

        # Mock GitHub operations and analysis
        with patch(
            "vibe_check.tools.shared.github_abstraction.get_default_github_operations"
        ) as mock_github:
            mock_github_ops = Mock()
            mock_github_ops.get_pull_request_files.return_value = Mock(
                success=True, data=[{"filename": "test.py", "patch": "test content"}]
            )
            mock_github.return_value = mock_github_ops

            # Mock chunked analysis
            with patch(
                "vibe_check.tools.pr_review.chunked_analyzer.ChunkedAnalyzer"
            ) as mock_coordinator:
                mock_result = Mock()
                mock_result.overall_assessment = "Good code"
                mock_result.patterns_detected = ["Pattern 1"]
                mock_result.recommendations = ["Add tests"]
                mock_result.total_chunks = 2
                mock_result.successful_chunks = 2
                mock_result.failed_chunks = 0
                mock_result.total_duration = 10.0
                mock_result.chunk_summaries = []

                mock_coordinator.return_value.analyze_pr_chunked.return_value = (
                    mock_result
                )

                # Process the job
                result = await self.worker._process_job(job)

                assert result.success
                assert result.job_id == "job-1"
                assert result.result is not None
                assert result.result["analysis_mode"] == "async_detailed_analysis"

    @pytest.mark.asyncio
    async def test_worker_process_job_failure(self):
        """Test job processing failure."""
        pr_data = {"title": "Test"}
        job = AnalysisJob("job-1", 1, "repo", pr_data)

        # Mock GitHub operations to fail
        with patch(
            "vibe_check.tools.shared.github_abstraction.get_default_github_operations"
        ) as mock_github:
            mock_github_ops = Mock()
            mock_github_ops.get_pull_request_files.return_value = Mock(
                success=False, error="GitHub API error"
            )
            mock_github.return_value = mock_github_ops

            # Process the job
            result = await self.worker._process_job(job)

            assert not result.success
            assert result.job_id == "job-1"
            assert "GitHub API error" in result.error


class TestAsyncWorkerManager:
    """Test async worker manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AsyncAnalysisConfig(max_concurrent_workers=2)
        self.queue = AsyncAnalysisQueue(self.config)
        self.manager = AsyncWorkerManager(self.queue, self.config)

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test manager initializes correctly."""
        assert len(self.manager.workers) == 0
        assert len(self.manager.worker_tasks) == 0

    @pytest.mark.asyncio
    async def test_start_and_stop_workers(self):
        """Test starting and stopping workers."""
        # Start workers
        await self.manager.start_workers()

        # Give event loop time to start worker tasks
        await asyncio.sleep(0.01)

        assert len(self.manager.workers) == 2
        assert len(self.manager.worker_tasks) == 2
        assert all(worker.running for worker in self.manager.workers)

        # Stop workers
        await self.manager.stop_workers()

        assert len(self.manager.workers) == 0
        assert len(self.manager.worker_tasks) == 0

    def test_get_worker_status(self):
        """Test getting worker status."""
        # Add mock workers
        worker1 = Mock()
        worker1.worker_id = "worker-1"
        worker1.running = True
        worker1.current_job = None

        worker2 = Mock()
        worker2.worker_id = "worker-2"
        worker2.running = True
        worker2.current_job = Mock()
        worker2.current_job.job_id = "job-1"
        worker2.current_job.repository = "repo"
        worker2.current_job.pr_number = 123

        self.manager.workers = [worker1, worker2]

        status = self.manager.get_worker_status()

        assert len(status) == 2
        assert status[0]["worker_id"] == "worker-1"
        assert status[0]["current_job"] is None
        assert status[1]["worker_id"] == "worker-2"
        assert status[1]["current_job"] == "job-1"


class TestStatusTracker:
    """Test status tracking system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AsyncAnalysisConfig()
        self.tracker = StatusTracker(self.config)
        self.queue = AsyncAnalysisQueue(self.config)

    def test_phase_determination(self):
        """Test determining analysis phase from job status."""
        # Queued job
        job_status = {"status": "queued", "progress": 0}
        phase = self.tracker._determine_phase(job_status)
        assert phase == AnalysisPhase.QUEUED

        # Processing - fetching data
        job_status = {"status": "processing", "progress": 15}
        phase = self.tracker._determine_phase(job_status)
        assert phase == AnalysisPhase.FETCHING_DATA

        # Processing - analyzing
        job_status = {"status": "processing", "progress": 50}
        phase = self.tracker._determine_phase(job_status)
        assert phase == AnalysisPhase.ANALYZING

        # Completed
        job_status = {"status": "completed", "progress": 100}
        phase = self.tracker._determine_phase(job_status)
        assert phase == AnalysisPhase.COMPLETED

    def test_timing_calculations(self):
        """Test timing information calculations."""
        now = time.time()
        job_status = {
            "queued_at": now - 300,  # 5 minutes ago
            "started_at": now - 180,  # 3 minutes ago
            "estimated_completion": now + 120,  # 2 minutes from now
        }

        timing = self.tracker._calculate_timing_info(job_status)

        # Allow 2 second tolerance for timing calculations (avoids flakiness)
        assert abs(timing["queued_duration_seconds"] - 300) <= 2
        assert abs(timing["processing_duration_seconds"] - 180) <= 2
        assert abs(timing["time_remaining_seconds"] - 120) <= 2

    def test_user_friendly_status(self):
        """Test generation of user-friendly status messages."""
        timing_info = {"queued_duration_seconds": 60}
        job_status = {
            "status": "queued",
            "progress": 0,
            "pr_info": {"title": "Test PR", "additions": 500, "changed_files": 10},
        }

        status = self.tracker._generate_user_friendly_status(job_status, timing_info)

        assert "queued" in status["message"].lower()
        # Friendly description includes PR stats, not necessarily the title
        assert "10 files" in status["friendly_description"]
        assert "500 lines" in status["friendly_description"]
        assert status["current_activity"] == "Waiting for available worker"

    def test_comprehensive_status(self):
        """Test comprehensive status generation."""
        # Mock queue with job status
        self.queue.active_jobs["job-1"] = AnalysisJob(
            "job-1", 123, "owner/repo", {"title": "Test PR"}
        )

        status = self.tracker.get_comprehensive_status("job-1", self.queue)

        assert status is not None
        assert status["job_id"] == "job-1"
        assert "message" in status
        assert "timing" in status
        assert "pr_info" in status
        assert "available_actions" in status


class TestAsyncIntegration:
    """Test async analysis integration functions."""

    @pytest.mark.asyncio
    async def test_start_async_analysis_suitable_pr(self):
        """Test starting async analysis for suitable PR."""
        pr_data = {
            "title": "Large PR",
            "additions": 2000,
            "deletions": 500,
            "changed_files": 35,
        }

        # Mock the queue operations
        with patch(
            "vibe_check.tools.async_analysis.integration.get_global_queue"
        ) as mock_queue:
            mock_queue_instance = AsyncMock()
            mock_queue_instance.queue_analysis.return_value = "job-123"
            mock_queue.return_value = mock_queue_instance

            with patch(
                "vibe_check.tools.async_analysis.integration._status_tracker"
            ) as mock_tracker:
                mock_tracker.get_comprehensive_status.return_value = {
                    "job_id": "job-123",
                    "timing": {"estimated_completion_timestamp": time.time() + 600},
                }

                result = await start_async_analysis(123, "owner/repo", pr_data)

                assert result["status"] == "queued_for_async_analysis"
                assert result["job_id"] == "job-123"
                assert "immediate_analysis" in result
                assert "instructions" in result

    @pytest.mark.asyncio
    async def test_start_async_analysis_unsuitable_pr(self):
        """Test starting async analysis for PR that's not suitable."""
        pr_data = {
            "title": "Small PR",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
        }

        result = await start_async_analysis(123, "owner/repo", pr_data)

        assert result["status"] == "not_suitable"
        assert "not large enough" in result["message"]
        assert "pr_size_info" in result

    @pytest.mark.asyncio
    async def test_check_analysis_status(self):
        """Test checking analysis status."""
        # Mock the queue and status tracker
        with patch(
            "vibe_check.tools.async_analysis.integration.get_global_queue"
        ) as mock_queue:
            mock_queue_instance = AsyncMock()
            mock_queue.return_value = mock_queue_instance

            with patch(
                "vibe_check.tools.async_analysis.integration._status_tracker"
            ) as mock_tracker:
                mock_status = {
                    "job_id": "job-123",
                    "status": "processing",
                    "progress_percent": 50,
                }
                mock_tracker.get_comprehensive_status.return_value = mock_status

                result = await check_analysis_status("job-123")

                assert result["status"] == "status_retrieved"
                assert result["job_status"]["job_id"] == "job-123"

    @pytest.mark.asyncio
    async def test_check_status_not_found(self):
        """Test checking status for non-existent job."""
        with patch(
            "vibe_check.tools.async_analysis.integration.get_global_queue"
        ) as mock_queue:
            mock_queue_instance = AsyncMock()
            mock_queue.return_value = mock_queue_instance

            with patch(
                "vibe_check.tools.async_analysis.integration._status_tracker"
            ) as mock_tracker:
                mock_tracker.get_comprehensive_status.return_value = None

                result = await check_analysis_status("nonexistent-job")

                assert result["status"] == "not_found"
                assert "not found" in result["error"]


class TestAsyncAnalysisMetrics:
    """Test metrics tracking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.metrics = AsyncAnalysisMetrics()

    def test_metrics_initialization(self):
        """Test metrics initialize correctly."""
        assert self.metrics.jobs_queued == 0
        assert self.metrics.jobs_completed == 0
        assert self.metrics.jobs_failed == 0
        assert self.metrics.total_analysis_time == 0.0

    def test_record_job_events(self):
        """Test recording job events."""
        # Record queued job
        self.metrics.record_job_queued()
        assert self.metrics.jobs_queued == 1

        # Record completed job
        self.metrics.record_job_completed(120.5)
        assert self.metrics.jobs_completed == 1
        assert self.metrics.total_analysis_time == 120.5

        # Record failed job
        self.metrics.record_job_failed()
        assert self.metrics.jobs_failed == 1

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        # No jobs yet
        assert self.metrics.get_success_rate() == 100.0

        # Add some jobs
        self.metrics.record_job_completed(100)
        self.metrics.record_job_completed(200)
        self.metrics.record_job_failed()

        # Success rate should be 2/3 = 66.67%
        success_rate = self.metrics.get_success_rate()
        assert abs(success_rate - 66.67) < 0.1

    def test_average_duration(self):
        """Test average duration calculation."""
        # No completed jobs
        assert self.metrics.get_average_duration() == 0.0

        # Add completed jobs
        self.metrics.record_job_completed(100)
        self.metrics.record_job_completed(200)

        # Average should be 150
        assert self.metrics.get_average_duration() == 150.0

    def test_metrics_export(self):
        """Test exporting metrics as dictionary."""
        self.metrics.record_job_queued()
        self.metrics.record_job_completed(100)

        metrics_dict = self.metrics.to_dict()

        assert metrics_dict["jobs_queued"] == 1
        assert metrics_dict["jobs_completed"] == 1
        assert metrics_dict["success_rate_percent"] == 100.0
        assert metrics_dict["average_duration_seconds"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
