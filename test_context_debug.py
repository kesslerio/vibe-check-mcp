#!/usr/bin/env python3
"""Debug context extraction"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.tools.vibe_mentor_enhanced import ContextExtractor

query = "Building a RAG system with OpenAI embeddings and custom vector database"
context = "Need to search 100K documents for our knowledge base"

tech_context = ContextExtractor.extract_context(query, context)

print("Query:", query)
print("\nExtracted Context:")
print(f"Technologies: {tech_context.technologies}")
print(f"Frameworks: {tech_context.frameworks}")
print(f"Problem Type: {tech_context.problem_type}")
print(f"Features: {tech_context.specific_features}")
print(f"Patterns: {tech_context.patterns}")

# Check what the AI engineer logic would see
vector_techs = [t for t in tech_context.technologies if t in ['pinecone', 'weaviate', 'qdrant', 'vector', 'rag', 'openai', 'embedding']]
print(f"\nVector techs found: {vector_techs}")
print(f"'rag' in query.lower(): {'rag' in query.lower()}")