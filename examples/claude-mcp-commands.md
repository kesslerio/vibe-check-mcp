# Claude Code MCP Commands for Vibe Check

## User-Level Installation (Recommended)

Add Vibe Check MCP server for use across all projects:

```bash
# Navigate to Vibe Check project directory
cd /Users/kesslerio/GDrive/Projects/vibe-check-mcp

# Add server with user scope (using JSON config for reliability)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "'$(pwd)'/src"
  }
}' -s user

# With GitHub token for private repositories
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python", 
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "'$(pwd)'/src",
    "GITHUB_TOKEN": "your_github_token_here"
  }
}' -s user
```

## Project-Level Installation

Add Vibe Check MCP server for current project only:

```bash
# From your project directory (using JSON config)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "vibe_check.server"],
  "env": {
    "PYTHONPATH": "/Users/kesslerio/GDrive/Projects/vibe-check-mcp/src"
  }
}' -s local
```

## Docker-Based Installation

```bash
# Build Docker image first
cd /Users/kesslerio/GDrive/Projects/vibe-check-mcp
docker build -t vibe-check-mcp .

# Docker-based installation (using JSON config like GitHub MCP)
claude mcp add-json vibe-check '{
  "type": "stdio",
  "command": "bash",
  "args": [
    "-c",
    "docker attach vibe_check_mcp || docker run -i --rm --name vibe_check_mcp -e GITHUB_TOKEN=${GITHUB_TOKEN:-} vibe-check-mcp"
  ],
  "env": {
    "GITHUB_TOKEN": "your_github_token_here"
  }
}' -s user

# Note: Requires Docker image built first
# docker build -t vibe-check-mcp .
```

## Verification Commands

```bash
# List all MCP servers
claude mcp list

# Test server status
claude mcp call vibe-check server_status

# Test GitHub issue analysis
claude mcp call vibe-check analyze_github_issue --issue_number 22 --repository "kesslerio/vibe-check-mcp"
```

## Management Commands

```bash
# Remove server
claude mcp remove vibe-check

# Update server (remove and re-add)
claude mcp remove vibe-check
claude mcp add vibe-check -s user python -m vibe_check.server --cwd $(pwd) --env PYTHONPATH=$(pwd)/src
```