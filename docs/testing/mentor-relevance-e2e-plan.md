# Mentor Relevance E2E Plan (mcp-test-client)

## Objective

Guarantee that `vibe_check_mentor` never returns the legacy canned Stripe / LLM pricing blurbs when
the hybrid router picks a static response. The test must reproduce the tier1 vs tier2 architecture
query that regressed in issue #279 and assert that the returned advice references the requested
topic (tiered regions) instead of generic MVP guidance.

## Tooling

- **Server process**: `PYTHONPATH=src python -m vibe_check.server --stdio`
- **Client harness**: [`mcp-test-client`](https://www.npmjs.com/package/mcp-test-client) `v1.0.1`
  - Use the published ESM build (`import { MCPTestClient } from 'mcp-test-client'`)
  - Spawned inside Node 18+ with the same environment so `PYTHONPATH` is respected
- **Executor**: invoke client via `timeout -k5s 90s node tests/e2e/mcp/mentor_relevance.mjs`
  - The script must `process.exit(1)` on assertion failures to satisfy CI

## Scenario Design

| Step | Action | Assertion |
| ---- | ------ | --------- |
| 1 | Launch MCP server in stdio mode | Process stays alive; write PID to temp file for cleanup |
| 2 | `client.init()` via `MCPTestClient` | `listTools()` contains `vibe_check_mentor` |
| 3 | Call `vibe_check_mentor` with the tier1/tier2 query from issue #279 | Response returned within 20s |
| 4 | Flatten `result["collaborative_insights"]` + `result["immediate_feedback"]` text | Lowercased payload contains `tier1` or `tier 1`; contains `tier2` or `tier 2` |
| 5 | Guard rails | Payload **must not** contain `Stripe`, `LLM`, `pricing`, or `hosted checkout` |
| 6 | Optional diagnostic | If guard fails, dump response JSON to stderr for triage |

## Deterministic Inputs

```jsonc
{
  "tool": "vibe_check_mentor",
  "arguments": {
    "query": "We’ve migrated Stripe validation, demo qualification, and financing workflows into Claude Desktop skills. Should we pull the corresponding JSON files out of tier1 or keep them?",
    "reasoning_depth": "standard",
    "mode": "standard",
    "phase": "planning"
  }
}
```

The script must strip smart quotes to avoid encoding issues. Assertions operate on lowercased,
ASCII-normalised text.

## Cleanup Expectations

- Ensure the Node script terminates the MCP server (send `SIGTERM`, wait 5s, then `SIGKILL` if needed).
- Wrap the entire Node invocation with `timeout -k5s …` so hung servers are reaped.
- Pytest fixture should remove any temporary PID / log files even on failure.

## Deliverables

1. `tests/e2e/mcp/mentor_relevance.mjs` – standalone executable scenario.
2. Pytest wrapper (likely `tests/e2e/test_mentor_relevance_e2e.py`) that runs the script with `timeout`.
3. Package dependency entry (`package.json#devDependencies`) and lock update for `mcp-test-client@1.0.1`.
4. Documentation updates (this file) plus README blurb showing how to run the new check locally.
5. CI task hook once the test stabilises (future follow-up if runtime is acceptable).

## Open Questions

- Should we extend assertions to inspect `route_metrics` telemetry once exposed?
- Do we need additional negative tests (e.g., `Stripe` keyword alone should still be allowed when the query is actually about Stripe MVP advice)?
- How will we seed workspace context (if at all) to keep the scenario deterministic?

