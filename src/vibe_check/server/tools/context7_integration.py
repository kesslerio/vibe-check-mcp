"""
Context7 MCP Server Integration Tools

Provides hybrid library documentation system combining Context7's real-time
documentation with local anti-pattern detection rules.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from mcp.server.fastmcp import FastMCP
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states for external API calls."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls due to failures
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """Circuit breaker pattern for external API calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitBreakerState.CLOSED

    def call_allowed(self) -> bool:
        """Check if call is allowed based on circuit breaker state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Record successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class Context7Config:
    """Configuration class for Context7Manager with environment variable support."""

    def __init__(self):
        self.max_cache_size = int(os.getenv("CONTEXT7_MAX_CACHE_SIZE", "1000"))
        self.max_memory_bytes = (
            int(os.getenv("CONTEXT7_MAX_MEMORY_MB", "50")) * 1024 * 1024
        )
        self.cache_ttl = int(os.getenv("CONTEXT7_CACHE_TTL_SECONDS", "3600"))
        self.timeout = int(os.getenv("CONTEXT7_TIMEOUT_SECONDS", "30"))
        self.rate_limit_requests = int(os.getenv("CONTEXT7_RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(
            os.getenv("CONTEXT7_RATE_LIMIT_WINDOW_SECONDS", "60")
        )
        self.circuit_breaker_threshold = int(
            os.getenv("CONTEXT7_CIRCUIT_BREAKER_THRESHOLD", "5")
        )
        self.circuit_breaker_timeout = int(
            os.getenv("CONTEXT7_CIRCUIT_BREAKER_TIMEOUT", "60")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for logging/debugging."""
        return {
            "max_cache_size": self.max_cache_size,
            "max_memory_mb": self.max_memory_bytes // (1024 * 1024),
            "cache_ttl_seconds": self.cache_ttl,
            "timeout_seconds": self.timeout,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window_seconds": self.rate_limit_window,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "circuit_breaker_timeout": self.circuit_breaker_timeout,
        }


class Context7Manager:
    """Manages Context7 MCP server interactions with caching and fallback."""

    def __init__(
        self,
        max_cache_size: int = 1000,  # Backward compatibility
        config: Optional[Context7Config] = None,
        mcp_client: Optional[Any] = None,
    ):
        if mcp_client and not hasattr(mcp_client, "call_tool"):
            raise ValueError("Invalid MCP client provided to Context7Manager")

        # Initialize configuration (backward compatible)
        if config is None:
            # Create config but allow max_cache_size override for backward compatibility
            self._config = Context7Config()
            if max_cache_size != 1000:  # User specified a custom cache size
                self._config.max_cache_size = max_cache_size
        else:
            self._config = config

        logger.info(
            f"Context7Manager initialized with config: {self._config.to_dict()}"
        )

        # Cache and tracking
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._current_memory_usage = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._context7_resolve_success = 0
        self._context7_resolve_failure = 0
        self._context7_docs_success = 0
        self._context7_docs_failure = 0
        self._rate_limit_tracker: Dict[str, List[float]] = {}

        # Circuit breaker for external API calls
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self._config.circuit_breaker_threshold,
            recovery_timeout=self._config.circuit_breaker_timeout,
        )

        # External dependencies
        self._knowledge_base: Optional[Dict[str, Any]] = None
        self._mcp_client = mcp_client  # MCP client for Context7 API calls
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """Load existing integration knowledge base for fallback patterns."""
        try:
            # Find knowledge base file relative to project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent.parent
            kb_path = project_root / "data" / "integration_knowledge_base.json"

            if kb_path.exists():
                with open(kb_path, "r") as f:
                    self._knowledge_base = json.load(f)
                logger.info(
                    f"Loaded knowledge base with {len(self._knowledge_base)} libraries"
                )
            else:
                logger.warning(f"Knowledge base not found at {kb_path}")
                self._knowledge_base = {}
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            self._knowledge_base = {}

    def _estimate_memory_usage(self, data: Any) -> int:
        """Estimate memory usage of data in bytes."""
        if isinstance(data, str):
            return len(data.encode("utf-8"))
        elif isinstance(data, dict):
            return sum(
                self._estimate_memory_usage(k) + self._estimate_memory_usage(v)
                for k, v in data.items()
            )
        elif isinstance(data, (list, tuple)):
            return sum(self._estimate_memory_usage(item) for item in data)
        elif isinstance(data, (int, float)):
            return sys.getsizeof(data)
        else:
            return sys.getsizeof(data)

    def _validate_library_name(self, library_name: str) -> bool:
        """Validate library name input with strict security rules."""
        if not library_name or not isinstance(library_name, str):
            return False

        library_name = library_name.strip()

        # Length validation - more restrictive
        if len(library_name) == 0 or len(library_name) > 50:
            return False

        # Strict regex - only allow lowercase alphanumeric, hyphens, dots
        # No consecutive special characters, must start and end with alphanumeric
        import re

        if not re.match(r"^[a-z0-9]+([.-]?[a-z0-9]+)*$", library_name):
            return False

        # Prevent common injection patterns
        dangerous_patterns = ["..", "--", "..", "script", "eval", "exec", "import"]
        if any(pattern in library_name.lower() for pattern in dangerous_patterns):
            return False

        return True

    def _check_rate_limit(
        self,
        client_id: str = "default",
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> bool:
        """Check if client is within rate limits."""
        # Use config defaults if not specified
        max_requests = max_requests or self._config.rate_limit_requests
        window_seconds = window_seconds or self._config.rate_limit_window

        current_time = time.time()

        # Initialize tracker for new clients
        if client_id not in self._rate_limit_tracker:
            self._rate_limit_tracker[client_id] = []

        # Clean old requests outside the window
        self._rate_limit_tracker[client_id] = [
            req_time
            for req_time in self._rate_limit_tracker[client_id]
            if current_time - req_time < window_seconds
        ]

        # Check if within limits
        if len(self._rate_limit_tracker[client_id]) >= max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False

        # Record this request
        self._rate_limit_tracker[client_id].append(current_time)
        return True

    def _enforce_cache_limits(self) -> None:
        """Enforce both cache size and memory limits by removing oldest entries."""
        entries_removed = 0

        # First check memory limit
        while (
            self._current_memory_usage > self._config.max_memory_bytes and self._cache
        ):
            # Find and remove oldest entry
            oldest_key = min(
                self._cache.keys(), key=lambda k: self._cache[k]["timestamp"]
            )
            old_entry = self._cache[oldest_key]
            entry_size = self._estimate_memory_usage(old_entry["data"])
            del self._cache[oldest_key]
            self._current_memory_usage -= entry_size
            entries_removed += 1

        # Then check entry count limit
        while len(self._cache) > self._config.max_cache_size:
            oldest_key = min(
                self._cache.keys(), key=lambda k: self._cache[k]["timestamp"]
            )
            old_entry = self._cache[oldest_key]
            entry_size = self._estimate_memory_usage(old_entry["data"])
            del self._cache[oldest_key]
            self._current_memory_usage -= entry_size
            entries_removed += 1

        if entries_removed > 0:
            logger.debug(
                f"Cache limits enforced, removed {entries_removed} entries. "
                f"Memory usage: {self._current_memory_usage / (1024*1024):.1f}MB / "
                f"{self._config.max_memory_bytes / (1024*1024):.1f}MB, "
                f"Entries: {len(self._cache)} / {self._config.max_cache_size}"
            )

    async def resolve_library_id(
        self, library_name: str, client_id: str = "default"
    ) -> Optional[str]:
        """
        Resolve library name to Context7-compatible ID with caching and rate limiting.

        Args:
            library_name: Library name (e.g., "react", "fastapi")
            client_id: Client identifier for rate limiting

        Returns:
            Context7-compatible library ID or None if not found
        """
        # Rate limiting check
        if not self._check_rate_limit(client_id):
            logger.warning(f"Rate limit exceeded for resolve request: {library_name}")
            return None

        # Input validation
        if not self._validate_library_name(library_name):
            logger.warning(f"Invalid library name: {library_name}")
            return None

        library_name = library_name.strip().lower()
        cache_key = f"resolve_{library_name}"

        # Check cache first
        if self._is_cache_valid(cache_key):
            self._cache_hits += 1
            logger.debug(f"Cache hit for library resolution: {library_name}")
            return self._cache[cache_key]["data"]

        self._cache_misses += 1

        # Check circuit breaker before making external call
        if not self._circuit_breaker.call_allowed():
            logger.warning(
                f"Circuit breaker is open, skipping Context7 call for {library_name}"
            )
            return None

        try:
            # Try Context7 resolution with timeout
            result = await asyncio.wait_for(
                self._call_context7_resolve(library_name), timeout=self._config.timeout
            )

            # Record success if we got a result
            if result:
                self._circuit_breaker.record_success()

            # Cache successful result and enforce limits
            self._set_cache(cache_key, result)
            self._enforce_cache_limits()
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Context7 resolve timeout for {library_name}")
            self._circuit_breaker.record_failure()
            return None
        except Exception as e:
            logger.error(f"Context7 resolve error for {library_name}: {e}")
            self._circuit_breaker.record_failure()
            return None

    async def get_library_docs(
        self, library_id: str, topic: Optional[str] = None, client_id: str = "default"
    ) -> Optional[str]:
        """
        Fetch library documentation from Context7 with caching and rate limiting.

        Args:
            library_id: Context7-compatible library ID
            topic: Optional topic filter for focused documentation
            client_id: Client identifier for rate limiting

        Returns:
            Library documentation or None if not available
        """
        # Rate limiting check
        if not self._check_rate_limit(
            client_id, max_requests=50
        ):  # Stricter limit for docs
            logger.warning(f"Rate limit exceeded for docs request: {library_id}")
            return None

        # Input validation
        if (
            not library_id
            or not isinstance(library_id, str)
            or len(library_id.strip()) == 0
        ):
            logger.warning(f"Invalid library_id: {library_id}")
            return None

        cache_key = f"docs_{library_id}_{topic or 'general'}"

        # Check cache first
        if self._is_cache_valid(cache_key):
            self._cache_hits += 1
            logger.debug(f"Cache hit for library docs: {library_id}")
            return self._cache[cache_key]["data"]

        self._cache_misses += 1

        # Check circuit breaker before making external call
        if not self._circuit_breaker.call_allowed():
            logger.warning(
                f"Circuit breaker is open, skipping Context7 docs call for {library_id}"
            )
            return None

        try:
            # Try Context7 documentation fetch with timeout
            result = await asyncio.wait_for(
                self._call_context7_docs(library_id, topic),
                timeout=self._config.timeout,
            )

            # Record success if we got a result
            if result:
                self._circuit_breaker.record_success()

            # Cache successful result and enforce limits
            self._set_cache(cache_key, result)
            self._enforce_cache_limits()
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Context7 docs timeout for {library_id}")
            self._circuit_breaker.record_failure()
            return None
        except Exception as e:
            logger.error(f"Context7 docs error for {library_id}: {e}")
            self._circuit_breaker.record_failure()
            return None

    def _select_best_library_match(
        self, library_name: str, context7_response: Union[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Select the best library match from Context7 response.
        Handles both legacy string format and new structured JSON format.

        Args:
            library_name: Original library name searched for
            context7_response: Raw Context7 response (string or dict)

        Returns:
            Best matching Context7-compatible library ID or None
        """
        entries = []
        if isinstance(context7_response, str):
            # Legacy string parsing
            if "Context7-compatible library ID:" not in context7_response:
                return None
            lines = context7_response.split("\n")
            current_entry = {}
            for line in lines:
                line = line.strip()
                if line.startswith("- Title:"):
                    if current_entry:
                        entries.append(current_entry)
                    current_entry = {"title": line.replace("- Title:", "").strip()}
                elif line.startswith("- Context7-compatible library ID:"):
                    current_entry["library_id"] = line.replace(
                        "- Context7-compatible library ID:", ""
                    ).strip()
                elif line.startswith("- Description:"):
                    current_entry["description"] = line.replace(
                        "- Description:", ""
                    ).strip()
                elif line.startswith("- Code Snippets:"):
                    try:
                        current_entry["code_snippets"] = int(
                            line.replace("- Code Snippets:", "").strip()
                        )
                    except ValueError:
                        current_entry["code_snippets"] = 0
                elif line.startswith("- Trust Score:"):
                    try:
                        current_entry["trust_score"] = float(
                            line.replace("- Trust Score:", "").strip()
                        )
                    except ValueError:
                        current_entry["trust_score"] = 0.0
            if current_entry:
                entries.append(current_entry)

        elif isinstance(context7_response, dict) and "libraries" in context7_response:
            # New structured JSON format
            entries = context7_response["libraries"]

        if not entries:
            return None

        # Selection logic
        library_name_lower = library_name.lower()

        for entry in entries:
            title = entry.get("title", "").lower()
            if title == library_name_lower or library_name_lower in title:
                trust_score = entry.get("trust_score", 0)
                if trust_score >= 8.0:
                    return entry.get("library_id")

        high_quality_matches = [
            entry
            for entry in entries
            if entry.get("trust_score", 0) >= 8.0
            and entry.get("code_snippets", 0) >= 100
        ]
        if high_quality_matches:
            high_quality_matches.sort(
                key=lambda x: (x.get("trust_score", 0), x.get("code_snippets", 0)),
                reverse=True,
            )
            return high_quality_matches[0].get("library_id")

        if entries:
            entries.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
            best_match = entries[0]
            if best_match.get("trust_score", 0) >= 7.0:
                return best_match.get("library_id")

        return None

    async def _call_context7_resolve(self, library_name: str) -> Optional[str]:
        """Call Context7 resolve-library-id tool using MCP integration."""
        if not self._mcp_client:
            logger.warning(
                "No MCP client available for Context7, falling back to hardcoded mappings"
            )
            library_mappings = {
                "react": "/facebook/react",
                "fastapi": "/tiangolo/fastapi",
                "supabase": "/supabase/supabase",
                "nextjs": "/vercel/next.js",
                "express": "/expressjs/express",
            }
            return library_mappings.get(library_name.lower())

        try:
            logger.info(f"Calling Context7 MCP tool to resolve: {library_name}")
            result = await self._mcp_client.call_tool(
                "mcp__Context7__resolve-library-id", libraryName=library_name
            )

            if result:
                library_id = self._select_best_library_match(library_name, result)
                if library_id:
                    logger.info(f"Context7 resolved {library_name} to {library_id}")
                    self._context7_resolve_success += 1
                    return library_id
                else:
                    logger.warning(
                        f"Context7 found matches for {library_name} but none met selection criteria"
                    )
                    self._context7_resolve_failure += 1
                    return None
            else:
                logger.warning(f"Context7 returned no results for {library_name}")
                self._context7_resolve_failure += 1
                return None

        except Exception as e:
            logger.error(f"Context7 MCP call failed for {library_name}: {e}")
            self._context7_resolve_failure += 1
            return None

    async def _call_context7_docs(
        self, library_id: str, topic: Optional[str] = None
    ) -> Optional[str]:
        """Call Context7 get-library-docs tool using MCP integration."""
        if not self._mcp_client:
            logger.warning(
                "No MCP client available for Context7, falling back to simulated docs"
            )
            return f"# {library_id} Documentation\n\nReal-time documentation from Context7.\n\n**Topic**: {topic or 'General'}"

        try:
            logger.info(f"Calling Context7 MCP tool to get docs for: {library_id}")
            call_params = {"context7CompatibleLibraryID": library_id}
            if topic:
                call_params["topic"] = topic

            result = await self._mcp_client.call_tool(
                "mcp__Context7__get-library-docs", **call_params
            )

            if isinstance(result, str) and result:
                logger.info(
                    f"Context7 retrieved docs for {library_id} (topic: {topic or 'general'})"
                )
                self._context7_docs_success += 1
                return result
            elif isinstance(result, dict):
                docs = (
                    result.get("documentation") or result.get("content") or str(result)
                )
                if docs:
                    logger.info(f"Context7 retrieved structured docs for {library_id}")
                    self._context7_docs_success += 1
                    return docs

            logger.warning(f"Context7 returned no documentation for {library_id}")
            self._context7_docs_failure += 1
            return None

        except Exception as e:
            logger.error(f"Context7 MCP docs call failed for {library_id}: {e}")
            self._context7_docs_failure += 1
            return None

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid (exists and not expired)."""
        if cache_key not in self._cache:
            return False
        return (
            time.time() - self._cache[cache_key]["timestamp"] < self._config.cache_ttl
        )

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set cache entry with current timestamp and update memory tracking."""
        entry_size = self._estimate_memory_usage(data)
        self._cache[cache_key] = {"data": data, "timestamp": time.time()}
        self._current_memory_usage += entry_size

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (
            (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "max_cache_size": self._config.max_cache_size,
            "memory_usage_mb": round(self._current_memory_usage / (1024 * 1024), 2),
            "max_memory_mb": round(self._config.max_memory_bytes / (1024 * 1024), 2),
            "circuit_breaker_state": self._circuit_breaker.state.value,
            "circuit_breaker_failures": self._circuit_breaker.failure_count,
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including configuration and health."""
        return {
            "config": self._config.to_dict(),
            "cache_stats": self.get_cache_stats(),
            "api_stats": {
                "context7_resolve_success": self._context7_resolve_success,
                "context7_resolve_failure": self._context7_resolve_failure,
                "context7_docs_success": self._context7_docs_success,
                "context7_docs_failure": self._context7_docs_failure,
            },
            "circuit_breaker": {
                "state": self._circuit_breaker.state.value,
                "failure_count": self._circuit_breaker.failure_count,
                "last_failure_time": self._circuit_breaker.last_failure_time,
            },
            "health": {
                "mcp_client_available": self._mcp_client is not None,
                "knowledge_base_loaded": self._knowledge_base is not None,
                "cache_healthy": len(self._cache) < self._config.max_cache_size * 0.9,
                "memory_healthy": self._current_memory_usage
                < self._config.max_memory_bytes * 0.9,
            },
        }


# Global Context7 manager instance
context7_manager = Context7Manager()


def register_context7_tools(mcp: FastMCP):
    """Register Context7 integration tools with the MCP server."""
    # The manager is already initialized globally and ready to use

    @mcp.tool(
        name="resolve_library_id",
        description="Resolve library name to Context7-compatible ID for documentation retrieval",
    )
    async def resolve_library_id(library_name: str) -> Dict[str, Any]:
        """
        Resolve library name to Context7-compatible library ID.

        Args:
            library_name: Name of the library (e.g., "react", "fastapi", "supabase")

        Returns:
            Result with resolved library ID or error
        """
        try:
            # Input validation
            if not context7_manager._validate_library_name(library_name):
                return {
                    "status": "error",
                    "message": f"Invalid library name: {library_name}",
                    "details": "Library name must be alphanumeric, between 1 and 100 characters, and contain no spaces or special characters other than ._-",
                }

            library_id = await context7_manager.resolve_library_id(library_name)

            if library_id:
                return {
                    "status": "success",
                    "library_name": library_name,
                    "library_id": library_id,
                    "message": f"Resolved {library_name} to Context7 ID: {library_id}",
                }
            else:
                return {
                    "status": "not_found",
                    "library_name": library_name,
                    "library_id": None,
                    "message": f"Could not resolve library: {library_name}",
                }

        except Exception as e:
            logger.error(f"Error resolving library {library_name}: {e}")
            return {
                "status": "error",
                "message": f"An unexpected error occurred while resolving library: {library_name}",
                "details": str(e),
            }

    @mcp.tool(
        name="get_library_documentation",
        description="Fetch real-time library documentation from Context7",
    )
    async def get_library_documentation(
        library_id: str, topic: Optional[str] = None, max_tokens: int = 10000
    ) -> Dict[str, Any]:
        """
        Fetch library documentation from Context7.

        Args:
            library_id: Context7-compatible library ID (e.g., "/facebook/react")
            topic: Optional topic filter (e.g., "hooks", "authentication")
            max_tokens: Maximum tokens to return (default: 10000)

        Returns:
            Result with documentation content or error
        """
        try:
            # Input validation
            if (
                not library_id
                or not isinstance(library_id, str)
                or len(library_id.strip()) == 0
            ):
                return {
                    "status": "error",
                    "message": f"Invalid library_id: {library_id}",
                    "details": "library_id must be a valid Context7-compatible ID string.",
                }

            docs = await context7_manager.get_library_docs(library_id, topic)

            if docs:
                return {
                    "status": "success",
                    "library_id": library_id,
                    "topic": topic,
                    "documentation": docs,
                    "message": f"Retrieved documentation for {library_id}",
                }
            else:
                return {
                    "status": "not_found",
                    "library_id": library_id,
                    "topic": topic,
                    "documentation": None,
                    "message": f"No documentation found for {library_id}",
                }

        except Exception as e:
            logger.error(f"Error fetching docs for {library_id}: {e}")
            return {
                "status": "error",
                "message": f"An unexpected error occurred while fetching documentation for {library_id}",
                "details": str(e),
            }

    # Developer/Debug tool - only expose in development mode
    if os.getenv("VIBE_CHECK_DEBUG_MODE", "false").lower() == "true":

        @mcp.tool(
            name="get_context7_system_status",
            description="[DEBUG] Get Context7 integration system status including configuration and health",
        )
        async def get_context7_system_status() -> Dict[str, Any]:
            """
            Get comprehensive Context7 system status (DEBUG MODE ONLY).

            Returns:
                System status including configuration, cache stats, circuit breaker state, and health metrics
            """
            try:
                return {
                    "status": "success",
                    "system_status": context7_manager.get_system_status(),
                    "message": "Context7 system status retrieved successfully (DEBUG MODE)",
                }
            except Exception as e:
                logger.error(f"Error getting Context7 system status: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to get system status: {str(e)}",
                }

    @mcp.tool(
        name="get_hybrid_library_context",
        description="Get comprehensive library context combining Context7 docs with local patterns",
    )
    async def get_hybrid_library_context(
        library_names: List[str],
        include_anti_patterns: bool = True,
        focus_topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get hybrid library context combining Context7 documentation with local anti-pattern rules.

        Args:
            library_names: List of library names to analyze
            include_anti_patterns: Whether to include local anti-pattern detection
            focus_topic: Optional topic to focus documentation on

        Returns:
            Comprehensive library context with docs and patterns
        """
        try:
            results = {}

            for library_name in library_names:
                # Step 1: Resolve library ID
                library_id = await context7_manager.resolve_library_id(library_name)

                library_context = {
                    "library_name": library_name,
                    "library_id": library_id,
                    "documentation": None,
                    "anti_patterns": [],
                    "status": "unknown",
                }

                # Step 2: Get documentation if resolved
                if library_id:
                    docs = await context7_manager.get_library_docs(
                        library_id, focus_topic
                    )
                    library_context["documentation"] = docs
                    library_context["status"] = "documented" if docs else "no_docs"
                else:
                    library_context["status"] = "not_found"

                # Step 3: Add local anti-patterns if requested
                if include_anti_patterns:
                    library_context["anti_patterns"] = await _get_local_anti_patterns(
                        library_name
                    )

                results[library_name] = library_context

            return {
                "status": "success",
                "libraries": results,
                "focus_topic": focus_topic,
                "context_source": "hybrid",
                "message": f"Retrieved hybrid context for {len(library_names)} libraries",
            }

        except Exception as e:
            logger.error(f"Error getting hybrid context: {e}")
            return {
                "status": "error",
                "libraries": {},
                "message": f"Error getting hybrid context: {str(e)}",
            }


async def _get_local_anti_patterns(
    library_name: str,
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Get local anti-patterns for a library from knowledge base.

    Args:
        library_name: Name of the library

    Returns:
        List of anti-pattern rules for the library
    """
    if not context7_manager._knowledge_base:
        return []

    library_name = library_name.lower()
    library_data = context7_manager._knowledge_base.get(library_name, {})

    if not library_data:
        return []

    # Extract anti-patterns from knowledge base structure
    patterns = []

    # Get red flags as anti-patterns
    red_flags = library_data.get("red_flags", [])
    for flag in red_flags:
        patterns.append(
            {
                "pattern": flag,
                "description": f"Anti-pattern detected in {library_name}: {flag}",
                "severity": "high",
                "source": "knowledge_base",
            }
        )

    # Get version-specific anti-patterns
    versions = library_data.get("versions", {})
    for version, version_data in versions.items():
        version_anti_patterns = version_data.get("anti_patterns", [])
        for anti_pattern in version_anti_patterns:
            patterns.append(
                {
                    "pattern": anti_pattern,
                    "description": f"Version {version} anti-pattern: {anti_pattern}",
                    "severity": "medium",
                    "source": "knowledge_base",
                    "version": version,
                }
            )

    # Add official SDK recommendation if custom implementation detected
    official_sdks = library_data.get("official_sdks", [])
    if official_sdks:
        patterns.append(
            {
                "pattern": "custom-implementation-over-official-sdk",
                "description": f"Consider using official SDKs: {', '.join(official_sdks)}",
                "severity": "medium",
                "source": "knowledge_base",
                "recommended_sdks": official_sdks,
            }
        )

    return patterns


logger.info("Context7 integration tools module loaded")
