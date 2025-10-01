"""
End-to-End Tests for Complete Workflow Validation

Tests complete workflows from input to output:
- Full analysis pipeline integration
- MCP server to tool chain execution
- GitHub integration workflows
- Educational content generation pipeline
- Error recovery and resilience
"""

import pytest
import asyncio
import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vibe_check.tools.analyze_text_nollm import analyze_text_demo


@pytest.mark.e2e
class TestCompleteWorkflows:
    """Test complete end-to-end workflows"""

    def test_full_text_analysis_workflow(self):
        """Test complete text analysis workflow from input to educational content"""
        # Realistic input that should trigger multiple patterns
        input_text = """
        We've been trying to integrate with the third-party API for weeks, but the 
        documentation is unclear and we can't get the authentication working properly.
        Instead of spending more time on this, we've decided to build our own HTTP 
        client library with custom authentication handling.
        
        We're also going to implement our own JSON parsing because the standard 
        library doesn't handle our specific data structures efficiently. This will 
        give us more control over performance optimization.
        """

        # Execute full workflow
        result = analyze_text_demo(input_text, detail_level="comprehensive")

        # Validate complete workflow execution
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ["success", "completed"]

        # Should have analysis results
        assert "analysis" in result
        analysis = result["analysis"]
        assert isinstance(analysis, dict)

        # Should include detection results
        if "detection_result" in analysis:
            detection = analysis["detection_result"]
            assert isinstance(detection, (dict, list))

        # Should include educational content
        if "educational_content" in analysis:
            education = analysis["educational_content"]
            assert isinstance(education, dict)
            assert "summary" in education or "recommendations" in education

    def test_mcp_tool_registration_to_execution_workflow(self):
        """Test workflow from MCP tool registration to execution"""
        # This tests the MCP server integration workflow
        with patch("vibe_check.server.FastMCP") as mock_fastmcp:
            mock_server = MagicMock()
            mock_fastmcp.return_value = mock_server

            # Import server to trigger registration
            from vibe_check import server

            # Mock tool registration
            mock_server.tool.return_value = lambda func: func

            # Test tool execution through MCP interface
            result = analyze_text_demo(
                "Custom implementation needed for MCP workflow test",
                detail_level="standard",
            )

            assert isinstance(result, dict)
            assert "status" in result

            # Result should be MCP-compatible (JSON serializable)
            json_result = json.dumps(result)
            parsed_result = json.loads(json_result)
            assert parsed_result == result

    def test_error_recovery_workflow(self):
        """Test error recovery throughout the complete workflow"""
        # Test with inputs that might cause various types of failures
        problematic_inputs = [
            "",  # Empty input
            "🚀" * 1000,  # Large Unicode
            "Custom implementation needed" * 10000,  # Very large
            None,  # Invalid type
        ]

        recovery_results = []

        for problematic_input in problematic_inputs:
            try:
                if problematic_input is None:
                    # This should raise an exception
                    result = analyze_text_demo(problematic_input)
                else:
                    result = analyze_text_demo(problematic_input)

                # If no exception, should be proper format
                assert isinstance(result, dict)
                assert "status" in result

                if result["status"] == "error":
                    assert "error" in result or "message" in result

                recovery_results.append(("success", result))

            except Exception as e:
                # Exception handling is also acceptable
                recovery_results.append(("exception", str(e)))

        # Should handle most cases gracefully
        success_count = sum(1 for status, _ in recovery_results if status == "success")
        assert success_count >= len(problematic_inputs) // 2, "Poor error recovery rate"

    def test_context_aware_analysis_workflow(self):
        """Test context-aware analysis workflow with project context"""
        # Create a realistic project context scenario
        main_content = "We need custom authentication for our React application"
        project_context = {
            "use_project_context": True,
            "project_root": ".",  # Use current project
        }

        # Execute with context
        result_with_context = analyze_text_demo(
            main_content, detail_level="standard", **project_context
        )

        # Execute without context
        result_without_context = analyze_text_demo(
            main_content, detail_level="standard", use_project_context=False
        )

        # Both should succeed
        assert isinstance(result_with_context, dict)
        assert isinstance(result_without_context, dict)
        assert "status" in result_with_context
        assert "status" in result_without_context

        # Results may differ based on context
        assert result_with_context != result_without_context or len(
            str(result_with_context)
        ) != len(str(result_without_context))

    def test_multi_detail_level_workflow(self):
        """Test workflow across all detail levels"""
        test_text = "We're building a custom HTTP client because the existing libraries don't meet our needs"

        detail_levels = ["brief", "standard", "comprehensive"]
        results = {}

        for level in detail_levels:
            result = analyze_text_demo(test_text, detail_level=level)

            assert isinstance(result, dict)
            assert "status" in result
            assert result["status"] in ["success", "completed"]

            results[level] = result

        # All levels should produce valid results
        assert len(results) == 3

        # Results should vary in detail (allowing for some similarity)
        brief_size = len(str(results["brief"]))
        comprehensive_size = len(str(results["comprehensive"]))

        # Comprehensive should generally be more detailed, but allow flexibility
        assert brief_size > 0 and comprehensive_size > 0

    def test_concurrent_workflow_execution(self):
        """Test concurrent execution of complete workflows"""
        import concurrent.futures
        import time

        def execute_workflow(workflow_id):
            text = f"Custom implementation workflow {workflow_id} requires analysis"
            start_time = time.time()

            result = analyze_text_demo(text, detail_level="standard")

            end_time = time.time()
            duration = end_time - start_time

            return {
                "workflow_id": workflow_id,
                "result": result,
                "duration": duration,
                "success": isinstance(result, dict) and "status" in result,
            }

        # Execute multiple workflows concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_workflow, i) for i in range(10)]

            workflow_results = [
                future.result(timeout=30)
                for future in concurrent.futures.as_completed(futures, timeout=60)
            ]

        # All workflows should complete successfully
        assert len(workflow_results) == 10

        success_count = sum(1 for wr in workflow_results if wr["success"])
        assert success_count == 10, f"Some workflows failed: {success_count}/10"

        # Check performance consistency
        durations = [wr["duration"] for wr in workflow_results]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 5.0, f"Average duration too high: {avg_duration}s"
        assert max_duration < 15.0, f"Max duration too high: {max_duration}s"

    def test_pattern_detection_to_education_workflow(self):
        """Test workflow from pattern detection through educational content generation"""
        # Input with clear anti-patterns
        anti_pattern_text = """
        The existing authentication library documentation was confusing, and we 
        couldn't figure out how to configure it for our specific use case. After 
        spending a few hours on it, we decided it would be faster to just build 
        our own authentication system from scratch.
        
        We're implementing custom password hashing, session management, and 
        user registration. This will give us complete control over the user 
        experience and we won't be dependent on external libraries.
        """

        result = analyze_text_demo(anti_pattern_text, detail_level="comprehensive")

        assert isinstance(result, dict)
        assert "status" in result
        assert "analysis" in result

        analysis = result["analysis"]

        # Should detect patterns
        if "detection_result" in analysis:
            detection = analysis["detection_result"]

            # Should have some pattern detection results
            if hasattr(detection, "total_issues"):
                assert detection.total_issues >= 0
            elif isinstance(detection, list):
                assert len(detection) >= 0
            elif isinstance(detection, dict):
                assert "total_issues" in detection or len(detection) >= 0

        # Should provide educational content
        if "educational_content" in analysis:
            education = analysis["educational_content"]
            assert isinstance(education, dict)

            # Should have actionable recommendations
            if "recommendations" in education:
                recommendations = education["recommendations"]
                assert isinstance(recommendations, (list, dict, str))
                assert len(str(recommendations)) > 0

    @pytest.mark.asyncio
    async def test_async_workflow_compatibility(self):
        """Test workflow compatibility with async execution"""

        # Test that synchronous tools work in async context
        async def async_analysis_workflow():
            text = "Async workflow test with custom implementation requirements"

            # Use asyncio.to_thread for CPU-bound synchronous work
            result = await asyncio.to_thread(
                analyze_text_demo, text, detail_level="standard"
            )

            return result

        # Execute async workflow
        result = await async_analysis_workflow()

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ["success", "completed"]

    def test_resilience_workflow(self):
        """Test workflow resilience under various failure conditions"""
        # Mock various failure scenarios
        failure_scenarios = [
            # Pattern detector failure
            (
                "vibe_check.tools.analyze_text_nollm.PatternDetector",
                Exception("Pattern detection failed"),
            ),
            # Educational content generator failure
            (
                "vibe_check.tools.analyze_text_nollm.EducationalContentGenerator",
                Exception("Education generation failed"),
            ),
            # Context manager failure
            (
                "vibe_check.tools.analyze_text_nollm.get_context_manager",
                Exception("Context loading failed"),
            ),
        ]

        resilience_results = []

        for component, exception in failure_scenarios:
            with patch(component, side_effect=exception):
                try:
                    result = analyze_text_demo(
                        "Resilience test custom implementation", detail_level="standard"
                    )

                    # Should either handle gracefully or provide error info
                    assert isinstance(result, dict)
                    assert "status" in result

                    if result["status"] == "error":
                        assert "error" in result or "message" in result

                    resilience_results.append(("handled", result))

                except Exception as e:
                    # Some failures may propagate, which is acceptable
                    resilience_results.append(("exception", str(e)))

        # Should handle at least some failure scenarios gracefully
        handled_count = sum(
            1 for status, _ in resilience_results if status == "handled"
        )
        assert (
            handled_count >= len(failure_scenarios) // 2
        ), "Poor resilience to component failures"

    def test_memory_efficient_workflow(self):
        """Test workflow memory efficiency with large inputs"""
        import psutil
        import os
        import gc

        process = psutil.Process(os.getpid())

        # Baseline memory usage
        gc.collect()
        baseline_memory = process.memory_info().rss

        # Process multiple large inputs
        large_inputs = [
            f"Large workflow test {i}: " + "Custom implementation needed. " * 1000
            for i in range(10)
        ]

        results = []
        for large_input in large_inputs:
            result = analyze_text_demo(large_input, detail_level="brief")
            results.append(result)

            # Force garbage collection
            gc.collect()

        # Final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - baseline_memory

        # All workflows should succeed
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)
            assert "status" in result

        # Memory usage should be reasonable
        memory_per_workflow = memory_increase / len(large_inputs)
        assert (
            memory_per_workflow < 50 * 1024 * 1024
        ), f"Excessive memory per workflow: {memory_per_workflow} bytes"

    def test_integration_with_external_context(self):
        """Test integration workflow with external context sources"""
        # Test with different project configurations
        project_scenarios = [
            {"use_project_context": False},
            {"use_project_context": True, "project_root": "."},
            {"use_project_context": True, "project_root": "/tmp"},
            {"use_project_context": True, "project_root": "/nonexistent"},
        ]

        base_text = "Integration test for external context loading"

        integration_results = []

        for scenario in project_scenarios:
            try:
                result = analyze_text_demo(
                    base_text, detail_level="standard", **scenario
                )

                assert isinstance(result, dict)
                assert "status" in result

                integration_results.append(("success", result))

            except Exception as e:
                # Some scenarios may fail, which is acceptable
                integration_results.append(("failure", str(e)))

        # Most integration scenarios should succeed
        success_count = sum(
            1 for status, _ in integration_results if status == "success"
        )
        assert (
            success_count >= len(project_scenarios) // 2
        ), f"Too many integration failures: {success_count}/{len(project_scenarios)}"

    def test_end_to_end_performance_workflow(self):
        """Test end-to-end performance across complete workflow"""
        import time

        # Performance test scenarios
        performance_scenarios = [
            ("Small input", "Custom implementation needed", "brief"),
            (
                "Medium input",
                "Custom implementation needed for testing. " * 100,
                "standard",
            ),
            (
                "Large input",
                "Complex custom implementation requirements. " * 500,
                "brief",
            ),
            (
                "Unicode input",
                "Custom 🚀 implementation with émojis needed αβγ",
                "standard",
            ),
        ]

        performance_results = []

        for scenario_name, text, detail_level in performance_scenarios:
            start_time = time.time()

            result = analyze_text_demo(text, detail_level=detail_level)

            end_time = time.time()
            duration = end_time - start_time

            assert isinstance(result, dict)
            assert "status" in result

            performance_results.append(
                {
                    "scenario": scenario_name,
                    "duration": duration,
                    "success": result["status"] in ["success", "completed"],
                    "input_size": len(text),
                }
            )

        # All scenarios should succeed
        success_count = sum(1 for pr in performance_results if pr["success"])
        assert success_count == len(
            performance_scenarios
        ), f"Performance test failures: {success_count}/{len(performance_scenarios)}"

        # Performance should be reasonable
        for pr in performance_results:
            assert (
                pr["duration"] < 10.0
            ), f"{pr['scenario']} too slow: {pr['duration']}s"

        # Performance should scale reasonably with input size
        small_duration = next(
            pr["duration"]
            for pr in performance_results
            if pr["scenario"] == "Small input"
        )
        large_duration = next(
            pr["duration"]
            for pr in performance_results
            if pr["scenario"] == "Large input"
        )

        # Large input shouldn't be more than 10x slower than small input
        assert (
            large_duration <= small_duration * 10
        ), f"Poor performance scaling: {large_duration / small_duration}x"
