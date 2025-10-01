import os
import logging

logger = logging.getLogger(__name__)


def detect_transport_mode() -> str:
    """Auto-detect the best transport mode based on environment."""
    # Check for explicit transport override first
    transport_override = os.environ.get("MCP_TRANSPORT")
    if transport_override in ["stdio", "streamable-http"]:
        logger.info(
            f"Transport override found: Using '{transport_override}' from MCP_TRANSPORT env var."
        )
        return transport_override

    # Check if running in Docker, which strongly implies an HTTP server is needed.
    if os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER"):
        logger.info("Docker environment detected. Defaulting to 'streamable-http'.")
        return "streamable-http"

    # For all other cases, default to 'stdio'. This is the standard for local clients
    # like Claude Code and Cursor, which launch the MCP server as a subprocess and
    # communicate over stdin/stdout. This avoids issues where the client environment
    # is minimal and doesn't set TERM or other variables.
    logger.info("Defaulting to 'stdio' transport for local client integration.")
    return "stdio"
