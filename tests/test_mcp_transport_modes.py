#!/usr/bin/env python3
"""
Integration tests for MCP server transport modes (stdio vs streamable-http)

Tests Issue #46 implementation: MCP Server Docker vs Host Deployment Strategy
"""

import pytest
import os
import subprocess
import sys
import time
import signal
import socket
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibe_check.server import detect_transport_mode, run_server


class TestTransportModeDetection:
    """Test automatic transport mode detection logic."""
    
    def test_docker_detection(self, monkeypatch):
        """Test Docker environment detection."""
        # Mock Docker environment
        monkeypatch.setenv("RUNNING_IN_DOCKER", "true")
        assert detect_transport_mode() == "streamable-http"
        
        # Test with .dockerenv file
        monkeypatch.delenv("RUNNING_IN_DOCKER", raising=False)
        with tempfile.NamedTemporaryFile() as tmp:
            monkeypatch.setattr("os.path.exists", lambda path: path == "/.dockerenv")
            assert detect_transport_mode() == "streamable-http"
    
    def test_claude_client_detection(self, monkeypatch):
        """Test Claude Desktop/Code client detection."""
        monkeypatch.setenv("MCP_CLAUDE_DESKTOP", "true")
        assert detect_transport_mode() == "stdio"
        
        monkeypatch.delenv("MCP_CLAUDE_DESKTOP", raising=False)
        monkeypatch.setenv("CLAUDE_CODE_MODE", "true") 
        assert detect_transport_mode() == "stdio"
    
    def test_explicit_override(self, monkeypatch):
        """Test explicit transport override."""
        monkeypatch.setenv("MCP_TRANSPORT", "stdio")
        assert detect_transport_mode() == "stdio"
        
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        assert detect_transport_mode() == "streamable-http"
    
    def test_terminal_detection(self, monkeypatch):
        """Test terminal-based detection."""
        # Clear all environment variables that could affect detection
        env_vars = ["RUNNING_IN_DOCKER", "MCP_CLAUDE_DESKTOP", "CLAUDE_CODE_MODE", "MCP_TRANSPORT"]
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)
        
        # Mock terminal environment
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.setattr("os.path.exists", lambda path: False)
        assert detect_transport_mode() == "stdio"
        
        # Mock server environment (no TERM)
        monkeypatch.delenv("TERM", raising=False)
        assert detect_transport_mode() == "streamable-http"


class TestServerIntegration:
    """Integration tests for server startup with different transports."""
    
    def test_stdio_transport_help(self):
        """Test stdio transport CLI help functionality."""
        result = subprocess.run(
            [sys.executable, "-m", "vibe_check", "server", "--help"],
            cwd=Path(__file__).parent.parent,
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "--stdio" in result.stdout
        assert "--transport" in result.stdout
        assert "streamable-http" in result.stdout
    
    def test_http_transport_startup(self):
        """Test HTTP transport server startup and shutdown."""
        # Find an available port
        port = self._find_free_port()
        
        # Start server with HTTP transport
        proc = subprocess.Popen(
            [sys.executable, "-m", "vibe_check", "server", "--transport", "streamable-http", "--port", str(port)],
            cwd=Path(__file__).parent.parent,
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is responding
            response = self._check_http_endpoint(port)
            assert response is not None, "Server should respond to HTTP requests"
            
        finally:
            # Clean shutdown
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    
    def test_environment_based_detection(self):
        """Test environment-based transport selection."""
        # Test with Claude Desktop environment
        env = {**os.environ, "PYTHONPATH": "src", "MCP_CLAUDE_DESKTOP": "true"}
        
        result = subprocess.run(
            [sys.executable, "-c", 
             "import sys; sys.path.insert(0, 'src'); "
             "from vibe_check.server import detect_transport_mode; "
             "print(detect_transport_mode())"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        assert result.returncode == 0
        assert result.stdout.strip() == "stdio"
        
        # Test with Docker environment
        env = {**os.environ, "PYTHONPATH": "src", "RUNNING_IN_DOCKER": "true"}
        
        result = subprocess.run(
            [sys.executable, "-c", 
             "import sys; sys.path.insert(0, 'src'); "
             "from vibe_check.server import detect_transport_mode; "
             "print(detect_transport_mode())"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        assert result.returncode == 0
        assert result.stdout.strip() == "streamable-http"
    
    def _find_free_port(self) -> int:
        """Find an available port for testing."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def _check_http_endpoint(self, port: int) -> bool:
        """Check if HTTP endpoint is responding."""
        try:
            import urllib.request
            import urllib.error
            
            url = f"http://localhost:{port}/mcp/"
            req = urllib.request.Request(url, headers={'Accept': 'text/event-stream'})
            
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200 or response.status == 406  # 406 is expected for SSE endpoint
        except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
            return False


class TestMCPCompatibility:
    """Test compatibility with Claude Desktop/Code MCP configuration."""
    
    def test_claude_desktop_config_compatibility(self):
        """Test that server works with Claude Desktop mcp.json configuration format."""
        # Simulate the exact configuration from user's mcp.json
        result = subprocess.run(
            [sys.executable, "-m", "vibe_check.server", "--stdio"],
            cwd=Path(__file__).parent.parent,
            env={
                **os.environ, 
                "PYTHONPATH": "src",
                "GITHUB_TOKEN": "dummy_token_for_testing"
            },
            input="",  # Provide empty input to stdin
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Server should start successfully and then exit when stdin closes
        # We expect a specific startup message
        assert "Starting Vibe Check MCP Server" in result.stderr or "Starting Vibe Check MCP Server" in result.stdout
    
    def test_module_entry_points(self):
        """Test all valid module entry points."""
        entry_points = [
            [sys.executable, "-m", "vibe_check", "server", "--help"],
            [sys.executable, "-m", "vibe_check.server", "--help"]
        ]
        
        for entry_point in entry_points:
            result = subprocess.run(
                entry_point,
                cwd=Path(__file__).parent.parent,
                env={**os.environ, "PYTHONPATH": "src"},
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0, f"Entry point {' '.join(entry_point)} failed"
            assert "Vibe Check MCP Server" in result.stdout


if __name__ == "__main__":
    # Run tests when called directly
    pytest.main([__file__, "-v"])