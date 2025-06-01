#!/bin/bash
# MCP Bridge Script - Connect stdio to HTTP MCP server using socat
# 
# This script enables Claude Desktop/Code to connect to a dockerized MCP server
# by bridging stdio to the HTTP endpoint using socat.
# 
# Usage:
#   ./mcp-bridge.sh [HOST] [PORT]
#   
# Default: localhost:8001

set -e

# Configuration
MCP_HOST=${1:-localhost}
MCP_PORT=${2:-8001}
MCP_ENDPOINT="TCP:${MCP_HOST}:${MCP_PORT}"

# Logging function
log() {
    echo "[MCP-BRIDGE] $1" >&2
}

# Check if socat is available
if ! command -v socat &> /dev/null; then
    log "ERROR: socat is not installed. Install with: apt-get install socat"
    exit 1
fi

# Check if MCP server is responding
if ! timeout 5 bash -c "</dev/tcp/${MCP_HOST}/${MCP_PORT}" 2>/dev/null; then
    log "WARNING: MCP server at ${MCP_HOST}:${MCP_PORT} is not responding"
    log "Make sure the MCP server is running with HTTP transport"
fi

log "Starting MCP bridge: stdio <-> ${MCP_ENDPOINT}"
log "Press Ctrl+C to stop the bridge"

# Start socat bridge
# This connects stdin/stdout to the TCP endpoint
exec socat STDIO "${MCP_ENDPOINT}"