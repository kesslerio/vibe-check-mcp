# Deprecated MCP Sampling Implementations

These files were deprecated as part of PR #205 - Post-Deployment Simplification.

## Why Deprecated?

After PR #203 successfully deployed security fixes with 0.02% overhead, we consolidated 7 different mcp_sampling implementations into a single canonical version. This follows the principle learned from the "security theater" incident: **built but not activated = worse than not built**.

## Files

- `mcp_sampling_migration.py` - Intermediate migration version
- `mcp_sampling_optimized.py` - Performance optimization attempt
- `mcp_sampling_patch.py` - Runtime patching mechanism (no longer needed)
- `mcp_sampling_secure.py` - Initial secure version (30.2% overhead)
- `mcp_sampling_ultrafast.py` - Final optimized version (0.02% overhead) - **THIS IS NOW THE MAIN VERSION**

## Historical Context

These implementations represent the evolution from discovering security vulnerabilities (PR #190) to achieving a production-ready solution with negligible overhead. The ultrafast version was promoted to be the canonical `mcp_sampling.py`.

## Do Not Use

These files are kept for historical reference only. All functionality has been consolidated into the main `mcp_sampling.py` file with built-in security patches.

If you're looking for the current implementation, use:
```python
from vibe_check.mentor.mcp_sampling import MCPSamplingClient
```