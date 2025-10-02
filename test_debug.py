#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from vibe_check.tools.doom_loop_analysis import get_session_health_analysis, reset_session_tracking

    # Test no session case
    print("Testing no session case:")
    reset_session_tracking()
    result = get_session_health_analysis()
    print(f"Result: {result}")
    print(f"Status: {result.get('status')}")
    print()

    print("Testing active session case:")
    from vibe_check.tools.doom_loop_analysis import analyze_text_for_doom_loops
    analyze_text_for_doom_loops("Test content for session", tool_name="test")
    result = get_session_health_analysis()
    print(f"Result: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Has health_score: {'health_score' in result}")
    print(f"Has duration_minutes: {'duration_minutes' in result}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
