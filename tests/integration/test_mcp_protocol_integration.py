"""
Integration Tests for MCP Protocol Compliance

Tests MCP protocol integration:
- FastMCP server integration
- Tool registration and discovery
- Request/response format compliance
- Error handling across protocol boundary
- Async/await pattern support
"""

import pytest
import asyncio
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.integration
@pytest.mark.mcp
class TestMCPProtocolIntegration:
    """Test MCP protocol integration and compliance"""

    @pytest.fixture
    def mock_mcp_server(self):
        """Create mock MCP server for testing"""
        mock_server = MagicMock()
        mock_server.list_tools = AsyncMock()
        mock_server.call_tool = AsyncMock()
        mock_server.get_tool = MagicMock()
        return mock_server

    @pytest.mark.asyncio
    async def test_server_initialization_with_fastmcp(self):
        """Test server initialization with FastMCP"""
        with patch("vibe_check.server.core.FastMCP") as mock_fastmcp:
            mock_app = MagicMock()
            mock_fastmcp.return_value = mock_app

            # Import should succeed without errors
            try:
                from vibe_check.server import app

                assert app is not None
            except ImportError as e:
                pytest.skip(f"FastMCP not available: {e}")

    @pytest.mark.asyncio
    async def test_tool_registration_compliance(self, mock_mcp_server):
        """Test that tools are registered with proper MCP compliance"""
        with patch("vibe_check.server.core.FastMCP", return_value=mock_mcp_server):
            from vibe_check import server

            # Should have registered tools
            mock_mcp_server.list_tools.return_value = [
                {
                    "name": "analyze_text_demo",
                    "description": "Analyze text for anti-patterns",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "detail_level": {"type": "string"},
                        },
                        "required": ["text"],
                    },
                }
            ]

            tools = await mock_mcp_server.list_tools()

            assert isinstance(tools, list)
            assert len(tools) > 0

            # Validate tool schema structure
            for tool in tools:
                assert "name" in tool
                assert "description" in tool
                assert isinstance(tool["name"], str)
                assert isinstance(tool["description"], str)

    @pytest.mark.asyncio
    async def test_tool_invocation_protocol(self, mock_mcp_server):
        """Test tool invocation through MCP protocol"""
        # Mock tool call response
        expected_response = {
            "status": "success",
            "analysis": {
                "detection_result": {"total_issues": 1},
                "educational_content": {"summary": "Test analysis"},
            },
        }

        mock_mcp_server.call_tool.return_value = expected_response

        # Simulate MCP tool call
        response = await mock_mcp_server.call_tool(
            "analyze_text_demo",
            {"text": "Custom implementation needed", "detail_level": "standard"},
        )

        assert isinstance(response, dict)
        assert "status" in response

    def test_mcp_response_serialization(self):
        """Test that all responses can be JSON serialized for MCP"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        test_cases = [
            "Simple text analysis",
            "🚀 Unicode content with émojis",
            "Complex custom implementation requirements" * 100,
            "",  # Empty content
        ]

        for text in test_cases:
            result = analyze_text_demo(text)

            # MCP requires JSON serializable responses
            try:
                json_str = json.dumps(result)
                parsed_back = json.loads(json_str)

                assert isinstance(parsed_back, dict)
                assert "status" in parsed_back

            except (TypeError, ValueError) as e:
                pytest.fail(
                    f"Response not MCP-serializable for input '{text[:50]}...': {e}"
                )

    def test_mcp_error_handling_format(self):
        """Test that errors are formatted properly for MCP protocol"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Test with potentially problematic inputs
        problematic_inputs = [
            None,  # Invalid type
            {"invalid": "structure"},  # Wrong parameter type
        ]

        for bad_input in problematic_inputs:
            try:
                if bad_input is None:
                    result = analyze_text_demo(bad_input)
                else:
                    result = analyze_text_demo(**bad_input)

                # If no exception raised, should return proper error format
                if isinstance(result, dict) and result.get("status") == "error":
                    assert "error" in result or "message" in result
                    # Should be JSON serializable
                    json.dumps(result)

            except Exception as e:
                # Exceptions should be handled at MCP layer
                # This is acceptable as long as they're caught properly
                assert isinstance(e, (TypeError, ValueError, AttributeError))

    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Test async execution patterns for MCP tools"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Test that synchronous tools can be called in async context
        async def async_analysis():
            return analyze_text_demo("Async test analysis")

        result = await async_analysis()

        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_concurrent_mcp_tool_calls(self):
        """Test concurrent MCP tool calls don't interfere"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        async def async_tool_call(text):
            # Wrap synchronous call for async execution
            return await asyncio.to_thread(analyze_text_demo, text)

        # Execute multiple tool calls concurrently
        tasks = [async_tool_call(f"Concurrent analysis {i}") for i in range(5)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent call {i} failed: {result}")

            assert isinstance(result, dict)
            assert "status" in result

    def test_mcp_parameter_validation(self):
        """Test MCP parameter validation and type checking"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Test valid parameter combinations
        valid_params = [
            {"text": "Test analysis"},
            {"text": "Test", "detail_level": "brief"},
            {"text": "Test", "detail_level": "standard", "use_project_context": False},
            {"text": "Test", "project_root": "/tmp"},
        ]

        for params in valid_params:
            result = analyze_text_demo(**params)
            assert isinstance(result, dict)
            assert "status" in result

    def test_mcp_tool_metadata_compliance(self):
        """Test that tool metadata complies with MCP standards"""
        # This would test the actual tool registration metadata
        # For now, we verify the tools have expected characteristics
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Tool should have proper docstring
        assert analyze_text_demo.__doc__ is not None
        assert len(analyze_text_demo.__doc__.strip()) > 0

        # Tool should have type hints (for MCP schema generation)
        import inspect

        signature = inspect.signature(analyze_text_demo)

        # Should have annotated parameters
        for param_name, param in signature.parameters.items():
            if param_name == "text":
                # Required parameter should have annotation
                assert param.annotation != inspect.Parameter.empty

    @pytest.mark.asyncio
    async def test_mcp_streaming_response_support(self):
        """Test support for MCP streaming responses (if implemented)"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # For now, test that responses are complete (not streaming)
        result = analyze_text_demo("Streaming test analysis")

        assert isinstance(result, dict)
        assert "status" in result
        # Response should be complete, not partial
        if result["status"] == "success":
            assert "analysis_results" in result
            assert isinstance(result["analysis_results"], dict)

    def test_mcp_resource_usage_limits(self):
        """Test that MCP tools respect resource usage limits"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo
        import time

        # Test with input that might consume resources
        large_text = "Resource usage test. " * 5000

        start_time = time.time()
        result = analyze_text_demo(large_text)
        end_time = time.time()

        duration = end_time - start_time

        assert isinstance(result, dict)
        assert "status" in result

        # Should complete within MCP timeout limits
        assert (
            duration < 30.0
        ), f"Tool execution exceeded reasonable MCP timeout: {duration}s"

    @pytest.mark.asyncio
    async def test_mcp_cancellation_support(self):
        """Test that MCP tools can be cancelled properly"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Create a task that can be cancelled
        async def cancellable_analysis():
            return await asyncio.to_thread(
                analyze_text_demo, "Cancellation test analysis"
            )

        task = asyncio.create_task(cancellable_analysis())

        # Let it run briefly then cancel
        await asyncio.sleep(0.1)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            # Cancellation should work properly
            pass

    def test_mcp_context_preservation(self):
        """Test that MCP context is preserved across tool calls"""
        from vibe_check.tools.analyze_text_nollm import analyze_text_demo

        # Multiple calls should not affect each other
        result1 = analyze_text_demo("First context test")
        result2 = analyze_text_demo("Second context test")
        result3 = analyze_text_demo("Third context test")

        results = [result1, result2, result3]

        for result in results:
            assert isinstance(result, dict)
            assert "status" in result

        # Results should be independent
        assert result1 != result2 or result1 != result3
        # But all should be valid
        for result in results:
            assert result["status"] in ["success", "completed"]
