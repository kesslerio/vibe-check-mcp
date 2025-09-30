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
    
    import os
    # Prevent pydantic-settings from automatically loading .env files
    # by temporarily changing the working directory during FastMCP initialization
    original_cwd = os.getcwd()
    original_log_level = os.environ.get('LOG_LEVEL', None)
    
    try:
        # Change to a temp directory to avoid .env file loading
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Also clear problematic env vars
            if 'LOG_LEVEL' in os.environ:
                del os.environ['LOG_LEVEL']
            
            try:
                mcp = FastMCP(
                    name="Vibe Check MCP",
                    version=version # Use dynamic version
                )
            except Exception as e:
                logger.warning(f"Failed to initialize FastMCP with version: {e}")
                # Fallback to basic initialization
                try:
                    mcp = FastMCP("Vibe Check MCP")
                except Exception as e2:
                    logger.warning(f"Basic FastMCP init failed: {e2}")
                    # Most basic fallback
                    mcp = FastMCP()
    finally:
        # Always restore original working directory and environment
        os.chdir(original_cwd)
        if original_log_level:
            # Fix case for FastMCP's case_sensitive=True validation
            if original_log_level.lower() in ['debug', 'info', 'warning', 'error', 'critical']:
                os.environ['LOG_LEVEL'] = original_log_level.upper()
            else:
                os.environ['LOG_LEVEL'] = original_log_level
    
    return mcp

mcp = get_mcp_instance()
