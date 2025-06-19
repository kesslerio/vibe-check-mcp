#!/usr/bin/env python3
"""Direct test of vibe mentor functionality"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the actual vibe_check_mentor function
import importlib
server_module = importlib.import_module('vibe_check.server')

# Find the vibe_check_mentor function
vibe_check_mentor = None
for name in dir(server_module):
    obj = getattr(server_module, name)
    if callable(obj) and name == 'vibe_check_mentor':
        # Get the original function before decoration
        if hasattr(obj, '__wrapped__'):
            vibe_check_mentor = obj.__wrapped__
        else:
            vibe_check_mentor = obj
        break

if not vibe_check_mentor:
    print("❌ Could not find vibe_check_mentor function")
    exit(1)

print("✅ Found vibe_check_mentor function")

# Test cases
test_cases = [
    {
        "name": "Stripe Integration",
        "query": "Should I build a custom HTTP client for Stripe?",
        "context": "Need to handle payments and subscriptions"
    },
    {
        "name": "Auth Decision",
        "query": "Building custom JWT auth for NextJS - good idea?",
        "context": "React/NextJS app with 1000 users"
    }
]

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"Test: {test['name']}")
    print(f"Query: {test['query']}")
    
    try:
        result = vibe_check_mentor(
            query=test['query'],
            context=test.get('context'),
            reasoning_depth="standard"
        )
        
        # Show senior engineer response
        perspectives = result.get("collaborative_insights", {}).get("perspectives", {})
        senior = perspectives.get("senior_engineer", {})
        
        print(f"\nSenior Engineer says:")
        print(senior.get("message", "No message")[:400])
        
        # Check if response is specific
        msg = senior.get("message", "").lower()
        if test['name'] == "Stripe Integration" and "stripe" in msg:
            print("\n✅ Response mentions Stripe specifically!")
        elif test['name'] == "Auth Decision" and any(auth in msg for auth in ["nextauth", "auth0", "clerk"]):
            print("\n✅ Response mentions specific auth libraries!")
        else:
            print("\n⚠️  Response seems generic")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n✅ Direct test completed!")