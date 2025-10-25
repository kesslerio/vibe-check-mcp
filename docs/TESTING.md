# Unit Testing Guidelines

This project relies heavily on asynchronous tooling. Keep these conventions in mind when adding or updating unit tests:

- Prefer the native async APIs exposed by tools (`analyze_issue_async`, `vibe_check_mentor`, etc.) and drive them with `asyncio.run()` or `pytest.mark.asyncio`. Avoid wrapping synchronous shims around asynchronous entry points.
- Use `unittest.mock.AsyncMock` for collaborators that are awaited in production code. Mismatched mocks (`MagicMock` or `Mock`) will surface `TypeError` once the tolerant `asyncio.run` shim is gone.
- When bridging async workflows that previously ran inside synchronous helpers, patch the exact module where the awaited function lives (for example `vibe_check.tools.issue_analysis.api.get_enhanced_github_analyzer`). Patching the re-export alias will not intercept awaits.
- Keep test doubles lightweight: stub global managers or long-running workflows by patching their factories (`get_global_degradation_manager`, `get_enhanced_github_analyzer`, etc.) rather than initializing the full subsystem.
- Fallback responses should be asserted on structured dictionaries (status, validation error, degradation metadata) instead of expecting exceptions from validation.

Following these rules keeps the suite aligned with the async behaviour exercised in production without resurrecting the legacy tolerance fixture.
