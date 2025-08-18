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
    
    def test_cache_stats(self):
        """Test cache statistics tracking."""
        manager = Context7Manager()
        
        # Initial stats
        stats = manager.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percent"] == 0
        assert stats["cache_size"] == 0
        
        # Simulate cache operations
        manager._cache_hits = 7
        manager._cache_misses = 3
        manager._cache["test"] = {"data": "test", "timestamp": 12345}
        
        stats = manager.get_cache_stats()
        assert stats["cache_hits"] == 7
        assert stats["cache_misses"] == 3
        assert stats["hit_rate_percent"] == 70.0
        assert stats["cache_size"] == 1
    
    def test_input_validation(self):
        """Test library name input validation."""
        manager = Context7Manager()
        
        # Valid inputs
        assert manager._validate_library_name("react") == True
        assert manager._validate_library_name("fast-api") == True
        assert manager._validate_library_name("some_lib") == True
        assert manager._validate_library_name("lib2.0") == True
        
        # Invalid inputs
        assert manager._validate_library_name("") == False
        assert manager._validate_library_name(None) == False
        assert manager._validate_library_name("  ") == False
        assert manager._validate_library_name("lib with spaces") == False
        assert manager._validate_library_name("lib@special") == False
        assert manager._validate_library_name("a" * 101) == False  # Too long
    
    def test_cache_size_limit_enforcement(self):
        """Test cache size limit enforcement."""
        manager = Context7Manager(max_cache_size=3)
        
        # Fill cache beyond limit
        for i in range(5):
            manager._set_cache(f"key_{i}", f"data_{i}")
        
        # Should not exceed max size
        assert len(manager._cache) == 5  # Before enforcement
        
        manager._enforce_cache_size_limit()
        assert len(manager._cache) <= 3  # After enforcement
    
    @pytest.mark.asyncio
    async def test_resolve_library_id_validation(self):
        """Test library resolution with input validation."""
        manager = Context7Manager()
        
        # Valid library
        result = await manager.resolve_library_id("react")
        assert result == "/facebook/react"
        
        # Invalid inputs should return None
        result = await manager.resolve_library_id("")
        assert result is None
        
        result = await manager.resolve_library_id("invalid@lib")
        assert result is None
        
        result = await manager.resolve_library_id(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_library_docs_validation(self):
        """Test documentation fetching with input validation."""
        manager = Context7Manager()
        
        # Valid library ID
        result = await manager.get_library_docs("/facebook/react", "hooks")
        assert result is not None
        assert "react" in result.lower()
        
        # Invalid inputs should return None
        result = await manager.get_library_docs("", "topic")
        assert result is None
        
        result = await manager.get_library_docs(None, "topic")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test caching behavior and hit/miss tracking."""
        manager = Context7Manager()
        
        # First call should be a cache miss
        result1 = await manager.resolve_library_id("react")
        assert manager._cache_misses == 1
        assert manager._cache_hits == 0
        
        # Second call should be a cache hit
        result2 = await manager.resolve_library_id("react")
        assert result1 == result2
        assert manager._cache_misses == 1
        assert manager._cache_hits == 1
        
        # Cache stats should reflect this
        stats = manager.get_cache_stats()
        assert stats["hit_rate_percent"] == 50.0


class TestKnowledgeBaseIntegration:
    """Test integration with existing knowledge base."""
    
    def test_knowledge_base_loading(self):
        """Test knowledge base loading from file."""
        # The global manager should have loaded the knowledge base
        assert context7_manager._knowledge_base is not None
        assert len(context7_manager._knowledge_base) > 0
        
        # Should contain expected libraries
        assert "react" in context7_manager._knowledge_base
        assert "fastapi" in context7_manager._knowledge_base
        assert "cognee" in context7_manager._knowledge_base
    
    @pytest.mark.asyncio
    async def test_local_anti_patterns_extraction(self):
        """Test anti-pattern extraction from knowledge base."""
        # Test React patterns
        react_patterns = await _get_local_anti_patterns("react")
        assert len(react_patterns) > 0
        
        # Should include red flags
        red_flag_patterns = [p for p in react_patterns if p.get("source") == "knowledge_base"]
        assert len(red_flag_patterns) > 0
        
        # Test FastAPI patterns  
        fastapi_patterns = await _get_local_anti_patterns("fastapi")
        assert len(fastapi_patterns) > 0
        
        # Test unknown library
        unknown_patterns = await _get_local_anti_patterns("unknown-lib")
        assert len(unknown_patterns) == 0
    
    def test_knowledge_base_structure_validation(self):
        """Test that knowledge base has expected structure."""
        kb = context7_manager._knowledge_base
        
        # Test React entry structure
        react_data = kb.get("react", {})
        assert "library_type" in react_data
        assert "detection_patterns" in react_data
        assert "versions" in react_data
        assert "red_flags" in react_data
        assert "official_sdks" in react_data
        
        # Test version-specific data
        versions = react_data.get("versions", {})
        assert len(versions) > 0
        
        for version, version_data in versions.items():
            assert "best_practices" in version_data
            assert "anti_patterns" in version_data


class TestErrorHandling:
    """Test error handling and fallback behavior."""
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in Context7 calls."""
        manager = Context7Manager()
        
        # Mock a timeout scenario
        with patch.object(manager, '_call_context7_resolve') as mock_resolve:
            mock_resolve.side_effect = asyncio.TimeoutError()
            
            result = await manager.resolve_library_id("test-lib")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test exception handling in Context7 calls."""
        manager = Context7Manager()
        
        # Mock an exception scenario
        with patch.object(manager, '_call_context7_resolve') as mock_resolve:
            mock_resolve.side_effect = Exception("Network error")
            
            result = await manager.resolve_library_id("test-lib")
            assert result is None
    
    def test_missing_knowledge_base(self):
        """Test behavior when knowledge base is missing."""
        # Create manager with missing knowledge base
        with patch('pathlib.Path.exists', return_value=False):
            manager = Context7Manager()
            assert manager._knowledge_base == {}


class TestMCPToolsIntegration:
    """Test MCP tools integration and response format."""
    
    @pytest.mark.asyncio
    async def test_resolve_library_id_tool_response(self):
        """Test resolve_library_id MCP tool response format."""
        # This would require importing and testing the actual MCP tool
        # For now, test the core manager functionality
        manager = Context7Manager()
        
        # Test successful resolution
        result = await manager.resolve_library_id("react")
        assert result == "/facebook/react"
        
        # Test cache stats availability
        stats = manager.get_cache_stats()
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate_percent" in stats
    
    @pytest.mark.asyncio
    async def test_hybrid_context_data_structure(self):
        """Test hybrid context data structure."""
        patterns = await _get_local_anti_patterns("react")
        
        # Validate pattern structure
        for pattern in patterns:
            assert "pattern" in pattern
            assert "description" in pattern
            assert "severity" in pattern
            assert "source" in pattern
            assert pattern["source"] == "knowledge_base"


# Fixtures for testing
@pytest.fixture
def temp_knowledge_base():
    """Create temporary knowledge base for testing."""
    test_kb = {
        "test-lib": {
            "library_type": "test",
            "red_flags": ["custom-implementation", "manual-setup"],
            "official_sdks": ["test-sdk"],
            "versions": {
                "1.0": {
                    "anti_patterns": ["deprecated-api"],
                    "best_practices": ["use-official-sdk"]
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_kb, f)
        yield f.name
    
    # Cleanup
    Path(f.name).unlink()


def test_with_custom_knowledge_base(temp_knowledge_base):
    """Test manager with custom knowledge base."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', create=True) as mock_open:
            with open(temp_knowledge_base, 'r') as real_file:
                mock_open.return_value.__enter__.return_value = real_file
                
                manager = Context7Manager()
                assert "test-lib" in manager._knowledge_base


if __name__ == "__main__":
    # Run tests manually for development
    pytest.main([__file__, "-v"])