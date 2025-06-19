#!/usr/bin/env python3
"""Final test showcasing enhanced vibe mentor specificity"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.vibe_mentor import get_mentor_engine, cleanup_mentor_engine
from vibe_check.tools.analyze_text_nollm import analyze_text_demo

def test_specific_scenarios():
    """Test mentor with various specific technical scenarios"""
    
    scenarios = [
        {
            "name": "Payment Integration",
            "query": "Should I build a custom HTTP client for Stripe API?",
            "context": "Need to handle payments, subscriptions, and webhooks for SaaS",
            "expected_terms": ["stripe", "sdk", "webhook", "payment"]
        },
        {
            "name": "Authentication",
            "query": "I want to implement custom JWT authentication",
            "context": "NextJS app with role-based access control",
            "expected_terms": ["nextauth", "auth0", "clerk", "jwt", "library"]
        },
        {
            "name": "RAG System",
            "query": "Building a RAG system with custom vector database",
            "context": "100K documents, need semantic search",
            "expected_terms": ["langchain", "pinecone", "weaviate", "rag", "vector"]
        },
        {
            "name": "Microservices",
            "query": "Should we use microservices for our startup?",
            "context": "5 developers, expecting 10K users in year 1",
            "expected_terms": ["monolith", "complexity", "team", "scale"]
        },
        {
            "name": "Database Choice",
            "query": "MongoDB vs PostgreSQL for our app?",
            "context": "Social media features with complex relationships",
            "expected_terms": ["postgres", "mongodb", "relationships", "schema"]
        }
    ]
    
    engine = get_mentor_engine()
    
    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"Scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print(f"Context: {scenario['context']}")
        print("-"*80)
        
        # Run analysis
        combined = f"{scenario['query']}\n{scenario['context']}"
        analysis = analyze_text_demo(combined)
        patterns = analysis.get("patterns", [])
        detected = [p for p in patterns if p.get("detected")]
        
        # Create session
        session = engine.create_session(scenario['query'])
        
        # Get contributions from all personas
        all_found_terms = set()
        
        for i, persona in enumerate(session.personas):
            contribution = engine.generate_contribution(
                session=session,
                persona=persona,
                detected_patterns=detected,
                context=scenario['context']
            )
            
            # Check for expected terms
            content_lower = contribution.content.lower()
            found_terms = [term for term in scenario['expected_terms'] if term in content_lower]
            all_found_terms.update(found_terms)
            
            if found_terms:
                print(f"\n{persona.name}:")
                print(f"✅ Found specific terms: {found_terms}")
                print(f"Preview: {contribution.content[:150]}...")
        
        # Summary for scenario
        if len(all_found_terms) >= len(scenario['expected_terms']) * 0.5:
            print(f"\n✅ SCENARIO PASSED: Found {len(all_found_terms)}/{len(scenario['expected_terms'])} expected terms")
        else:
            print(f"\n⚠️  SCENARIO NEEDS IMPROVEMENT: Only found {len(all_found_terms)}/{len(scenario['expected_terms'])} terms")
            print(f"   Missing: {set(scenario['expected_terms']) - all_found_terms}")

def test_interrupt_mode():
    """Test interrupt mode with specific technologies"""
    print(f"\n{'='*80}")
    print("TESTING INTERRUPT MODE")
    print("="*80)
    
    engine = get_mentor_engine()
    
    interrupt_scenarios = [
        "I'll build a custom HTTP wrapper for Stripe payments",
        "Creating abstraction layer for future Cognito flexibility",
        "Implementing custom OAuth2 flow instead of using NextAuth"
    ]
    
    for query in interrupt_scenarios:
        print(f"\nQuery: {query}")
        
        # Analyze for patterns
        analysis = analyze_text_demo(query)
        patterns = analysis.get("patterns", [])
        detected = [p for p in patterns if p.get("detected")]
        
        if detected:
            primary = detected[0]
            result = engine.generate_interrupt_intervention(
                query=query,
                phase="planning",
                primary_pattern=primary,
                pattern_confidence=0.85
            )
            
            print(f"⚠️  Interrupt: {result['question']}")
            print(f"💡 Suggestion: {result['suggestion']}")
        else:
            print("✅ No patterns detected - proceed")

if __name__ == "__main__":
    print("ENHANCED VIBE MENTOR - FINAL TEST")
    print("="*80)
    print("Testing specific technical advice across multiple scenarios")
    
    test_specific_scenarios()
    test_interrupt_mode()
    
    cleanup_mentor_engine()
    print("\n✅ All tests completed!")