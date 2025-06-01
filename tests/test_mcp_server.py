"""
Tests for FastMCP Server Implementation (Issue #21)

Validates that the FastMCP server integrates correctly with the proven
Phase 1 core detection engine.
"""

import pytest
from unittest.mock import patch
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vibe_compass.tools.demo_tool import demo_analyze_text
from vibe_compass.server import analyze_text_demo, server_status


class TestMCPServerIntegration:
    """Test FastMCP server integration with core engine"""
    
    def test_demo_tool_integration(self):
        """Test that demo tool integrates correctly with core engine"""
        # Test with Infrastructure-Without-Implementation pattern
        test_text = "We should build our own custom HTTP client instead of using the SDK"
        
        result = demo_analyze_text(test_text)
        
        # Verify expected structure
        assert "demo_analysis" in result
        assert "patterns" in result
        assert "server_status" in result
        assert "accuracy_note" in result
        
        # Verify core engine integration
        assert result["demo_analysis"]["analysis_method"] == "Phase 1 validated core engine"
        assert "87.5% accuracy" in result["accuracy_note"]
        
    def test_mcp_tool_wrapper(self):
        """Test MCP tool wrapper functions work correctly"""
        test_text = "planning to implement our own authentication system"
        
        # Test the MCP tool wrapper
        result = analyze_text_demo(test_text, "brief")
        
        assert isinstance(result, dict)
        assert "patterns" in result
        assert result["demo_analysis"]["text_length"] == len(test_text)
        
    def test_server_status_tool(self):
        """Test server status tool returns correct information"""
        status = server_status()
        
        # Verify status structure
        assert status["server_name"] == "Vibe Compass MCP"
        assert status["status"] == "✅ Operational"
        assert status["core_engine_status"]["validation_completed"] is True
        assert status["core_engine_status"]["detection_accuracy"] == "87.5%"
        assert status["core_engine_status"]["false_positive_rate"] == "0%"
        
        # Verify tool information
        assert len(status["available_tools"]) == 2
        assert len(status["upcoming_tools"]) == 4
        
    def test_error_handling(self):
        """Test error handling in demo tool"""
        # Test with problematic input
        result = demo_analyze_text("")
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert result["demo_analysis"]["text_length"] == 0
        
    def test_server_import(self):
        """Test server can be imported and initialized"""
        from vibe_compass.server import mcp, run_server
        
        # Verify FastMCP instance
        assert mcp is not None
        assert hasattr(mcp, 'tool')
        
        # Verify run_server function exists
        assert callable(run_server)
        
    @patch('vibe_compass.server.mcp.run')
    def test_server_startup(self, mock_run):
        """Test server startup process"""
        from vibe_compass.server import run_server
        
        # Test normal startup
        run_server()
        mock_run.assert_called_once()
        
    def test_module_structure(self):
        """Test proper module structure and imports"""
        # Test main module imports
        from vibe_compass import PatternDetector, EducationalContentGenerator, run_server
        
        assert PatternDetector is not None
        assert EducationalContentGenerator is not None
        assert run_server is not None
        
        # Test tools module
        from vibe_compass.tools import demo_analyze_text
        assert demo_analyze_text is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])