"""
Web Search Integration for Integration Decision Tools

Uses available MCP tools (Tavily, Crawl4AI, Brave Search) to enhance 
integration decision analysis with real-time web research.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def search_technology_documentation(technology: str, custom_features: List[str] = None) -> Dict[str, Any]:
    """Search for official technology documentation using available MCP tools."""
    if custom_features is None:
        custom_features = []
        
    results = {
        "technology": technology,
        "searches_performed": [],
        "documentation_found": [],
        "containers_found": [],
        "sdks_found": [],
        "confidence_level": "unknown",
        "search_strategy": "hybrid_mcp_approach"
    }
    
    # Step 1: Try Context7 for library documentation (if it's a known library)
    try:
        context7_results = _search_with_context7(technology, custom_features)
        if context7_results and context7_results.get("documentation_found"):
            results.update(context7_results)
            results["searches_performed"].append("context7_library_docs")
            results["confidence_level"] = "high"
            logger.info(f"Context7 found comprehensive docs for {technology}")
            return results
    except Exception as e:
        logger.warning(f"Context7 search failed for {technology}: {e}")
    
    # Step 2: Try crawl4ai-rag for existing knowledge
    try:
        rag_results = _search_with_crawl4ai_rag(technology, custom_features)
        if rag_results and rag_results.get("relevant_content"):
            results.update(rag_results)
            results["searches_performed"].append("crawl4ai_rag_existing")
            results["confidence_level"] = "medium-high"
            return results
    except Exception as e:
        logger.warning(f"Crawl4AI RAG search failed for {technology}: {e}")
    
    # Step 3: Fallback to Tavily for comprehensive web search
    try:
        tavily_results = _search_with_tavily(technology, custom_features)
        if tavily_results:
            results.update(tavily_results)
            results["searches_performed"].append("tavily_web_search")
            results["confidence_level"] = "medium"
            return results
    except Exception as e:
        logger.warning(f"Tavily search failed for {technology}: {e}")
    
    # Step 4: Final fallback to Brave search
    try:
        brave_results = _search_with_brave(technology)
        if brave_results:
            results.update(brave_results)
            results["searches_performed"].append("brave_web_search")
            results["confidence_level"] = "low-medium"
            return results
    except Exception as e:
        logger.warning(f"Brave search failed for {technology}: {e}")
    
    # If all searches fail, provide manual search guidance
    results["searches_performed"].append("manual_guidance_only")
    results["manual_search_guidance"] = _get_manual_search_guidance(technology)
    results["confidence_level"] = "manual_research_required"
    
    return results

def _search_with_context7(technology: str, custom_features: List[str]) -> Optional[Dict[str, Any]]:
    """Search using Context7 MCP tool for official library documentation."""
    try:
        # Context7 is best for well-known libraries and frameworks
        # Note: Context7 tools aren't directly available but we can provide guidance
        # for using Context7 in the prompt to Claude
        
        # For integration decisions, we want to guide users to use Context7
        context7_guidance = {
            "documentation_found": True,
            "search_method": "context7",
            "usage_instruction": f"To get the most up-to-date {technology} documentation, use: 'How do I deploy {technology} in production? use context7'",
            "recommended_queries": [
                f"How do I deploy {technology}? use context7",
                f"What are the official {technology} installation methods? use context7",
                f"How do I configure {technology} for production? use context7",
                f"What are {technology} best practices? use context7"
            ],
            "context7_benefits": [
                "Access to latest documentation",
                "Version-specific information",
                "Official vendor sources",
                "Real-time updates"
            ],
            "integration_focus": []
        }
        
        # Add specific integration queries based on custom features
        for feature in custom_features:
            if "auth" in feature.lower():
                context7_guidance["recommended_queries"].append(f"How does {technology} handle authentication? use context7")
            if "api" in feature.lower() or "rest" in feature.lower():
                context7_guidance["recommended_queries"].append(f"What are {technology} API deployment options? use context7")
            if "container" in feature.lower() or "docker" in feature.lower():
                context7_guidance["recommended_queries"].append(f"How do I containerize {technology}? use context7")
        
        return context7_guidance
        
    except Exception as e:
        logger.error(f"Context7 guidance generation failed: {e}")
        return None

def _search_with_crawl4ai_rag(technology: str, custom_features: List[str]) -> Optional[Dict[str, Any]]:
    """Search using Crawl4AI-RAG for existing crawled documentation."""
    try:
        # Provide guidance for using crawl4ai-rag tools
        # In practice, this would use the actual MCP tools
        
        potential_docs = [
            f"https://docs.{technology.lower()}.com",
            f"https://{technology.lower()}.io/docs", 
            f"https://github.com/{technology.lower()}/{technology.lower()}",
            f"https://deepwiki.com/{technology.lower()}",  # Excellent for public GitHub repos
            f"https://{technology.lower()}.readthedocs.io"
        ]
        
        return {
            "relevant_content": False,
            "search_method": "crawl4ai_rag",
            "mcp_tools_guidance": {
                "step_1": "Use mcp__crawl4ai_rag__get_available_sources() to check existing crawled content",
                "step_2": f"Use mcp__crawl4ai_rag__perform_rag_query(query='{technology} official documentation', match_count=5)",
                "step_3": "If no results, use mcp__crawl4ai_rag__smart_crawl_url() to crawl official docs",
                "recommended_crawl_targets": potential_docs
            },
            "crawl_suggestions": potential_docs,
            "next_steps": [
                f"Search existing RAG database for {technology} documentation",
                "If not found, crawl official documentation sites",
                "Use smart_crawl_url for comprehensive documentation coverage",
                "DeepWiki.com is excellent for understanding public GitHub repositories"
            ]
        }
            
    except Exception as e:
        logger.error(f"Crawl4AI RAG search failed: {e}")
        return None

def _search_with_tavily(technology: str, custom_features: List[str]) -> Optional[Dict[str, Any]]:
    """Search using Tavily MCP tool."""
    try:
        # Import MCP tools - this should work in the MCP environment
        from ..server import mcp__tavily_mcp__tavily_search
        
        # Search for official documentation
        doc_query = f"{technology} official documentation deployment guide"
        doc_results = mcp__tavily_mcp__tavily_search(
            query=doc_query,
            max_results=5,
            include_raw_content=True
        )
        
        # Search for Docker containers
        container_query = f"{technology} official docker container"
        container_results = mcp__tavily_mcp__tavily_search(
            query=container_query,
            max_results=3,
            include_domains=["hub.docker.com", "docker.com"]
        )
        
        # Search for SDKs including DeepWiki for public repos
        sdk_query = f"{technology} official SDK API client"
        sdk_results = mcp__tavily_mcp__tavily_search(
            query=sdk_query,
            max_results=5,
            include_domains=["github.com", "npmjs.com", "pypi.org", "deepwiki.com"]
        )
        
        # Search DeepWiki specifically for public GitHub repo insights
        deepwiki_query = f"{technology} site:deepwiki.com"
        deepwiki_results = mcp__tavily_mcp__tavily_search(
            query=deepwiki_query,
            max_results=3,
            include_domains=["deepwiki.com"]
        )
        
        return {
            "documentation_search": _extract_tavily_results(doc_results),
            "container_search": _extract_tavily_results(container_results),
            "sdk_search": _extract_tavily_results(sdk_results),
            "deepwiki_search": _extract_tavily_results(deepwiki_results),
            "confidence_level": "high",
            "search_method": "tavily",
            "deepwiki_advantage": "DeepWiki provides excellent structured documentation for public GitHub repositories"
        }
        
    except ImportError:
        logger.info("Tavily MCP tool not available")
        return None
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return None

def _search_with_brave(technology: str) -> Optional[Dict[str, Any]]:
    """Search using Brave Search MCP tool."""
    try:
        from ..server import mcp__brave_search__brave_web_search
        
        # Search for official resources
        doc_query = f"{technology} official documentation"
        doc_results = mcp__brave_search__brave_web_search(
            query=doc_query,
            count=5
        )
        
        container_query = f"{technology} docker container official"
        container_results = mcp__brave_search__brave_web_search(
            query=container_query,
            count=3
        )
        
        return {
            "documentation_search": _extract_brave_results(doc_results),
            "container_search": _extract_brave_results(container_results),
            "confidence_level": "medium",
            "search_method": "brave"
        }
        
    except ImportError:
        logger.info("Brave Search MCP tool not available")
        return None
    except Exception as e:
        logger.error(f"Brave search error: {e}")
        return None

def _search_with_crawl4ai(technology: str) -> Optional[Dict[str, Any]]:
    """Search using Crawl4AI RAG tool for known documentation sites."""
    try:
        from ..server import mcp__crawl4ai_rag__perform_rag_query, mcp__crawl4ai_rag__smart_crawl_url
        
        # Try to find existing crawled content
        rag_query = f"{technology} official documentation deployment"
        rag_results = mcp__crawl4ai_rag__perform_rag_query(
            query=rag_query,
            match_count=5
        )
        
        # Common documentation patterns to crawl
        potential_docs = [
            f"https://docs.{technology.lower()}.com",
            f"https://{technology.lower()}.readthedocs.io",
            f"https://github.com/{technology.lower()}/{technology.lower()}",
        ]
        
        crawl_results = []
        for doc_url in potential_docs:
            try:
                result = mcp__crawl4ai_rag__smart_crawl_url(
                    url=doc_url,
                    max_depth=1,
                    chunk_size=1000
                )
                crawl_results.append(result)
            except:
                continue  # URL might not exist
        
        return {
            "rag_results": rag_results,
            "crawl_results": crawl_results,
            "confidence_level": "medium",
            "search_method": "crawl4ai"
        }
        
    except ImportError:
        logger.info("Crawl4AI MCP tool not available")
        return None
    except Exception as e:
        logger.error(f"Crawl4AI search error: {e}")
        return None

def _extract_tavily_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant information from Tavily search results."""
    if not results or "results" not in results:
        return {"found": False, "results": []}
    
    extracted = {
        "found": True,
        "results": [],
        "summary": ""
    }
    
    for result in results.get("results", []):
        extracted["results"].append({
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", "")[:500],  # Limit content length
            "score": result.get("score", 0)
        })
    
    return extracted

def _extract_brave_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant information from Brave search results."""
    if not results or "web" not in results:
        return {"found": False, "results": []}
    
    extracted = {
        "found": True,
        "results": []
    }
    
    for result in results.get("web", {}).get("results", []):
        extracted["results"].append({
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "description": result.get("description", ""),
        })
    
    return extracted

def _get_manual_search_guidance(technology: str) -> Dict[str, Any]:
    """Provide manual search guidance when automated search fails."""
    return {
        "search_queries": [
            f"{technology} official documentation",
            f"{technology} official docker container",
            f"{technology} official SDK",
            f"{technology} vs custom implementation",
            f"{technology} deployment guide"
        ],
        "search_sites": [
            f"site:docs.{technology.lower()}.com",
            f"site:github.com/{technology.lower()}",
            f"site:deepwiki.com/{technology.lower()}",  # Excellent for public GitHub repo understanding
            "site:hub.docker.com",
            "site:npmjs.com",
            "site:pypi.org"
        ],
        "validation_steps": [
            "Check if URLs are from official vendor domains",
            "Look for 'official' or 'verified' badges",
            "Check repository maintenance and recent updates",
            "Validate community adoption and documentation quality"
        ],
        "red_flags_to_avoid": [
            "Outdated documentation (>1 year old)",
            "Unofficial or community-only solutions",
            "Abandoned repositories with no recent commits",
            "Complex custom implementations without clear justification"
        ]
    }

def analyze_search_results_for_integration(results: Dict[str, Any], custom_features: List[str]) -> Dict[str, Any]:
    """Analyze search results to determine integration recommendations."""
    analysis = {
        "official_solutions_found": [],
        "confidence_assessment": "unknown",
        "integration_recommendations": [],
        "red_flags_identified": []
    }
    
    # Check for official documentation
    if results.get("documentation_search", {}).get("found"):
        doc_results = results["documentation_search"]["results"]
        for result in doc_results:
            if any(keyword in result.get("title", "").lower() for keyword in ["official", "docs", "documentation"]):
                analysis["official_solutions_found"].append({
                    "type": "documentation",
                    "title": result.get("title", ""),
                    "url": result.get("url", "")
                })
    
    # Check for official containers
    if results.get("container_search", {}).get("found"):
        container_results = results["container_search"]["results"]
        for result in container_results:
            if "hub.docker.com" in result.get("url", "") or "docker" in result.get("title", "").lower():
                analysis["official_solutions_found"].append({
                    "type": "container",
                    "title": result.get("title", ""),
                    "url": result.get("url", "")
                })
    
    # Assess confidence based on findings
    if len(analysis["official_solutions_found"]) >= 2:
        analysis["confidence_assessment"] = "high"
        analysis["integration_recommendations"] = [
            "Strong official support detected - test official solutions first",
            "Multiple deployment options available - compare official vs custom",
            "Consider official containers and SDKs before custom development"
        ]
    elif len(analysis["official_solutions_found"]) == 1:
        analysis["confidence_assessment"] = "medium"
        analysis["integration_recommendations"] = [
            "Some official support found - investigate thoroughly",
            "Validate official solution completeness for your requirements",
            "Document any gaps that justify custom development"
        ]
    else:
        analysis["confidence_assessment"] = "low"
        analysis["integration_recommendations"] = [
            "Limited official solutions found - custom development may be justified",
            "Ensure comprehensive research completed before proceeding",
            "Consider community solutions and document decision rationale"
        ]
    
    # Identify red flags based on custom features and search results
    for feature in custom_features:
        if any(keyword in feature.lower() for keyword in ["rest", "api", "server", "auth"]):
            if len(analysis["official_solutions_found"]) > 0:
                analysis["red_flags_identified"].append(f"Custom {feature} development detected despite official alternatives")
    
    return analysis