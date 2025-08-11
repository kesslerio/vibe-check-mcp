# Workspace-Aware Vibe Check Mentor Setup Guide

## Overview

The Vibe Check Mentor can now read actual code files from your project to provide specific, context-aware guidance instead of generic advice. This feature follows MCP's security model by requiring explicit workspace configuration.

## Quick Start

### 1. Set the WORKSPACE Environment Variable

Configure your MCP server to pass the workspace directory:

```json
// In your MCP configuration (e.g., Claude Desktop config)
{
  "mcpServers": {
    "vibe-check-mcp": {
      "command": "python",
      "args": ["-m", "vibe_check"],
      "env": {
        "WORKSPACE": "/path/to/your/project"  // Add this line
      }
    }
  }
}
```

### 2. Use the Enhanced Mentor

Once configured, the mentor will automatically read relevant files:

```python
# The mentor will now read actual TypeScript files
vibe_check_mentor(
    query="Should I refactor the UserAuthService.ts to use dependency injection?",
    reasoning_depth="comprehensive"
)

# Explicitly specify files to analyze
vibe_check_mentor(
    query="Review the error handling approach",
    file_paths=["src/services/api.py", "src/utils/errors.py"]
)
```

## Detailed Configuration

### Environment Variable

The `WORKSPACE` environment variable sets the root directory for file access:

- **Required**: No (mentor works without it, but provides generic advice)
- **Type**: Absolute path to a directory
- **Security**: All file access is restricted to this directory and its subdirectories

Example configurations:

```bash
# Unix/Linux/macOS
export WORKSPACE="/Users/yourname/projects/my-app"

# Windows
set WORKSPACE="C:\Users\yourname\projects\my-app"
```

### MCP Configuration Examples

#### Claude Desktop (macOS)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibe-check-mcp": {
      "command": "python",
      "args": ["-m", "vibe_check"],
      "env": {
        "WORKSPACE": "/Users/yourname/projects/my-app",
        "PYTHONPATH": "/path/to/vibe-check-mcp/src"
      }
    }
  }
}
```

#### Claude Desktop (Windows)

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibe-check-mcp": {
      "command": "python",
      "args": ["-m", "vibe_check"],
      "env": {
        "WORKSPACE": "C:\\Users\\yourname\\projects\\my-app",
        "PYTHONPATH": "C:\\path\\to\\vibe-check-mcp\\src"
      }
    }
  }
}
```

#### VS Code with Continue.dev

In your `.continuerc.json`:

```json
{
  "models": [...],
  "mcpServers": {
    "vibe-check-mcp": {
      "command": "python",
      "args": ["-m", "vibe_check"],
      "env": {
        "WORKSPACE": "${workspaceFolder}"  // Uses current VS Code workspace
      }
    }
  }
}
```

## Features

### Automatic File Discovery

The mentor automatically finds relevant files based on your query:

```python
# Mentioning a file name triggers automatic loading
vibe_check_mentor(
    query="The authentication in user_service.py seems complex"
)
# Automatically loads and analyzes user_service.py
```

### Multi-Language Support

Supports analysis of multiple programming languages:

- **Python** (.py, .pyw, .pyi) - Full AST parsing
- **TypeScript/JavaScript** (.ts, .tsx, .js, .jsx, .mjs) - Pattern-based analysis
- **Go** (.go) - Struct and function detection
- **Rust** (.rs) - Trait and impl analysis
- **Java** (.java) - Class and method extraction
- **C/C++** (.c, .cpp, .cc, .h, .hpp) - Generic parsing
- **Ruby** (.rb), **PHP** (.php), **Swift** (.swift), **Kotlin** (.kt) - Basic support

### Security Features

All file access is secured:

1. **Path Validation**: Only files within WORKSPACE are accessible
2. **Path Traversal Prevention**: Attempts to access parent directories are blocked
3. **File Size Limits**: Maximum 1MB per file, 5MB total
4. **File Type Restrictions**: Only source code and text files
5. **Symlink Resolution**: Symlinks are resolved and validated

### Session Caching

File contents are cached per session for performance:

```python
# First call loads files
result1 = vibe_check_mentor(
    query="Review the API design",
    session_id="my-session-123"
)

# Subsequent calls reuse cached files
result2 = vibe_check_mentor(
    query="What about error handling?",
    session_id="my-session-123",
    continue_session=True
)
```

## Usage Examples

### Basic Usage

```python
# Let the mentor auto-discover files
vibe_check_mentor(
    query="Should I use Redis or in-memory caching for the session store?"
)
```

### With Specific Files

```python
# Analyze specific files
vibe_check_mentor(
    query="Is this the right abstraction level?",
    file_paths=[
        "src/core/repository.ts",
        "src/services/user_service.ts"
    ]
)
```

### Architecture Review

```python
# Review overall architecture with multiple files
vibe_check_mentor(
    query="Review our microservices communication pattern",
    file_paths=[
        "services/auth/main.go",
        "services/user/main.go",
        "shared/messaging/broker.go"
    ],
    reasoning_depth="comprehensive"
)
```

### Debugging Session

```python
# Get help with a specific bug
vibe_check_mentor(
    query="Why might this cause a memory leak?",
    file_paths=["src/cache/manager.rs"],
    context="Users report increasing memory usage over time"
)
```

## Workspace Info in Responses

When workspace is configured, responses include additional information:

```json
{
  "workspace_info": {
    "workspace_configured": true,
    "workspace_path": "/Users/you/project",
    "files_loaded": 3,
    "files_analyzed": [
      "src/auth.ts",
      "src/user.ts",
      "src/api.ts"
    ],
    "total_context_size": 15234
  },
  "code_insights": [
    "Potential issue in src/auth.ts at line 45: TODO: Add rate limiting",
    "Potential issue in src/api.ts at line 123: FIXME: Handle timeout"
  ]
}
```

## Troubleshooting

### Workspace Not Found

If you see "No workspace configured":
1. Verify WORKSPACE environment variable is set
2. Check the path exists and is a directory
3. Ensure the MCP server has read permissions

### Files Not Loading

If files aren't being loaded:
1. Check file extensions are supported
2. Verify files are within WORKSPACE directory
3. Ensure files are under 1MB in size
4. Check logs for specific error messages

### Permission Errors

If you get permission denied errors:
1. Verify the MCP server process has read access
2. Check file permissions: `ls -la /path/to/file`
3. On Windows, check if files are locked by another process

## Best Practices

1. **Set workspace to project root**: This gives the mentor full context
2. **Use relative paths in queries**: Makes queries portable across team members
3. **Leverage auto-discovery**: Mention file names naturally in questions
4. **Cache sessions**: Use session IDs for related questions
5. **Limit file count**: Focus on 3-5 most relevant files for best results

## Privacy and Security

- **Local only**: All file reading happens locally, no files are sent to external services
- **Read-only**: The mentor only reads files, never modifies them
- **Sandboxed**: File access is restricted to the configured workspace
- **No traversal**: Parent directory access is blocked (no `../` attacks)
- **Type safe**: Only text-based source files are processed

## Advanced Configuration

### Multiple Workspaces

To switch between projects, update the WORKSPACE variable and restart the MCP server:

```bash
# Project A
export WORKSPACE="/path/to/project-a"

# Project B  
export WORKSPACE="/path/to/project-b"
```

### Project Registry (Coming Soon)

Future versions will support a project registry for quick switching:

```python
# Register projects
register_project("frontend", "/Users/you/projects/web-app")
register_project("backend", "/Users/you/projects/api-server")

# Mentor auto-discovers based on context
vibe_check_mentor(query="Review the React components")  # Uses frontend
vibe_check_mentor(query="Check the database models")    # Uses backend
```

## Migration from Generic Mentor

If you've been using the mentor without workspace configuration:

1. **No breaking changes**: Existing usage continues to work
2. **Gradual adoption**: Add WORKSPACE when ready for enhanced features
3. **Backwards compatible**: All existing parameters still supported
4. **Same API**: No code changes required

## Performance Considerations

- **File limit**: Maximum 10 files per request
- **Size limit**: 1MB per file, 5MB total
- **Cache TTL**: Files cached for 1 hour per session
- **Auto-discovery**: Searches up to 3 directory levels deep

## Support

For issues or questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review [server logs](#) for detailed error messages
3. Open an issue with workspace configuration details (excluding sensitive paths)