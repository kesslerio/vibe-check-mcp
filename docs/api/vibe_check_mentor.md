# vibe_check_mentor API Reference

## Overview

`vibe_check_mentor` is an async FastMCP tool that provides multi-perspective collaborative reasoning for technical decisions. With MCP sampling integration (v0.5.1+), it can generate dynamic, context-specific responses tailored to your exact situation.

## Function Signature

```python
@server.tool(
    name="vibe_check_mentor",
    description="Senior engineer collaborative reasoning - Get multi-perspective feedback on technical decisions"
)
async def vibe_check_mentor(
    query: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    reasoning_depth: str = "standard",
    continue_session: bool = False,
    mode: str = "standard",
    phase: str = "planning",
    confidence_threshold: float = 0.7,
    file_paths: Optional[List[str]] = None,
    working_directory: Optional[str] = None,
    ctx: Optional[Context] = None  # NEW: FastMCP context for MCP sampling
) -> Dict[str, Any]
```

## Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The technical question or decision to discuss |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context` | `str` | `None` | Additional context (code, architecture, requirements) |
| `session_id` | `str` | `None` | Session ID to continue previous conversation |
| `reasoning_depth` | `str` | `"standard"` | Analysis depth: `"quick"`, `"standard"`, `"comprehensive"` |
| `continue_session` | `bool` | `False` | Whether to continue existing session |
| `mode` | `str` | `"standard"` | Interaction mode: `"interrupt"`, `"standard"`, `"comprehensive"` |
| `phase` | `str` | `"planning"` | Development phase: `"planning"`, `"implementation"`, `"review"` |
| `confidence_threshold` | `float` | `0.7` | Minimum confidence to trigger interrupt (0.0-1.0) |
| `file_paths` | `List[str]` | `None` | Optional list of file paths to analyze (max 10 files, 1MB each) |
| `working_directory` | `str` | `None` | Optional working directory for resolving relative paths |
| `ctx` | `Context` | `None` | **NEW**: FastMCP context object for MCP sampling (passed automatically) |

## The ctx Parameter (NEW in v0.5.1)

The `ctx` parameter is automatically provided by FastMCP and enables:
- **Dynamic response generation** via MCP sampling
- **Access to client capabilities** without API keys
- **Context-aware completions** using conversation history

### How ctx Works

```python
# FastMCP automatically provides ctx
@server.tool()
async def vibe_check_mentor(query: str, ctx: Context):
    # ctx.sample() enables MCP sampling
    response = await ctx.sample(
        messages="Analyze this architecture decision",
        system_prompt="You are a senior engineer...",
        temperature=0.7,
        max_tokens=1000
    )
    return {"advice": response.text}
```

## Response Format

```python
{
    "summary": str,              # Executive summary of the analysis
    "interrupt": bool,           # Whether to interrupt current action
    "question": Optional[str],   # Clarifying question if interrupt=true
    "confidence": float,         # Confidence score (0.0-1.0)
    "severity": str,            # Issue severity: "low", "medium", "high"
    "personas": List[Dict],     # Persona perspectives
    "consensus": List[str],     # Points of agreement
    "disagreements": List[Dict], # Points of disagreement
    "recommendations": List[str], # Actionable recommendations
    "next_steps": List[str],    # Concrete next actions
    "session_id": str,          # Session ID for continuity
    "generated": bool,          # NEW: Whether response was dynamically generated
    "route_decision": str,      # NEW: "static", "dynamic", or "hybrid"
    "latency_ms": int          # NEW: Response generation time
}
```

## Modes of Operation

### 1. Interrupt Mode

Quick focused intervention (<3 seconds) for single questions:

```python
result = await vibe_check_mentor(
    query="I'll build a custom HTTP client for the API",
    mode="interrupt",
    phase="planning",
    ctx=ctx
)

if result["interrupt"]:
    print(result["question"])  # "Have you checked if an official SDK exists?"
```

### 2. Standard Mode

Normal collaborative reasoning with selected personas:

```python
result = await vibe_check_mentor(
    query="Should I use microservices or monolith?",
    mode="standard",
    reasoning_depth="standard",
    context="E-commerce platform, 5 developers, expecting 10k users",
    ctx=ctx
)
```

### 3. Comprehensive Mode (Legacy)

Full analysis with all personas:

```python
result = await vibe_check_mentor(
    query="Architecture for real-time collaboration",
    mode="comprehensive",
    file_paths=["src/websocket.py", "src/models.py"],
    ctx=ctx
)
```

## MCP Sampling Integration

### When Dynamic Generation Occurs

The tool uses MCP sampling to generate dynamic responses when:

1. **Low confidence** in static responses (<0.7 score)
2. **Novel scenarios** not covered by response banks
3. **Workspace context** requires specific analysis
4. **Complex queries** with multiple technologies
5. **Force dynamic** flag is set

### Example with Dynamic Generation

```python
# Complex, context-specific query triggers dynamic generation
result = await vibe_check_mentor(
    query="How to integrate Stripe with Next.js 14 app router using server actions?",
    context="Building SaaS with subscription tiers",
    file_paths=["app/actions/billing.ts"],
    reasoning_depth="comprehensive",
    ctx=ctx  # Required for MCP sampling
)

# Response includes dynamic generation metadata
print(f"Generated: {result['generated']}")  # True
print(f"Route: {result['route_decision']}")  # "dynamic"
print(f"Latency: {result['latency_ms']}ms")  # ~2000ms
```

### Example with Static Response

```python
# Common query uses fast static response
result = await vibe_check_mentor(
    query="Should I use REST or GraphQL?",
    reasoning_depth="quick",
    ctx=ctx
)

# Response uses cached static content
print(f"Generated: {result['generated']}")  # False
print(f"Route: {result['route_decision']}")  # "static"
print(f"Latency: {result['latency_ms']}ms")  # ~50ms
```

## Reasoning Depths

### Quick
- Single persona (Senior Engineer)
- Fast response (~500ms with static, ~2s with dynamic)
- Best for straightforward questions

### Standard (Default)
- Two personas (Senior + Product Engineer)
- Balanced analysis (~1s with static, ~3s with dynamic)
- Good for most decisions

### Comprehensive
- All personas with full collaboration
- Detailed analysis (~2s with static, ~5s with dynamic)
- Best for critical architecture decisions

## Development Phases

### Planning Phase
- Focus on architecture and design
- Prevents premature implementation
- Asks "why" before "how"

### Implementation Phase
- Focus on code quality and patterns
- Catches anti-patterns early
- Suggests best practices

### Review Phase
- Focus on completeness and quality
- Identifies missing pieces
- Validates decisions

## Session Continuity

Continue conversations across multiple calls:

```python
# First call
result1 = await vibe_check_mentor(
    query="Should I use PostgreSQL or MongoDB?",
    ctx=ctx
)
session_id = result1["session_id"]

# Continue conversation
result2 = await vibe_check_mentor(
    query="What about scaling considerations?",
    session_id=session_id,
    continue_session=True,
    ctx=ctx
)
```

## File Analysis

Analyze up to 10 files (1MB each):

```python
result = await vibe_check_mentor(
    query="Review this authentication implementation",
    file_paths=[
        "/src/auth/login.py",
        "/src/auth/middleware.py",
        "/src/models/user.py"
    ],
    working_directory="/Users/dev/project",
    ctx=ctx
)
```

## Error Handling

```python
try:
    result = await vibe_check_mentor(
        query="Complex architecture question",
        ctx=ctx
    )
except TimeoutError:
    # MCP sampling timeout (default 30s)
    print("Request timed out, try with quicker depth")
except ValidationError as e:
    # Invalid parameters
    print(f"Validation error: {e}")
except Exception as e:
    # General error with fallback
    print(f"Error: {e}, falling back to static response")
```

## Performance Considerations

### Latency by Route

| Route | Static Response | Dynamic Generation | Cache Hit |
|-------|----------------|-------------------|-----------|
| Quick | 50ms | 2000ms | 150ms |
| Standard | 100ms | 3000ms | 200ms |
| Comprehensive | 200ms | 5000ms | 300ms |

### Optimization Tips

1. **Use appropriate depth**: Don't use comprehensive for simple questions
2. **Leverage sessions**: Continue conversations to maintain context
3. **Cache warming**: Common queries build cache over time
4. **Prefer speed mode**: Enable for faster responses when appropriate

```python
# Fast mode for common questions
result = await vibe_check_mentor(
    query="Best practices for API design",
    reasoning_depth="quick",
    ctx=ctx
)

# Comprehensive for critical decisions
result = await vibe_check_mentor(
    query="Migrating from monolith to microservices strategy",
    reasoning_depth="comprehensive",
    context="50M users, 200 developers, 5TB database",
    ctx=ctx
)
```

## Security Features

The tool includes multiple security measures:

1. **Path validation**: Prevents symlink attacks
2. **Secret redaction**: Removes API keys and passwords
3. **Injection prevention**: Blocks prompt manipulation
4. **Rate limiting**: 10 requests/minute per session
5. **Timeout protection**: 30-second default timeout
6. **Circuit breaker**: Prevents cascading failures

## Common Use Cases

### Architecture Decisions
```python
await vibe_check_mentor(
    query="Choosing between serverless and containers for API",
    context="Startup, variable traffic, 3 developers",
    ctx=ctx
)
```

### Code Review
```python
await vibe_check_mentor(
    query="Review this authentication flow",
    file_paths=["auth.py", "middleware.py"],
    phase="review",
    ctx=ctx
)
```

### Debugging Help
```python
await vibe_check_mentor(
    query="Memory leak in WebSocket connections",
    context="Node.js app, 1000 concurrent users",
    reasoning_depth="comprehensive",
    ctx=ctx
)
```

### Technology Selection
```python
await vibe_check_mentor(
    query="Vue 3 vs React for dashboard project",
    context="Team knows React, timeline 3 months",
    ctx=ctx
)
```

## Best Practices

1. **Provide context**: More context enables better dynamic responses
2. **Use appropriate mode**: Interrupt for quick checks, standard for decisions
3. **Include files**: When discussing specific code, include file paths
4. **Continue sessions**: For multi-part discussions, use session continuity
5. **Monitor performance**: Check latency_ms to optimize usage
6. **Handle failures**: Implement fallback for timeout/errors

## Troubleshooting

### No Dynamic Responses
- Ensure `ctx` parameter is provided
- Check MCP server connectivity
- Verify circuit breaker status

### Slow Responses
- Use `reasoning_depth="quick"` for simple queries
- Enable cache with longer TTL
- Consider `prefer_speed` configuration

### Inconsistent Advice
- Use session continuity for related questions
- Provide more context for accuracy
- Check confidence scores in response

## Version History

- **v0.5.1**: Added MCP sampling integration with ctx parameter
- **v0.4.6**: Fixed phase parameter handling
- **v0.4.5**: Added interrupt mode and multi-persona reasoning
- **v0.4.0**: Initial vibe_check_mentor implementation