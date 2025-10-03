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

    # Detect Claude desktop/code clients which expect stdio transport even in containers
    claude_client_env_vars = [
        "MCP_CLAUDE_DESKTOP",
        "MCP_CLAUDE_CODE",
        "CLAUDE_CODE_MODE",
    ]
    if any(os.environ.get(var) for var in claude_client_env_vars):
        logger.info("Claude client environment detected. Defaulting to 'stdio'.")
        return "stdio"

    # Check if running in Docker, which strongly implies an HTTP server is needed.
    if os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER"):
        logger.info("Docker environment detected. Defaulting to 'streamable-http'.")
        return "streamable-http"

    # Terminal presence indicates an interactive local client environment
    if os.environ.get("TERM"):
        logger.info("Terminal detected. Using 'stdio' transport.")
        return "stdio"

    # Fall back to HTTP transport when no terminal context is available
    logger.info("No terminal detected. Defaulting to 'streamable-http'.")
    return "streamable-http"
