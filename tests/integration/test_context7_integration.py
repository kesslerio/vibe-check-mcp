"""
Integration tests for Context7 MCP server integration.
Tests the Context7Manager and MCP tools for proper functionality,
caching behavior, knowledge base integration, and error handling.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the Context7 components
from vibe_check.server.tools.context7_integration import (
    Context7Manager, 
    context7_manager,
    _get_local_anti_patterns
)

# Mock MCP Client
class MockMCPClient:
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
                            "trust_score": 9.5
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
    
    def test_manager_initialization(self):
        """Test Context7Manager initialization with proper defaults."""
        manager = Context7Manager(max_cache_size=50)
        
        assert manager._max_cache_size == 50
        assert manager._cache_ttl == 3600
        assert manager._timeout == 30
        assert manager._cache_hits == 0
        assert manager._cache_misses == 0
        assert isinstance(manager._cache, dict)
        assert len(manager._cache) == 0
    
    @pytest.mark.asyncio
    async def test_resolve_library_id_structured_response(self, manager):
        """Test library resolution with new structured JSON response."""
        result = await manager.resolve_library_id("react")
        assert result == "/facebook/react"
        
    @pytest.mark.asyncio
    async def test_caching_behavior_with_mock_client(self, manager):
        """Test caching behavior with the mock client."""
        # First call (miss)
        await manager.resolve_library_id("react")
        assert manager.get_cache_stats()["cache_misses"] == 1
        assert manager.get_cache_stats()["cache_hits"] == 0

        # Second call (hit)
        await manager.resolve_library_id("react")
        assert manager.get_cache_stats()["cache_misses"] == 1
        assert manager.get_cache_stats()["cache_hits"] == 1
        assert manager.get_cache_stats()["hit_rate_percent"] == 50.0

class TestKnowledgeBaseIntegration:
    """Test integration with existing knowledge base."""
    
    def test_knowledge_base_loading(self):
        """Test knowledge base loading from file."""
        assert context7_manager._knowledge_base is not None
        assert len(context7_manager._knowledge_base) > 0
        assert "react" in context7_manager._knowledge_base
        assert "fastapi" in context7_manager._knowledge_base

class TestErrorHandling:
    """Test error handling and fallback behavior."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in Context7 calls."""
        manager = Context7Manager()
        with patch.object(manager, '_call_context7_resolve', side_effect=asyncio.TimeoutError()):
            result = await manager.resolve_library_id("test-lib")
            assert result is None

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test exception handling in Context7 calls."""
        manager = Context7Manager()
        with patch.object(manager, '_call_context7_resolve', side_effect=Exception("Network error")):
            result = await manager.resolve_library_id("test-lib")
            assert result is None

class TestMCPToolsIntegration:
    """Test MCP tools integration and response format."""

    @pytest.mark.asyncio
    async def test_resolve_library_id_tool_response_format(self, manager):
        """Test resolve_library_id MCP tool response format."""
        result = await manager.resolve_library_id("react")
        assert result == "/facebook/react"
        
        stats = manager.get_cache_stats()
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate_percent" in stats

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
