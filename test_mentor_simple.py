#!/usr/bin/env python3
"""Simple test of enhanced vibe mentor"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.vibe_mentor import get_mentor_engine
from vibe_check.tools.analyze_text_nollm import analyze_text_demo

def test_specific_advice():
    """Test that mentor gives specific technical advice"""
    
    queries = [
        {
            "query": "Should I build a custom HTTP client for Stripe payments?",
            "context": "We need payment processing for SaaS subscriptions"
        },
        {
            "query": "I'm implementing custom OAuth2 for Google authentication",
            "context": "NextJS app with 5000 users"
        },
        {
            "query": "Building a RAG system with custom vector database",
            "context": "Need to search 100K documents with OpenAI embeddings"
        }
    ]
    
    engine = get_mentor_engine()
    
    for q in queries:
        print(f"\n{'='*70}")
        print(f"Query: {q['query']}")
        
        # Run analysis
        combined = f"{q['query']}\n{q['context']}"
        analysis = analyze_text_demo(combined)
        patterns = analysis.get("patterns", [])
        detected = [p for p in patterns if p.get("detected")]
        
        # Create session
        session = engine.create_session(q['query'])
        
        # Get senior engineer response
        senior = session.personas[0]
        contribution = engine.generate_contribution(
            session=session,
            persona=senior,
            detected_patterns=detected,
            context=q['context']
        )
        
        print(f"\nSenior Engineer Response:")
        print(f"Type: {contribution.type}")
        print(f"Confidence: {contribution.confidence}")
        print(f"\nMessage:")
        print(contribution.content)
        
        # Check specificity
        content_lower = contribution.content.lower()
        specific_terms = {
            "stripe": ["stripe", "sdk", "payment", "webhook"],
            "oauth": ["oauth", "google", "auth0", "nextauth", "library"],
            "rag": ["rag", "vector", "pinecone", "weaviate", "langchain", "embeddings"]
        }
        
        found_specific = False
        for category, terms in specific_terms.items():
            if any(term in content_lower for term in terms):
                found_specific = True
                found_terms = [t for t in terms if t in content_lower]
                print(f"\n✅ Found specific terms: {found_terms}")
                break
        
        if not found_specific:
            print("\n⚠️  Response seems generic - no specific technology mentioned")

if __name__ == "__main__":
    print("Testing Enhanced Vibe Mentor - Specific Technical Advice")
    print("="*70)
    test_specific_advice()
    print("\n✅ Test completed!")