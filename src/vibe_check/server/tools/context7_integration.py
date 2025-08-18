"""
Context7 MCP Server Integration Tools

Provides hybrid library documentation system combining Context7's real-time
documentation with local anti-pattern detection rules.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

class Context7Manager:
    """Manages Context7 MCP server interactions with caching and fallback."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour TTL
        self._timeout = 30  # 30 second timeout for Context7 calls
        
    async def resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve library name to Context7-compatible ID with caching.
        
        Args:
            library_name: Library name (e.g., "react", "fastapi")
            
        Returns:
            Context7-compatible library ID or None if not found
        """
        cache_key = f"resolve_{library_name}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for library resolution: {library_name}")
            return self._cache[cache_key]["data"]
            
        try:
            # Try Context7 resolution with timeout
            result = await asyncio.wait_for(
                self._call_context7_resolve(library_name),
                timeout=self._timeout
            )
            
            # Cache successful result
            self._set_cache(cache_key, result)
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Context7 resolve timeout for {library_name}")
            return None
        except Exception as e:
            logger.error(f"Context7 resolve error for {library_name}: {e}")
            return None
    
    async def get_library_docs(self, library_id: str, topic: Optional[str] = None) -> Optional[str]:
        """
        Fetch library documentation from Context7 with caching.
        
        Args:
            library_id: Context7-compatible library ID
            topic: Optional topic filter for focused documentation
            
        Returns:
            Library documentation or None if not available
        """
        cache_key = f"docs_{library_id}_{topic or 'general'}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for library docs: {library_id}")
            return self._cache[cache_key]["data"]
            
        try:
            # Try Context7 documentation fetch with timeout
            result = await asyncio.wait_for(
                self._call_context7_docs(library_id, topic),
                timeout=self._timeout
            )
            
            # Cache successful result
            self._set_cache(cache_key, result)
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Context7 docs timeout for {library_id}")
            return None
        except Exception as e:
            logger.error(f"Context7 docs error for {library_id}: {e}")
            return None
    
    async def _call_context7_resolve(self, library_name: str) -> Optional[str]:
        """Call Context7 resolve-library-id tool (placeholder for MCP integration)."""
        # TODO: Replace with actual MCP tool call when Context7 is integrated
        # For now, return simulated mapping for testing
        library_mappings = {
            "react": "/facebook/react",
            "fastapi": "/tiangolo/fastapi", 
            "supabase": "/supabase/supabase",
            "nextjs": "/vercel/next.js",
            "express": "/expressjs/express"
        }
        return library_mappings.get(library_name.lower())
    
    async def _call_context7_docs(self, library_id: str, topic: Optional[str] = None) -> Optional[str]:
        """Call Context7 get-library-docs tool (placeholder for MCP integration)."""
        # TODO: Replace with actual MCP tool call when Context7 is integrated
        # For now, return simulated documentation
        return f"# {library_id} Documentation\n\nReal-time documentation from Context7.\n\n**Topic**: {topic or 'General'}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid (exists and not expired)."""
        if cache_key not in self._cache:
            return False
        return time.time() - self._cache[cache_key]["timestamp"] < self._cache_ttl
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set cache entry with current timestamp."""
        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }

# Global Context7 manager instance
context7_manager = Context7Manager()

def register_context7_tools(mcp: FastMCP):
    """Register Context7 integration tools with the MCP server."""
    
    @mcp.tool(
        name="resolve_library_id",
        description="Resolve library name to Context7-compatible ID for documentation retrieval"
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
            library_id = await context7_manager.resolve_library_id(library_name)
            
            if library_id:
                return {
                    "status": "success",
                    "library_name": library_name,
                    "library_id": library_id,
                    "message": f"Resolved {library_name} to Context7 ID: {library_id}"
                }
            else:
                return {
                    "status": "not_found",
                    "library_name": library_name,
                    "library_id": None,
                    "message": f"Could not resolve library: {library_name}"
                }
                
        except Exception as e:
            logger.error(f"Error resolving library {library_name}: {e}")
            return {
                "status": "error",
                "library_name": library_name,
                "library_id": None,
                "message": f"Error resolving library: {str(e)}"
            }
    
    @mcp.tool(
        name="get_library_documentation",
        description="Fetch real-time library documentation from Context7"
    )
    async def get_library_documentation(
        library_id: str, 
        topic: Optional[str] = None,
        max_tokens: int = 10000
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
            docs = await context7_manager.get_library_docs(library_id, topic)
            
            if docs:
                return {
                    "status": "success",
                    "library_id": library_id,
                    "topic": topic,
                    "documentation": docs,
                    "cached": False,  # TODO: Add cache hit detection
                    "message": f"Retrieved documentation for {library_id}"
                }
            else:
                return {
                    "status": "not_found",
                    "library_id": library_id,
                    "topic": topic,
                    "documentation": None,
                    "message": f"No documentation found for {library_id}"
                }
                
        except Exception as e:
            logger.error(f"Error fetching docs for {library_id}: {e}")
            return {
                "status": "error",
                "library_id": library_id,
                "topic": topic,
                "documentation": None,
                "message": f"Error fetching documentation: {str(e)}"
            }
    
    @mcp.tool(
        name="get_hybrid_library_context",
        description="Get comprehensive library context combining Context7 docs with local patterns"
    )
    async def get_hybrid_library_context(
        library_names: List[str],
        include_anti_patterns: bool = True,
        focus_topic: Optional[str] = None
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
                    "status": "unknown"
                }
                
                # Step 2: Get documentation if resolved
                if library_id:
                    docs = await context7_manager.get_library_docs(library_id, focus_topic)
                    library_context["documentation"] = docs
                    library_context["status"] = "documented" if docs else "no_docs"
                else:
                    library_context["status"] = "not_found"
                
                # Step 3: Add local anti-patterns if requested
                if include_anti_patterns:
                    library_context["anti_patterns"] = await _get_local_anti_patterns(library_name)
                
                results[library_name] = library_context
            
            return {
                "status": "success",
                "libraries": results,
                "focus_topic": focus_topic,
                "context_source": "hybrid",
                "message": f"Retrieved hybrid context for {len(library_names)} libraries"
            }
            
        except Exception as e:
            logger.error(f"Error getting hybrid context: {e}")
            return {
                "status": "error",
                "libraries": {},
                "message": f"Error getting hybrid context: {str(e)}"
            }

async def _get_local_anti_patterns(library_name: str) -> List[Dict[str, str]]:
    """
    Get local anti-patterns for a library from knowledge base.
    
    Args:
        library_name: Name of the library
        
    Returns:
        List of anti-pattern rules for the library
    """
    # TODO: Integrate with existing integration_knowledge_base.json
    # For now, return placeholder patterns
    common_patterns = {
        "react": [
            {
                "pattern": "Custom HTTP client instead of established libraries",
                "description": "Building custom fetch wrappers when axios/react-query exist",
                "severity": "medium"
            }
        ],
        "fastapi": [
            {
                "pattern": "Manual authentication instead of FastAPI security",
                "description": "Implementing custom auth when FastAPI has built-in security",
                "severity": "high"
            }
        ]
    }
    
    return common_patterns.get(library_name.lower(), [])

logger.info("Context7 integration tools module loaded")