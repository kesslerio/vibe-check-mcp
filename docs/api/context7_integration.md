# Context7 MCP Integration API Reference

## Overview

The Context7 integration provides hybrid library documentation capabilities, combining Context7's real-time documentation with vibe-check-mcp's curated anti-pattern detection. This integration replaces the manual library knowledge base with dynamic documentation retrieval while preserving critical anti-pattern rules.

## Core Components

### Context7Manager

Central manager for Context7 MCP server interactions with intelligent caching and fallback mechanisms.

**Features:**
- **Intelligent Caching**: 1-hour TTL with cache hit tracking
- **Cache Size Limits**: Configurable LRU eviction (default: 1000 entries)
- **Knowledge Base Integration**: Seamless fallback to existing patterns
- **Input Validation**: Sanitization and security measures
- **Performance Monitoring**: Detailed cache statistics

## MCP Tools

### resolve_library_id

Convert library names to Context7-compatible IDs for documentation retrieval.

#### Function Signature

```python
@server.tool(
    name="resolve_library_id",
    description="Resolve library name to Context7-compatible ID for documentation retrieval"
)
async def resolve_library_id(library_name: str) -> Dict[str, Any]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `library_name` | `str` | Library name (e.g., "react", "fastapi", "supabase") |

#### Response Format

```python
{
    "status": "success" | "not_found" | "error",
    "library_name": str,
    "library_id": Optional[str],
    "cached": bool,                    # Whether result was from cache
    "cache_stats": Dict[str, Any],     # Cache performance statistics
    "message": str
}
```

#### Examples

**Successful Resolution:**
```python
result = await resolve_library_id("react")
# {
#     "status": "success",
#     "library_name": "react", 
#     "library_id": "/facebook/react",
#     "cached": false,
#     "cache_stats": {
#         "cache_hits": 0,
#         "cache_misses": 1,
#         "hit_rate_percent": 0.0,
#         "cache_size": 1,
#         "max_cache_size": 1000
#     },
#     "message": "Resolved react to Context7 ID: /facebook/react"
# }
```

**Library Not Found:**
```python
result = await resolve_library_id("unknown-library")
# {
#     "status": "not_found",
#     "library_name": "unknown-library",
#     "library_id": null,
#     "message": "Could not resolve library: unknown-library"
# }
```

**Input Validation Error:**
```python
result = await resolve_library_id("invalid@lib!")
# {
#     "status": "error",
#     "library_name": "invalid@lib!",
#     "library_id": null,
#     "message": "Error resolving library: Invalid library name"
# }
```

### get_library_documentation

Fetch real-time library documentation from Context7 with caching and topic filtering.

#### Function Signature

```python
@server.tool(
    name="get_library_documentation",
    description="Fetch real-time library documentation from Context7"
)
async def get_library_documentation(
    library_id: str, 
    topic: Optional[str] = None,
    max_tokens: int = 10000
) -> Dict[str, Any]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `library_id` | `str` | - | Context7-compatible library ID (e.g., "/facebook/react") |
| `topic` | `str` | `None` | Optional topic filter (e.g., "hooks", "authentication") |
| `max_tokens` | `int` | `10000` | Maximum tokens to return |

#### Response Format

```python
{
    "status": "success" | "not_found" | "error",
    "library_id": str,
    "topic": Optional[str],
    "documentation": Optional[str],
    "cached": bool,                    # Whether result was from cache
    "cache_stats": Dict[str, Any],     # Cache performance statistics
    "message": str
}
```

#### Examples

**Successful Documentation Fetch:**
```python
result = await get_library_documentation("/facebook/react", "hooks")
# {
#     "status": "success",
#     "library_id": "/facebook/react",
#     "topic": "hooks",
#     "documentation": "# React Hooks Documentation\n\nReal-time documentation...",
#     "cached": false,
#     "cache_stats": {...},
#     "message": "Retrieved documentation for /facebook/react"
# }
```

**Cached Result:**
```python
result = await get_library_documentation("/facebook/react", "hooks")  # Second call
# {
#     "status": "success",
#     "library_id": "/facebook/react", 
#     "topic": "hooks",
#     "documentation": "# React Hooks Documentation...",
#     "cached": true,                   # Served from cache
#     "cache_stats": {
#         "cache_hits": 1,
#         "cache_misses": 1,
#         "hit_rate_percent": 50.0,
#         "cache_size": 2,
#         "max_cache_size": 1000
#     },
#     "message": "Retrieved documentation for /facebook/react"
# }
```

### get_hybrid_library_context

Get comprehensive library context combining Context7 documentation with local anti-pattern detection.

#### Function Signature

```python
@server.tool(
    name="get_hybrid_library_context",
    description="Get comprehensive library context combining Context7 docs with local patterns"
)
async def get_hybrid_library_context(
    library_names: List[str],
    include_anti_patterns: bool = True,
    focus_topic: Optional[str] = None
) -> Dict[str, Any]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `library_names` | `List[str]` | - | List of library names to analyze |
| `include_anti_patterns` | `bool` | `True` | Whether to include local anti-pattern detection |
| `focus_topic` | `str` | `None` | Optional topic to focus documentation on |

#### Response Format

```python
{
    "status": "success" | "error",
    "libraries": Dict[str, LibraryContext],
    "focus_topic": Optional[str],
    "context_source": "hybrid",
    "message": str
}
```

#### LibraryContext Structure

```python
{
    "library_name": str,
    "library_id": Optional[str],
    "documentation": Optional[str],
    "anti_patterns": List[AntiPattern],
    "status": "documented" | "no_docs" | "not_found"
}
```

#### AntiPattern Structure

```python
{
    "pattern": str,                    # Anti-pattern identifier
    "description": str,                # Human-readable description
    "severity": "high" | "medium" | "low",
    "source": "knowledge_base",        # Source of the pattern
    "version": Optional[str],          # Version-specific patterns
    "recommended_sdks": Optional[List[str]]  # Official SDK recommendations
}
```

#### Examples

**Hybrid Context Analysis:**
```python
result = await get_hybrid_library_context(
    library_names=["react", "fastapi", "unknown-lib"],
    include_anti_patterns=True,
    focus_topic="authentication"
)
# {
#     "status": "success",
#     "libraries": {
#         "react": {
#             "library_name": "react",
#             "library_id": "/facebook/react",
#             "documentation": "# React Authentication Documentation...",
#             "anti_patterns": [
#                 {
#                     "pattern": "class-components-new-code",
#                     "description": "Anti-pattern detected in react: class-components-new-code",
#                     "severity": "high",
#                     "source": "knowledge_base"
#                 },
#                 {
#                     "pattern": "custom-implementation-over-official-sdk",
#                     "description": "Consider using official SDKs: react, @types/react",
#                     "severity": "medium",
#                     "source": "knowledge_base",
#                     "recommended_sdks": ["react", "@types/react"]
#                 }
#             ],
#             "status": "documented"
#         },
#         "fastapi": {
#             "library_name": "fastapi",
#             "library_id": "/tiangolo/fastapi",
#             "documentation": "# FastAPI Authentication Documentation...",
#             "anti_patterns": [
#                 {
#                     "pattern": "custom-authentication",
#                     "description": "Anti-pattern detected in fastapi: custom-authentication",
#                     "severity": "high",
#                     "source": "knowledge_base"
#                 }
#             ],
#             "status": "documented"
#         },
#         "unknown-lib": {
#             "library_name": "unknown-lib",
#             "library_id": null,
#             "documentation": null,
#             "anti_patterns": [],
#             "status": "not_found"
#         }
#     },
#     "focus_topic": "authentication",
#     "context_source": "hybrid",
#     "message": "Retrieved hybrid context for 3 libraries"
# }
```

## Cache Management

### Cache Statistics

Monitor cache performance using the integrated statistics:

```python
# Cache stats are included in all tool responses
cache_stats = {
    "cache_hits": 15,               # Number of cache hits
    "cache_misses": 5,              # Number of cache misses  
    "hit_rate_percent": 75.0,       # Cache hit rate percentage
    "cache_size": 20,               # Current cache entries
    "max_cache_size": 1000          # Maximum cache size
}
```

### Cache Behavior

- **TTL**: 1-hour time-to-live for all cached entries
- **LRU Eviction**: Oldest entries removed when cache size exceeds limit
- **Automatic Cleanup**: Cache size enforced on every operation
- **Performance Tracking**: Hit/miss statistics for monitoring

## Error Handling

### Common Error Scenarios

**Timeout Errors:**
```python
# Context7 API timeout (30 seconds)
{
    "status": "error",
    "message": "Context7 timeout for library resolution"
}
```

**Input Validation Errors:**
```python
# Invalid library name
{
    "status": "error", 
    "message": "Invalid library name: must be alphanumeric with hyphens, underscores, dots"
}
```

**Network Errors:**
```python
# Context7 service unavailable
{
    "status": "error",
    "message": "Context7 service error: Connection failed"
}
```

### Graceful Fallback

When Context7 is unavailable, the system gracefully falls back to:
1. **Local Knowledge Base**: Anti-patterns from `integration_knowledge_base.json`
2. **Error Indication**: Clear status messages about service availability
3. **Cached Data**: Previously cached results remain available

## Knowledge Base Integration

### Supported Libraries

The integration includes anti-pattern detection for 9 libraries from the existing knowledge base:

- **react**: Frontend framework patterns
- **fastapi**: Backend framework patterns  
- **cognee**: Knowledge graph service patterns
- **supabase**: Backend service patterns
- **claude**: AI service patterns
- **openai**: AI service patterns
- **github**: Version control patterns
- **docker**: Containerization patterns
- **kubernetes**: Container orchestration patterns

### Anti-Pattern Categories

**Red Flags (High Severity):**
- Custom implementations when official SDKs exist
- Security anti-patterns (client-side secrets, manual auth)
- Deprecated API usage

**Version-Specific (Medium Severity):**
- Patterns specific to library versions
- Migration recommendations
- Best practice violations

**SDK Recommendations (Medium Severity):**
- Official SDK alternatives to custom implementations
- Performance and maintenance benefits

## Performance Considerations

### Latency Optimization

| Operation | Cache Hit | Cache Miss | Context7 Call |
|-----------|-----------|------------|---------------|
| Library Resolution | ~1ms | ~5ms | ~100-500ms |
| Documentation Fetch | ~1ms | ~5ms | ~200-1000ms |
| Hybrid Context | ~2ms | ~10ms | ~300-1500ms |

### Best Practices

1. **Use Caching**: Let the system cache frequently accessed libraries
2. **Batch Requests**: Use `get_hybrid_library_context` for multiple libraries
3. **Monitor Performance**: Check `cache_stats` for optimization opportunities
4. **Topic Filtering**: Use specific topics to reduce documentation size

## Integration Examples

### Basic Library Analysis

```python
# Step 1: Resolve library ID
resolution = await resolve_library_id("react")
library_id = resolution["library_id"]

# Step 2: Get documentation
docs = await get_library_documentation(library_id, "hooks")

# Step 3: Get complete context with anti-patterns
context = await get_hybrid_library_context(["react"], include_anti_patterns=True)
```

### Multi-Library Analysis

```python
# Analyze entire tech stack
libraries = ["react", "fastapi", "supabase", "docker"]
context = await get_hybrid_library_context(
    library_names=libraries,
    include_anti_patterns=True,
    focus_topic="authentication"
)

# Extract anti-patterns for review
for lib_name, lib_context in context["libraries"].items():
    anti_patterns = lib_context["anti_patterns"]
    high_severity = [p for p in anti_patterns if p["severity"] == "high"]
    if high_severity:
        print(f"⚠️ High-severity patterns in {lib_name}: {len(high_severity)}")
```

### Cache Monitoring

```python
# Monitor cache performance
result = await resolve_library_id("popular-library")
stats = result["cache_stats"]

if stats["hit_rate_percent"] < 50:
    print("⚠️ Low cache hit rate - consider cache optimization")

if stats["cache_size"] > stats["max_cache_size"] * 0.9:
    print("ℹ️ Cache approaching size limit")
```

## Migration from Manual Knowledge Base

### Gradual Migration Strategy

1. **Phase 1**: Use hybrid approach (current implementation)
2. **Phase 2**: Migrate high-traffic libraries to Context7-only
3. **Phase 3**: Deprecate manual entries for libraries with Context7 coverage
4. **Phase 4**: Maintain only vibe-check-specific anti-patterns locally

### Preserving Custom Patterns

Critical vibe-check-specific anti-patterns remain in the local knowledge base:
- Integration decision anti-patterns (Cognee case study patterns)
- Custom development red flags
- Project-specific pattern exceptions

## Version History

- **v0.5.2**: Initial Context7 integration with hybrid approach
- **v0.5.3**: Enhanced caching, validation, and knowledge base integration
- **v0.5.4**: Integration tests and performance optimization