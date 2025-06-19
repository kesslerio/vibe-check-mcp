#!/usr/bin/env python3
"""Test all three personas for specific advice"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.vibe_mentor import get_mentor_engine
from vibe_check.tools.analyze_text_nollm import analyze_text_demo

def test_all_personas():
    """Test that all personas give specific advice"""
    
    query = "Building a RAG system with OpenAI embeddings and custom vector database"
    context = "Need to search 100K documents for our knowledge base"
    
    engine = get_mentor_engine()
    
    # Run analysis
    combined = f"{query}\n{context}"
    analysis = analyze_text_demo(combined)
    patterns = analysis.get("patterns", [])
    detected = [p for p in patterns if p.get("detected")]
    
    # Create session
    session = engine.create_session(query)
    
    print(f"Query: {query}")
    print(f"Context: {context}")
    print("="*70)
    
    # Get responses from all three personas
    for persona in session.personas:
        contribution = engine.generate_contribution(
            session=session,
            persona=persona,
            detected_patterns=detected,
            context=context
        )
        session.contributions.append(contribution)
        
        print(f"\n{persona.name} ({persona.id}):")
        print(f"Type: {contribution.type}")
        print(f"Confidence: {contribution.confidence}")
        print(f"\nMessage:")
        print(contribution.content)
        print("-"*70)
        
        # Check for specific terms
        content_lower = contribution.content.lower()
        rag_terms = ["rag", "vector", "pinecone", "weaviate", "langchain", "embeddings", "openai"]
        found = [t for t in rag_terms if t in content_lower]
        if found:
            print(f"✅ Found RAG-specific terms: {found}")
        else:
            print("⚠️  No RAG-specific terms found")

if __name__ == "__main__":
    print("Testing All Personas - RAG System Query")
    print("="*70)
    test_all_personas()
    print("\n✅ Test completed!")