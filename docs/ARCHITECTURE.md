# Vibe Check MCP Module Architecture

This document summarizes the public module layout used by integrations and test
suites.  It focuses on the import surfaces that must remain stable after the
recent refactor of the MCP server package.

## Package Layout

```
vibe_check/
├── __init__.py                # Core entry point exporting PatternDetector, etc.
├── server/                    # MCP server orchestration
│   ├── __init__.py            # Re-exports FastMCP app and mentor helpers
│   ├── main.py                # CLI entry point for running the server
│   ├── core.py                # FastMCP wiring and lazy initialisation
│   ├── registry.py            # Tool registration orchestration
│   └── tools/                 # Individual MCP tool modules
└── mentor/                    # Collaborative reasoning system
    ├── __init__.py            # Persona data models for external callers
    ├── models/                # Typed dataclasses and Pydantic schemas
    ├── mcp_sampling.py        # Secure MCP sampling client
    └── telemetry.py           # Runtime metrics and collectors
```

The `vibe_check.server` package now provides a flat namespace for historical
imports such as `from vibe_check.server import app` and `get_mentor_engine`.
Likewise, `vibe_check.server.tools` and the nested `mentor` package re-export
registration helpers and tool entry-points that the regression tests import
directly.

## Import Validation

A dedicated script, `scripts/validate_imports.py`, verifies that the canonical
modules expose the expected attributes and that their `__all__` definitions are
kept in sync.  The script imports:

- `vibe_check.server`
- `vibe_check.server.tools`
- `vibe_check.server.tools.mentor`
- `vibe_check.mentor`
- `vibe_check.tools`

For each module the script checks both attribute availability and `__all__`
contents, exiting with a non-zero status code if any mismatch is found.  This
makes it suitable for use in CI pipelines and as a quick smoke test after local
changes:

```
python scripts/validate_imports.py
```

When adding new public tool entry-points, update the relevant `__all__` list and
extend the validation mapping to keep the import contract explicit.
