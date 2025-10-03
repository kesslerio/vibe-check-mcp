# Vibe Check MCP Tools

This document describes how FastMCP tools are registered with the Vibe Check
server and how to introspect the currently available capabilities.

## Registration pipeline

1. **Create FastMCP instance** – `vibe_check.server.core.get_mcp_instance()`
   instantiates a `FastMCP` server and exports it as `vibe_check.server.mcp`.
2. **Register tools** – `vibe_check.server.registry.ensure_tools_registered()`
   orchestrates the environment-aware registration process. The helper only
   registers tools when none are currently attached to the server to avoid
   duplicate warnings.
3. **Start transport** – `vibe_check.server.main.run_server()` calls
   `ensure_tools_registered(mcp)` before invoking `mcp.run(...)` so that the
   server always exposes every tool before transport startup.

The central registry lives in `src/vibe_check/server/tools/__init__.py` and
collects every server-defined tool callable. Registration helpers use the
registry to expose deterministic tool names and metadata for tests.

## Introspection helpers

The `server.tools.system` module exposes an MCP tool named `list_tools` which
returns JSON metadata for each registered tool (including optional schema
information when requested).

The `vibe_check.server` package also provides a synchronous-friendly wrapper so
scripts can inspect the active server without spinning up the transport layer:

```bash
python -c "import sys; sys.path.insert(0, 'src'); from vibe_check.server import server; print(server.list_tools())"
```

The wrapper keeps an alias at `vibe_check.server.app` for compatibility with the
existing tests.

## Local tool catalogue

`src/vibe_check/server/tools/__init__.py` exposes helper functions that tests
can import to validate the expected tool names:

- `get_local_tool_names()` – returns a sorted list of tool names defined in the
  server package.
- `get_local_tool_registry()` – returns a copy of the name → callable mapping.
- `iter_local_tools()` – yields each callable to support custom assertions.

These helpers complement the MCP-level `list_tools` call by offering a static
view of the server-owned tools regardless of environment flags.
