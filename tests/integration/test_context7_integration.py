"""
Integration tests for Context7 MCP server integration.
Tests the Context7Manager and MCP tools for proper functionality,
caching behavior, knowledge base integration, and error handling.
"""

import pytest
import asyncio
from unittest.mock import MagicMock

# Import the Context7 components
from vibe_check.server.tools.context7_integration import (
    Context7Manager,
    register_context7_tools,
)


# Mock MCP Client
class MockMCPClient:
    def __init__(self):
        self.tools = {}

    def tool(self, name, description):
        def decorator(func):
            self.tools[name] = {"function": func, "description": description}
            return func

        return decorator

    async def call_tool(self, tool_name, **kwargs):
        if tool_name == "mcp__Context7__resolve-library-id":
            library_name = kwargs.get("libraryName")
            if library_name == "react":
                return {
                    "libraries": [
                        {
                            "title": "React",
                            "library_id": "/facebook/react",
                            "description": "A JavaScript library for building user interfaces.",
                            "code_snippets": 5000,
                            "trust_score": 9.5,
                        }
                    ]
                }
            return None
        elif tool_name == "mcp__Context7__get-library-docs":
            return {"documentation": "Mock documentation"}
        return None


@pytest.fixture
def manager():
    """Fixture for a Context7Manager with a mock MCP client."""
    return Context7Manager(mcp_client=MockMCPClient())


class TestContext7Manager:
    """Test Context7Manager core functionality."""

    def test_manager_initialization(self, manager):
        """Test Context7Manager initialization with proper defaults."""
        assert manager._max_cache_size == 1000
        assert manager._cache_ttl == 3600
        assert manager._timeout == 30
        assert manager._cache_hits == 0
        assert manager._cache_misses == 0
        assert manager._context7_resolve_success == 0
        assert manager._context7_resolve_failure == 0
        assert manager._context7_docs_success == 0
        assert manager._context7_docs_failure == 0

    def test_invalid_mcp_client(self):
        """Test that an invalid MCP client raises a ValueError."""
        with pytest.raises(ValueError):
            Context7Manager(
                mcp_client=object()
            )  # Pass an object without a call_tool method

    @pytest.mark.asyncio
    async def test_resolve_library_id_metrics(self, manager):
        """Test that resolve_library_id updates metrics correctly."""
        await manager.resolve_library_id("react")
        assert manager._context7_resolve_success == 1
        assert manager._context7_resolve_failure == 0

        await manager.resolve_library_id("non-existent-library")
        assert manager._context7_resolve_success == 1
        assert manager._context7_resolve_failure == 1


class TestMCPToolRegistration:
    """Test the registration of MCP tools."""

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that the MCP tools are registered correctly."""
        mcp_client = MockMCPClient()
        register_context7_tools(mcp_client)

        assert "resolve_library_id" in mcp_client.tools
        assert "get_library_documentation" in mcp_client.tools
        assert "get_hybrid_library_context" in mcp_client.tools

    @pytest.mark.asyncio
    async def test_resolve_library_id_error_response(self):
        """Test the error response format for resolve_library_id."""
        mcp_client = MockMCPClient()
        register_context7_tools(mcp_client)
        resolve_tool = mcp_client.tools["resolve_library_id"]["function"]

        # Test with an invalid library name
        response = await resolve_tool("")
        assert response["status"] == "error"
        assert "message" in response
        assert "details" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
