# Migration Guide: MCP Sampling (v0.5.1)

## Overview

This guide helps you migrate to Vibe Check MCP v0.5.1+ which includes MCP sampling for dynamic response generation. The integration is designed to be **backward compatible** with zero required changes for most users.

## For Users

### What's New

MCP sampling enables vibe_check_mentor to generate **context-specific responses** tailored to your exact situation, rather than relying only on pre-written responses.

### No Action Required

If you're using Vibe Check MCP through Claude Code:
- **Everything continues to work** as before
- **No configuration needed** - MCP sampling works automatically
- **Performance improves over time** as the cache builds

### What You'll Notice

1. **More specific advice**: Responses are tailored to your exact code and context
2. **Initial slowness**: First-time queries may take 2-3 seconds (vs <100ms for cached)
3. **Improving performance**: Common queries get faster as cache builds
4. **Better accuracy**: Advice considers your actual files and workspace

### Performance Expectations

| Query Type | Before v0.5.1 | After v0.5.1 (First) | After v0.5.1 (Cached) |
|------------|---------------|---------------------|----------------------|
| Common questions | 50-100ms | 50-100ms | 50-100ms |
| Specific questions | 50-100ms (generic) | 2000-3000ms (tailored) | 150-300ms |
| With file context | Not supported | 2000-3000ms | 200-400ms |

## For Developers

### API Changes

#### vibe_check_mentor

The tool now accepts an optional `ctx` parameter:

**Before (v0.5.0)**:
```python
@server.tool()
async def vibe_check_mentor(
    query: str,
    context: Optional[str] = None,
    # ... other params
) -> Dict[str, Any]:
    # Implementation
```

**After (v0.5.1)**:
```python
@server.tool()
async def vibe_check_mentor(
    query: str,
    context: Optional[str] = None,
    # ... other params
    ctx: Optional[Context] = None  # NEW parameter
) -> Dict[str, Any]:
    # Implementation with MCP sampling support
```

### Response Format Changes

New fields in the response:

```python
{
    # Existing fields remain unchanged
    "summary": str,
    "personas": List[Dict],
    # ... 
    
    # New fields
    "generated": bool,        # True if dynamically generated
    "route_decision": str,    # "static", "dynamic", or "hybrid"
    "latency_ms": int,       # Response generation time
    "cache_hit": bool,       # True if served from cache
    "confidence_score": float # Routing confidence (0.0-1.0)
}
```

### Configuration Options

#### Environment Variables

```bash
# Enable/disable MCP sampling (default: true)
export VIBE_CHECK_MCP_SAMPLING_ENABLED=true

# Confidence threshold for static responses (default: 0.7)
export VIBE_CHECK_CONFIDENCE_THRESHOLD=0.7

# Response cache TTL in seconds (default: 3600)
export VIBE_CHECK_CACHE_TTL=3600

# Maximum tokens for generation (default: 1000)
export VIBE_CHECK_MAX_TOKENS=1000

# LLM temperature (default: 0.7)
export VIBE_CHECK_TEMPERATURE=0.7

# Request timeout in seconds (default: 30)
export VIBE_CHECK_REQUEST_TIMEOUT=30

# Prefer speed over quality (default: false)
export VIBE_CHECK_PREFER_SPEED=false
```

#### Programmatic Configuration

```python
from vibe_check.mentor.mcp_sampling import SamplingConfig, ResponseQuality
from vibe_check.mentor.hybrid_router import HybridRouter

# Configure sampling
sampling_config = SamplingConfig(
    temperature=0.7,
    max_tokens=1000,
    model_preferences=["claude-3-sonnet"],
    quality=ResponseQuality.BALANCED
)

# Configure routing
router = HybridRouter(
    confidence_threshold=0.7,
    enable_caching=True,
    prefer_speed=False
)
```

### Testing Your Integration

#### 1. Verify MCP Sampling is Working

```python
# Test with a simple query
result = await vibe_check_mentor(
    query="Should I use React or Vue?",
    ctx=ctx
)

# Check if routing is working
assert "route_decision" in result
assert result["route_decision"] in ["static", "dynamic", "hybrid"]
```

#### 2. Test Dynamic Generation

```python
# Force dynamic generation with a complex query
result = await vibe_check_mentor(
    query="How to integrate Stripe with Next.js 14 app router using server actions in a TypeScript monorepo?",
    context="Building a SaaS with subscription tiers",
    ctx=ctx
)

# Should trigger dynamic generation
assert result["generated"] == True
assert result["route_decision"] == "dynamic"
```

#### 3. Test Cache Performance

```python
import time

# First request (cache miss)
start = time.time()
result1 = await vibe_check_mentor(query="REST vs GraphQL", ctx=ctx)
time1 = time.time() - start

# Second request (cache hit)
start = time.time()
result2 = await vibe_check_mentor(query="REST vs GraphQL", ctx=ctx)
time2 = time.time() - start

# Cache should be faster
assert time2 < time1 * 0.5  # At least 50% faster
```

### Monitoring and Debugging

#### Enable Debug Logging

```python
import logging

# Enable detailed logging
logging.getLogger("vibe_check.mentor.mcp_sampling").setLevel(logging.DEBUG)
logging.getLogger("vibe_check.mentor.hybrid_router").setLevel(logging.DEBUG)
```

#### Monitor Performance

```python
# Get routing statistics
from vibe_check.mentor.hybrid_router import HybridRouter

router = HybridRouter()
stats = router.get_stats()

print(f"Total requests: {stats['total_requests']}")
print(f"Static routes: {stats['static_percentage']}")
print(f"Dynamic routes: {stats['dynamic_percentage']}")
print(f"Cache hit rate: {stats['cache_hit_rate']}")
```

#### Check Circuit Breaker

```python
from vibe_check.mentor.mcp_sampling import CircuitBreaker

cb = CircuitBreaker()
status = cb.get_status()

print(f"Circuit state: {status['state']}")
print(f"Failures: {status['failure_count']}")
print(f"Uptime: {status['uptime']}s")
```

### Common Migration Issues

#### Issue 1: ctx Parameter Not Available

**Symptom**: `No FastMCP context provided` error

**Solution**: Ensure you're using FastMCP decorators correctly:

```python
# Correct
@server.tool()
async def my_tool(query: str, ctx: Context):
    result = await vibe_check_mentor(query=query, ctx=ctx)
    
# Incorrect (missing ctx)
@server.tool()
async def my_tool(query: str):
    result = await vibe_check_mentor(query=query)  # No ctx!
```

#### Issue 2: Slow Initial Responses

**Symptom**: First queries take 2-3 seconds

**Solution**: This is expected behavior. Options:
1. Pre-warm cache with common queries on startup
2. Use `prefer_speed=true` for faster responses
3. Lower confidence threshold to use more static responses

#### Issue 3: High Memory Usage

**Symptom**: Memory increases over time

**Solution**: Adjust cache settings:

```python
# Reduce cache size
cache = ResponseCache(
    max_size=50,  # Smaller cache
    ttl_seconds=1800  # Shorter TTL (30 minutes)
)
```

### Rollback Plan

If you need to disable MCP sampling:

```bash
# Disable via environment variable
export VIBE_CHECK_MCP_SAMPLING_ENABLED=false
```

Or programmatically:

```python
# Force static responses only
router = HybridRouter(
    confidence_threshold=2.0  # Impossible threshold, always static
)
```

## Performance Optimization

### For Speed-Critical Applications

```python
# Configure for speed
config = SamplingConfig(
    quality=ResponseQuality.FAST,
    max_tokens=500,
    temperature=0.5
)

router = HybridRouter(
    confidence_threshold=0.6,  # Lower threshold
    prefer_speed=True,         # Prefer static/hybrid
    enable_caching=True
)
```

### For Quality-Critical Applications

```python
# Configure for quality
config = SamplingConfig(
    quality=ResponseQuality.HIGH,
    max_tokens=2000,
    temperature=0.8,
    model_preferences=["claude-3-opus"]
)

router = HybridRouter(
    confidence_threshold=0.8,  # Higher threshold
    prefer_speed=False,        # Prefer dynamic
    enable_caching=True
)
```

### For Cost-Sensitive Applications

```python
# Maximize cache, minimize generation
cache = ResponseCache(
    max_size=500,      # Large cache
    ttl_seconds=10800  # 3-hour TTL
)

config = SamplingConfig(
    max_tokens=750,    # Moderate limit
    model_preferences=["claude-3-haiku"]  # Cheaper model
)
```

## Validation Checklist

Before deploying v0.5.1:

- [ ] Test with existing queries to ensure backward compatibility
- [ ] Verify ctx parameter is passed to vibe_check_mentor
- [ ] Monitor initial performance impact
- [ ] Check memory usage with cache enabled
- [ ] Test circuit breaker recovery after failures
- [ ] Verify security features (secret redaction, rate limiting)
- [ ] Review logs for any errors or warnings
- [ ] Test with both simple and complex queries
- [ ] Verify file analysis still works correctly
- [ ] Check session continuity across requests

## Support

For migration assistance:

1. Check [MCP_SAMPLING.md](./MCP_SAMPLING.md) for technical details
2. Review [GitHub Issues](https://github.com/kesslerio/vibe-check-mcp/issues) for known issues
3. Enable debug logging for detailed diagnostics
4. Open an issue with reproduction steps if needed

## Summary

The migration to v0.5.1 with MCP sampling is designed to be seamless:

- **Users**: No action required, enjoy better responses
- **Developers**: Optional configuration, backward compatible
- **Performance**: Initial slowness improves with cache
- **Security**: Enhanced with multiple protective measures
- **Monitoring**: Built-in metrics and debugging tools

The key benefit is **context-specific advice** that adapts to your exact situation, making vibe_check_mentor more helpful and accurate than ever before.