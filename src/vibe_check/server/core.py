import logging
import sys
from .utils import get_version # Import the new function

try:
    # Use official MCP server FastMCP for better Claude Code compatibility
    from mcp.server.fastmcp import FastMCP
    print("Using official MCP server FastMCP implementation for Claude Code compatibility")
except ImportError:
    try:
        # Fallback to standalone FastMCP
        from fastmcp import FastMCP
        print("Using standalone FastMCP - consider installing official MCP package")
    except ImportError:
        print("😅 FastMCP isn't vibing with us yet. Get it with: pip install fastmcp")
        sys.exit(1)

logger = logging.getLogger(__name__)

def get_mcp_instance() -> FastMCP:
    """Initializes and returns the FastMCP server instance."""
    version = get_version() # Get version dynamically
    # Initialize FastMCP server
    mcp = FastMCP(
        name="Vibe Check MCP",
        version=version # Use dynamic version
    )
    return mcp

mcp = get_mcp_instance()
