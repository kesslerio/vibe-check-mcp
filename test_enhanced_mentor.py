#!/usr/bin/env python3
"""Test script to verify enhanced vibe mentor functionality"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.vibe_mentor import get_mentor_engine, cleanup_mentor_engine
from vibe_check.tools.vibe_mentor_enhanced import ContextExtractor

def test_context_extraction():
    """Test that context extraction works properly"""
    print("\n=== Testing Context Extraction ===\n")
    
    test_queries = [
        "Should I build a custom HTTP client for Stripe API integration?",
        "I'm planning to create a React app with NextJS and integrate Supabase for auth",
        "Deciding between MongoDB and PostgreSQL for our microservices architecture",
        "Need to implement OAuth2 authentication with custom user management",
        "Building a RAG system with OpenAI embeddings and Pinecone vector database"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        context = ContextExtractor.extract_context(query)
        print(f"Technologies: {context.technologies}")
        print(f"Frameworks: {context.frameworks}")
        print(f"Problem Type: {context.problem_type}")
        print(f"Features: {context.specific_features}")
        print(f"Decisions: {context.decision_points}")
        print("-" * 50)

def test_mentor_responses():
    """Test that mentor gives specific responses"""
    print("\n=== Testing Mentor Responses ===\n")
    
    # Import the actual function implementation
    from vibe_check.tools.vibe_mentor import get_mentor_engine
    from vibe_check.tools.analyze_text_nollm import analyze_text_demo
    import secrets
    
    test_cases = [
        {
            "query": "Should I build a custom HTTP client for the Stripe API?",
            "context": "We need to process payments and handle webhooks",
            "expected_keywords": ["Stripe", "SDK", "official"]
        },
        {
            "query": "Planning to build custom authentication system with JWT",
            "context": "For our React/NextJS app with 1000 users",
            "expected_keywords": ["auth", "library", "Auth0", "Clerk", "NextAuth"]
        },
        {
            "query": "Implementing RAG with OpenAI and custom vector database",
            "context": "Need to search through 10K documents",
            "expected_keywords": ["Pinecone", "LangChain", "embeddings", "vector"]
        }
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\nTest {i+1}: {test['query']}")
        print(f"Context: {test['context']}")
        
        # Simulate the vibe_check_mentor function logic
        engine = get_mentor_engine()
        
        # Run pattern detection
        combined_text = f"{test['query']}\n\n{test['context']}"
        vibe_analysis = analyze_text_demo(combined_text, detail_level="standard")
        # Extract patterns from the analysis
        patterns = vibe_analysis.get("patterns", [])
        detected_patterns = [p for p in patterns if p.get("detected", False)]
        
        # Create session and generate contributions
        session = engine.create_session(topic=test['query'])
        
        # Generate contributions from first 2 personas (standard depth)
        for i in range(2):
            if i < len(session.personas):
                persona = session.personas[i]
                contribution = engine.generate_contribution(
                    session=session,
                    persona=persona,
                    detected_patterns=detected_patterns,
                    context=test['context']
                )
                session.contributions.append(contribution)
        
        # Build result similar to vibe_check_mentor output
        result = {
            "collaborative_insights": {
                "perspectives": {
                    contrib.persona_id: {
                        "message": contrib.content,
                        "type": contrib.type,
                        "confidence": contrib.confidence
                    }
                    for contrib in session.contributions
                }
            }
        }
        
        # Check senior engineer response
        if "collaborative_insights" in result:
            perspectives = result["collaborative_insights"]["perspectives"]
            senior_response = perspectives.get("senior_engineer", {}).get("message", "")
            
            print(f"\nSenior Engineer Response:")
            print(senior_response[:200] + "..." if len(senior_response) > 200 else senior_response)
            
            # Check for expected keywords
            found_keywords = [kw for kw in test["expected_keywords"] if kw.lower() in senior_response.lower()]
            print(f"\nFound expected keywords: {found_keywords}")
            
            if found_keywords:
                print("✅ Response is specific and contextual!")
            else:
                print("⚠️  Response might be too generic")
        
        print("-" * 80)

def test_interrupt_mode():
    """Test interrupt mode with specific contexts"""
    print("\n=== Testing Interrupt Mode ===\n")
    
    from vibe_check.tools.vibe_mentor import get_mentor_engine
    from vibe_check.tools.analyze_text_nollm import analyze_text_demo
    
    test_interrupts = [
        "I'll build a custom HTTP client for Cognito",
        "Creating abstraction layer for future database flexibility",
        "Implementing custom OAuth2 flow for Google auth"
    ]
    
    for query in test_interrupts:
        print(f"\nQuery: {query}")
        
        # Simulate interrupt mode logic
        engine = get_mentor_engine()
        vibe_analysis = analyze_text_demo(query, detail_level="standard")
        # Extract patterns from the analysis
        patterns = vibe_analysis.get("patterns", [])
        detected_patterns = [p for p in patterns if p.get("detected", False)]
        pattern_confidence = vibe_analysis.get("vibe_assessment", {}).get("confidence", 0)
        
        # Check if interrupt needed
        interrupt_needed = pattern_confidence > 0.7 and detected_patterns
        
        if interrupt_needed:
            primary_pattern = detected_patterns[0]
            result = engine.generate_interrupt_intervention(
                query=query,
                phase="planning",
                primary_pattern=primary_pattern,
                pattern_confidence=pattern_confidence
            )
            result["interrupt"] = True
        else:
            result = {"interrupt": False}
        
        if result.get("interrupt"):
            print(f"Question: {result['question']}")
            print(f"Suggestion: {result['suggestion']}")
            print(f"Severity: {result['severity']}")
        else:
            print("No interrupt triggered")
        
        print("-" * 50)

if __name__ == "__main__":
    print("Testing Enhanced Vibe Mentor")
    print("=" * 80)
    
    test_context_extraction()
    test_mentor_responses()
    test_interrupt_mode()
    
    # Cleanup
    cleanup_mentor_engine()
    print("\n✅ Tests completed!")