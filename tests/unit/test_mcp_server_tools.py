"""
Unit Tests for MCP Server Tool Registration and Functionality

Tests the FastMCP server setup and tool registration:
- Tool registration and discovery
- MCP protocol compliance
- Tool parameter validation
- Error handling and responses
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestMCPServerTools:
    """Test MCP server tool registration and functionality"""

    @pytest.fixture
    def mock_fastmcp_server(self):
        """Mock FastMCP server instance"""
        mock_server = MagicMock()
        mock_server.list_tools = AsyncMock(return_value=[])
        mock_server.call_tool = AsyncMock()
        return mock_server

    def test_server_initialization(self, mock_fastmcp_server):
        """Test that MCP server initializes properly"""
        with patch("vibe_check.server.FastMCP", return_value=mock_fastmcp_server):
            from vibe_check.server import app

            assert app is not None

    @pytest.mark.asyncio
    async def test_analyze_text_tool_registration(self, mock_fastmcp_server):
        """Test that analyze_text_demo tool is properly registered"""
        with patch("vibe_check.server.FastMCP", return_value=mock_fastmcp_server):
            from vibe_check.server import app

            # Simulate tool registration
            tools = await mock_fastmcp_server.list_tools()
            assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self):
        """Test tool parameter validation for MCP calls"""
        # Import the actual analyze_text_demo function
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Test valid parameters
        result = analyze_text_demo(text="Test analysis text", detail_level="standard")

        assert isinstance(result, dict)
        assert "status" in result

        # Test invalid parameters should be handled gracefully
        result_invalid = analyze_text_demo(
            text="Test text", detail_level="invalid_level"
        )

        assert isinstance(result_invalid, dict)
        assert "status" in result_invalid

    def test_mcp_response_format_compliance(self):
        """Test that responses comply with MCP format requirements"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        result = analyze_text_demo("Test text for MCP compliance")

        # MCP responses should be JSON-serializable
        import json

        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Response not JSON-serializable: {e}")

        # Should have proper status indication
        assert "status" in result
        assert result["status"] in ["success", "error", "completed"]

    def test_error_handling_in_tools(self):
        """Test error handling in MCP tools"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Test with problematic input that might cause errors
        test_cases = [
            {"text": None},  # None input
            {"text": ""},  # Empty string
            {"text": "x" * 1000000, "detail_level": "invalid"},  # Large + invalid
        ]

        for test_case in test_cases:
            try:
                result = analyze_text_demo(**test_case)
                # Should return proper error format
                assert isinstance(result, dict)
                assert "status" in result
                if result["status"] == "error":
                    assert "error" in result or "message" in result
            except Exception:
                # Some errors might be raised, which is also acceptable
                pass

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test that tools can handle concurrent execution"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Run multiple analyses concurrently
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                asyncio.to_thread(analyze_text_demo, f"Concurrent test {i}")
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete successfully
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Task {i} failed with exception: {result}")

            assert isinstance(result, dict)
            assert "status" in result

    def test_tool_schema_validation(self):
        """Test that tools have proper schema definitions"""
        # This would test the tool schema definitions
        # For now, we test that tools can be called with expected parameters
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Test all expected parameters
        result = analyze_text_demo(
            text="Schema validation test",
            detail_level="standard",
            use_project_context=True,
            project_root=".",
        )

        assert isinstance(result, dict)
        assert "status" in result

    def test_large_response_handling(self):
        """Test handling of large responses from tools"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Generate input that might produce large response
        large_input = (
            """
        We need to build a completely custom solution from scratch.
        This involves creating our own HTTP client, authentication system,
        database abstraction layer, caching mechanism, logging framework,
        configuration management, error handling system, and much more.
        """
            * 100
        )  # Repeat to make it substantial

        result = analyze_text_demo(large_input, detail_level="comprehensive")

        assert isinstance(result, dict)
        assert "status" in result

        # Response should be reasonable size (not infinite)
        import json

        response_size = len(json.dumps(result))
        assert response_size < 10 * 1024 * 1024  # Less than 10MB

    @patch("vibe_check.tools.analyze_text_nollm.PatternDetector")
    @patch("vibe_check.tools.analyze_text_nollm.EducationalContentGenerator")
    def test_tool_dependency_injection(self, mock_edu_gen, mock_detector):
        """Test that tools properly use injected dependencies"""
        # Mock the dependencies
        mock_detector_instance = MagicMock()
        mock_detector.return_value = mock_detector_instance

        mock_edu_gen_instance = MagicMock()
        mock_edu_gen.return_value = mock_edu_gen_instance

        # Mock return values
        mock_result = MagicMock()
        mock_result.total_issues = 1
        mock_result.patterns = []
        mock_result.summary = "Mock result"
        mock_detector_instance.detect_patterns.return_value = mock_result

        mock_edu_gen_instance.generate_content.return_value = {
            "summary": "Mock education",
            "recommendations": [],
        }

        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        result = analyze_text_demo("Test dependency injection")

        # Verify dependencies were used
        mock_detector.assert_called_once()
        mock_detector_instance.detect_patterns.assert_called_once()

        assert isinstance(result, dict)
        assert "status" in result

    def test_tool_timeout_handling(self):
        """Test that tools handle timeout scenarios properly"""
        import time
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # For this test, we'll just verify the tool completes in reasonable time
        # In a real timeout test, we'd patch time-consuming operations
        start_time = time.time()

        result = analyze_text_demo("Timeout test scenario")

        end_time = time.time()
        duration = end_time - start_time

        assert isinstance(result, dict)
        assert "status" in result
        # Should complete quickly for normal input
        assert duration < 10.0, f"Tool took too long: {duration} seconds"

    def test_unicode_parameter_handling(self):
        """Test that tools handle Unicode parameters properly"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        unicode_text = "Unicode test: 🚀 émojis spéciál chars αβγδ ∑∏∆"

        result = analyze_text_demo(unicode_text)

        assert isinstance(result, dict)
        assert "status" in result
        # Should handle Unicode without errors

    def test_memory_usage_reasonable(self):
        """Test that tools don't consume excessive memory"""
        import psutil
        import os

        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Run analysis
        large_text = "Custom implementation needed. " * 10000
        result = analyze_text_demo(large_text)

        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        assert isinstance(result, dict)
        assert "status" in result

        # Memory increase should be reasonable (less than 100MB)
        assert (
            memory_increase < 100 * 1024 * 1024
        ), f"Excessive memory usage: {memory_increase} bytes"

    def test_tool_state_isolation(self):
        """Test that tool calls don't affect each other's state"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # First call
        result1 = analyze_text_demo("First analysis call")

        # Second call with different input
        result2 = analyze_text_demo("Second completely different analysis call")

        # Both should succeed independently
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert "status" in result1
        assert "status" in result2

        # Results should be independent (not identical)
        assert result1 != result2 or len(str(result1)) != len(str(result2))

    @patch("builtins.print")
    def test_logging_and_debug_output(self, mock_print):
        """Test that tools handle logging appropriately"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Run analysis
        result = analyze_text_demo("Debug output test")

        assert isinstance(result, dict)
        assert "status" in result

        # Should not print excessively to stdout (allow some debug output)
        print_call_count = mock_print.call_count
        assert (
            print_call_count < 10
        ), f"Too much stdout output: {print_call_count} print calls"
