#!/usr/bin/env bash
# Development server launcher for vibe-check-mcp
# Use this for local testing with Claude Desktop

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Export Python path
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Change to project directory
cd "$SCRIPT_DIR"

# Check Python availability
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found" >&2
    exit 1
fi

# Run the server with all arguments passed through
exec $PYTHON_CMD -m vibe_check.server "$@"