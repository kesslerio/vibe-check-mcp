#!/usr/bin/env python3
"""
Demo script showcasing MCP Sampling integration with vibe_check_mentor

This demonstrates how the mentor can now dynamically generate responses
for novel queries using MCP's native sampling protocol.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibe_check.mentor.mcp_sampling import (
    MCPSamplingClient,
    PromptBuilder,
    ResponseCache
)
from vibe_check.mentor.hybrid_router import (
    HybridRouter,
    ConfidenceScorer,
    RouteDecision
)


def demonstrate_confidence_scoring():
    """Show how confidence scoring works for different queries"""
    print("\n=== Confidence Scoring Demo ===\n")
    
    test_queries = [
        # High confidence (common patterns)
        ("Should I use React or Vue?", "decision", {"technologies": ["javascript"]}),
        ("How to implement authentication?", "implementation", {"technologies": ["django"]}),
        ("REST vs GraphQL", "decision", {"technologies": []}),
        
        # Low confidence (novel/specific scenarios)
        ("How to integrate ESLint hybrid automation with v3.2.1 API?", "integration", 
         {"technologies": ["eslint", "custom", "api", "v3.2.1"]}),
        ("Custom implementation in my project", "implementation", 
         {"technologies": ["custom", "proprietary"]}),
    ]
    
    for query, intent, context in test_queries:
        confidence, reasoning = ConfidenceScorer.calculate_confidence(
            query=query,
            intent=intent,
            context=context,
            has_workspace_context=False
        )
        
        print(f"Query: {query[:50]}...")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Reasoning: {reasoning}")
        print()


def demonstrate_routing_decisions():
    """Show how the hybrid router makes decisions"""
    print("\n=== Routing Decision Demo ===\n")
    
    router = HybridRouter(confidence_threshold=0.7)
    
    test_cases = [
        {
            "query": "Should I use microservices or monolith?",
            "intent": "architecture_decision",
            "context": {"technologies": ["python", "django"]},
            "has_workspace": False
        },
        {
            "query": "How to integrate our custom ESLint automation with the new API?",
            "intent": "integration",
            "context": {"technologies": ["eslint", "custom", "api"]},
            "has_workspace": True
        },
        {
            "query": "Debug memory leak in production",
            "intent": "debugging",
            "context": {"technologies": ["nodejs"], "patterns": ["memory_leak"]},
            "has_workspace": False
        }
    ]
    
    for case in test_cases:
        metrics = router.decide_route(
            query=case["query"],
            intent=case["intent"],
            context=case["context"],
            has_workspace_context=case["has_workspace"],
            has_static_response=True
        )
        
        print(f"Query: {case['query'][:50]}...")
        print(f"  Decision: {metrics.decision.value}")
        print(f"  Confidence: {metrics.confidence:.2f}")
        print(f"  Reasoning: {metrics.reasoning[:100]}...")
        print(f"  Est. Latency: {metrics.latency_estimate_ms}ms")
        print()
    
    # Show statistics
    stats = router.get_stats()
    print("Router Statistics:")
    for key, value in stats.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")


def demonstrate_prompt_building():
    """Show how prompts are built for different scenarios"""
    print("\n=== Prompt Building Demo ===\n")
    
    scenarios = [
        {
            "intent": "architecture_decision",
            "query": "Should we use Kubernetes for our startup?",
            "context": {
                "technologies": ["docker", "aws"],
                "patterns": ["over_engineering"]
            }
        },
        {
            "intent": "debugging_help",
            "query": "API timeout after 30 seconds",
            "context": {
                "technologies": ["fastapi", "postgres"],
                "patterns": ["slow_query"]
            },
            "workspace_data": {
                "files": ["api.py", "database.py"],
                "language": "python",
                "frameworks": ["fastapi"]
            }
        }
    ]
    
    for scenario in scenarios:
        prompt = PromptBuilder.build_prompt(
            intent=scenario["intent"],
            query=scenario["query"],
            context=scenario["context"],
            workspace_data=scenario.get("workspace_data")
        )
        
        print(f"Intent: {scenario['intent']}")
        print(f"Query: {scenario['query']}")
        print(f"Prompt Preview (first 300 chars):")
        print(f"  {prompt[:300]}...")
        print()


def demonstrate_response_caching():
    """Show how response caching improves performance"""
    print("\n=== Response Caching Demo ===\n")
    
    cache = ResponseCache(max_size=10)
    
    # Simulate adding responses to cache
    test_responses = [
        ("architecture", "microservices vs monolith", {"tech": ["python"]}, 
         {"content": "Start with monolith for MVP", "confidence": 0.9}),
        ("debugging", "memory leak", {"tech": ["nodejs"]},
         {"content": "Use heap snapshots and profiling", "confidence": 0.85}),
        ("implementation", "auth system", {"tech": ["django"]},
         {"content": "Use Django's built-in auth", "confidence": 0.95})
    ]
    
    # Add to cache
    for intent, query, context, response in test_responses:
        cache.put(intent, query, context, response)
        print(f"Cached: {query} -> {response['content'][:30]}...")
    
    print()
    
    # Test cache hits and misses
    test_queries = [
        ("architecture", "microservices vs monolith", {"tech": ["python"]}),  # Hit
        ("debugging", "memory leak", {"tech": ["nodejs"]}),  # Hit
        ("testing", "unit tests", {"tech": ["pytest"]}),  # Miss
    ]
    
    for intent, query, context in test_queries:
        result = cache.get(intent, query, context)
        if result:
            print(f"Cache HIT for '{query}': {result['content'][:30]}...")
        else:
            print(f"Cache MISS for '{query}'")
    
    # Show cache statistics
    print("\nCache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Run all demonstrations"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     MCP Sampling Integration for vibe_check_mentor Demo     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  This demo showcases the new dynamic response generation    ║
║  capability that uses MCP's native sampling protocol to     ║
║  handle novel queries without pre-written responses.        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    demonstrate_confidence_scoring()
    demonstrate_routing_decisions()
    demonstrate_prompt_building()
    demonstrate_response_caching()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                        Key Benefits                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Infinite Scalability: No pre-written responses needed   ║
║  2. Context Awareness: Understands unique situations        ║
║  3. Hybrid Approach: Fast static + flexible dynamic         ║
║  4. Smart Caching: Reduces latency for common queries       ║
║  5. No API Keys: Uses client's LLM via MCP protocol         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()