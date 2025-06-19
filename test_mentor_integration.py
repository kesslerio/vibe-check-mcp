#!/usr/bin/env python3
"""Integration test for enhanced vibe mentor through MCP server"""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.server import mcp

async def test_vibe_mentor():
    """Test vibe mentor tool through MCP interface"""
    
    # Get the vibe_check_mentor tool
    mentor_tool = None
    for tool in await mcp.get_tools():
        if tool.name == "vibe_check_mentor":
            mentor_tool = tool
            break
    
    if not mentor_tool:
        print("❌ vibe_check_mentor tool not found!")
        return
    
    print("✅ Found vibe_check_mentor tool")
    print(f"Description: {mentor_tool.description[:100]}...")
    
    # Test cases with expected specific responses
    test_cases = [
        {
            "name": "Stripe SDK vs Custom",
            "args": {
                "query": "Should I build a custom HTTP client for Stripe payment processing?",
                "context": "We need to handle payments, subscriptions, and webhooks for 1000 customers",
                "reasoning_depth": "standard"
            },
            "expected_keywords": ["Stripe", "SDK", "official", "webhooks", "retry"]
        },
        {
            "name": "Auth Library Selection", 
            "args": {
                "query": "Building custom JWT authentication for NextJS app - good idea?",
                "context": "React/NextJS app with PostgreSQL backend, need user roles and permissions",
                "reasoning_depth": "standard"
            },
            "expected_keywords": ["NextAuth", "Auth0", "Clerk", "library", "never write auth"]
        },
        {
            "name": "Microservices Decision",
            "args": {
                "query": "Should we use microservices architecture for our 5-person startup?",
                "context": "Building a SaaS product, expecting 1000 users in first year",
                "reasoning_depth": "comprehensive"
            },
            "expected_keywords": ["monolith", "complexity", "team size", "premature", "scaling"]
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"Test: {test['name']}")
        print(f"Query: {test['args']['query']}")
        
        # Call the tool
        result = await mentor_tool.invoke(test['args'])
        
        if result.get("status") == "error":
            print(f"❌ Error: {result.get('message')}")
            continue
        
        # Extract responses
        perspectives = result.get("collaborative_insights", {}).get("perspectives", {})
        
        print("\n--- Senior Engineer Response ---")
        senior_response = perspectives.get("senior_engineer", {})
        print(f"Type: {senior_response.get('type')}")
        print(f"Confidence: {senior_response.get('confidence')}")
        print(f"Message: {senior_response.get('message', '')[:300]}...")
        
        # Check for expected keywords
        message = senior_response.get('message', '').lower()
        found_keywords = [kw for kw in test['expected_keywords'] if kw.lower() in message]
        
        if found_keywords:
            print(f"\n✅ Found expected keywords: {found_keywords}")
        else:
            print(f"\n⚠️  Missing expected keywords. Expected: {test['expected_keywords']}")
        
        # Show product engineer perspective if available
        if "product_engineer" in perspectives:
            print("\n--- Product Engineer Response ---")
            product_response = perspectives["product_engineer"]
            print(f"Message: {product_response.get('message', '')[:200]}...")
        
        # Show consensus points
        consensus = result.get("collaborative_insights", {}).get("consensus", [])
        if consensus:
            print(f"\n--- Consensus Points ---")
            for point in consensus[:3]:
                print(f"• {point}")

async def test_interrupt_mode():
    """Test interrupt mode functionality"""
    print(f"\n{'='*80}")
    print("Testing Interrupt Mode")
    print("="*80)
    
    # Get the tool
    mentor_tool = None
    for tool in await mcp.get_tools():
        if tool.name == "vibe_check_mentor":
            mentor_tool = tool
            break
    
    interrupt_queries = [
        {
            "query": "I'll build a custom HTTP wrapper for the Cognito API",
            "expected": ["Cognito", "SDK", "AWS"]
        },
        {
            "query": "Creating an abstraction layer for future database flexibility",
            "expected": ["YAGNI", "premature", "abstraction"]
        }
    ]
    
    for test in interrupt_queries:
        print(f"\nQuery: {test['query']}")
        
        result = await mentor_tool.invoke({
            "query": test['query'],
            "mode": "interrupt",
            "phase": "planning"
        })
        
        if result.get("interrupt"):
            print(f"⚠️  Interrupt triggered!")
            print(f"Question: {result.get('question')}")
            print(f"Suggestion: {result.get('suggestion')}")
            print(f"Severity: {result.get('severity')}")
            
            # Check for expected content
            question = result.get('question', '').lower()
            suggestion = result.get('suggestion', '').lower()
            combined = question + " " + suggestion
            
            found = [kw for kw in test['expected'] if kw.lower() in combined]
            if found:
                print(f"✅ Contains expected keywords: {found}")
        else:
            print("✅ No interrupt (good to proceed)")

async def main():
    print("Testing Enhanced Vibe Mentor Integration")
    print("="*80)
    
    await test_vibe_mentor()
    await test_interrupt_mode()
    
    print("\n✅ Integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main())