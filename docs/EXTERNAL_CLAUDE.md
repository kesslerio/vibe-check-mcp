# External Claude CLI Integration

The `ExternalClaudeCli` wrapper provides an asynchronous interface to the
Claude Code CLI so that MCP tools can offload heavy analysis work to the local
Claude installation without blocking the main event loop.

## Features

- **Async execution** using `asyncio.create_subprocess_exec` for reliable
  process handling and timeout support.
- **Structured parsing** via `_parse_response`, which prefers JSON output but
  gracefully falls back to raw text responses when necessary.
- **Environment isolation** to avoid recursive MCP launches. The helper
  `_create_isolated_environment` removes conflicting variables and tags each
  invocation with a unique `CLAUDE_TASK_ID`.
- **System prompt specialisation** for `pr_review`, `code_analysis`,
  `issue_analysis`, and `general` tasks.
- **Tool call tracking** through the `tool_calls` property so tests and MCP
  telemetry can assert how many CLI invocations occurred.
- **Mock mode** enabled with `MOCK_CLAUDE_CLI=1`, producing deterministic
  responses without spawning the real CLI.
- **Fallback handling** when the CLI is unavailable. The wrapper validates the
  executable path and returns a structured error message rather than raising.
- **New API**: `run_claude_analysis(prompt, context)` which returns a
  dictionary summarising success, output, and metadata for higher-level tools.

## Usage

```python
from vibe_check.tools.analyze_llm_backup import ExternalClaudeCli

cli = ExternalClaudeCli(timeout_seconds=90)
result = await cli.analyze_content("print('hello world')", task_type="code_analysis")
if result.success:
    print(result.output)
else:
    print(result.error)
```

For PR review integrations you can supply extra metadata:

```python
analysis = await cli.run_claude_analysis(
    prompt=combined_prompt,
    context={
        "task_type": "pr_review",
        "metadata": {"pr_number": 42},
        "additional_args": ["--verbose"],
    },
)
```

## Testing tips

- Set `MOCK_CLAUDE_CLI=1` to bypass the real CLI while maintaining the same
  code paths and tool call counters.
- `tool_calls` should match the number of invocations (mock or real). The unit
  tests assert this value in mock mode to guarantee consistent behaviour.
- When running integration tests locally, ensure the CLI exists at
  `~/.claude/local/claude` or expose a custom path via `CLAUDE_CLI_PATH`.
- Run `~/.claude/local/claude --version` to verify the binary is
  available. On CI containers without the CLI installed the command will
  fail, which is expected when operating in mock mode.
