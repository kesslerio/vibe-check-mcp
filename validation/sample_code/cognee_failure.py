"""
Real example: Cognee Integration Failure Case
This is the actual pattern that led to 2+ years of technical debt
"""

# Anti-pattern example that SHOULD be detected
example_issue_text = """
Title: Integrate Cognee for Vector Search

We need to integrate with Cognee for our vector search functionality.
I'm planning to build a custom HTTP client with proper error handling
and retry logic since their SDK might be limiting for our use case.

We'll implement our own vector processing pipeline to ensure we have
full control over the search operations. This will involve:

1. Custom HTTP client for API calls
2. Our own data preprocessing 
3. Custom vector similarity algorithms
4. Manual result ranking system

This approach gives us more flexibility than using their standard SDK.
"""

# What we SHOULD have done (simple standard approach)
correct_approach = """
Title: Integrate Cognee for Vector Search

After reviewing the official Cognee documentation, I'll implement
the standard integration approach:

1. Use cognee.add() to add documents
2. Use cognee.cognify() to process them  
3. Use cognee.search() for queries

The official examples show this handles our use case perfectly.
Let me start with a basic implementation to validate it works.
"""

# The actual failure outcome
failure_outcome = {
    "timeline": "2+ years",
    "functionality_delivered": "Zero working vector search",
    "technical_debt": "Massive custom infrastructure that doesn't work",
    "opportunity_cost": "Could have had working solution in 1 week",
    "lesson": "Test standard approach before building custom"
}