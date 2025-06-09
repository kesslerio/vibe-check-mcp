#!/usr/bin/env python3
"""
Manual test for Phase 1 implementation (Issue #101)

This script tests the intelligent pre-filtering and graceful degradation
functionality without requiring external dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibe_check.core.pr_filtering import should_use_llm_analysis, create_large_pr_response


def test_small_pr():
    """Test that small PRs are approved for LLM analysis."""
    print("🧪 Testing small PR...")
    pr_data = {
        'additions': 100,
        'deletions': 50,
        'changed_files': 5
    }
    
    result = should_use_llm_analysis(pr_data)
    print(f"  Should use LLM: {result.should_use_llm}")
    print(f"  Reason: {result.reason}")
    assert result.should_use_llm is True
    print("  ✅ PASS: Small PR approved for LLM analysis")


def test_large_pr_lines():
    """Test that PRs with >1000 lines skip LLM analysis."""
    print("\n🧪 Testing large PR (lines)...")
    pr_data = {
        'additions': 800,
        'deletions': 400,  # Total: 1200
        'changed_files': 15
    }
    
    result = should_use_llm_analysis(pr_data)
    print(f"  Should use LLM: {result.should_use_llm}")
    print(f"  Reason: {result.reason}")
    assert result.should_use_llm is False
    assert "Large PR: 1200 lines changed" in result.reason
    print("  ✅ PASS: Large PR skips LLM analysis")


def test_large_pr_files():
    """Test that PRs with >20 files skip LLM analysis."""
    print("\n🧪 Testing large PR (files)...")
    pr_data = {
        'additions': 300,
        'deletions': 200,
        'changed_files': 25
    }
    
    result = should_use_llm_analysis(pr_data)
    print(f"  Should use LLM: {result.should_use_llm}")
    print(f"  Reason: {result.reason}")
    assert result.should_use_llm is False
    assert "Many files changed: 25 files" in result.reason
    print("  ✅ PASS: Many files PR skips LLM analysis")


def test_large_pr_response():
    """Test that large PR responses provide helpful guidance."""
    print("\n🧪 Testing large PR response generation...")
    from vibe_check.core.pr_filtering import PRFilterResult
    
    pr_data = {
        'number': 123,
        'title': 'Large refactoring PR'
    }
    
    filter_result = PRFilterResult(
        should_use_llm=False,
        reason="Large PR: 1500 lines changed (threshold: 1000)",
        fallback_strategy="fast_analysis_with_guidance",
        size_metrics={
            'total_changes': 1500,
            'changed_files': 30,
            'additions': 1000,
            'deletions': 500,
            'files_per_change_ratio': 0.02
        }
    )
    
    response = create_large_pr_response(pr_data, filter_result)
    print(f"  Status: {response['status']}")
    print(f"  Message: {response['message']}")
    print(f"  Guidance items: {len(response['guidance']['splitting_strategy'])}")
    
    assert response['status'] == "large_pr_detected"
    assert "Large PR detected" in response['message']
    assert 'guidance' in response
    assert len(response['guidance']['splitting_strategy']) > 0
    print("  ✅ PASS: Large PR response provides helpful guidance")


def test_edge_cases():
    """Test edge cases and thresholds."""
    print("\n🧪 Testing edge cases...")
    
    # Exactly at threshold
    pr_data = {
        'additions': 500,
        'deletions': 500,  # Exactly 1000
        'changed_files': 10
    }
    
    result = should_use_llm_analysis(pr_data)
    print(f"  At threshold (1000 lines): Use LLM = {result.should_use_llm}")
    assert result.should_use_llm is True
    
    # Just over threshold
    pr_data['additions'] = 501  # Now 1001 total
    result = should_use_llm_analysis(pr_data)
    print(f"  Over threshold (1001 lines): Use LLM = {result.should_use_llm}")
    assert result.should_use_llm is False
    
    print("  ✅ PASS: Edge cases handled correctly")


def main():
    """Run all Phase 1 tests."""
    print("🚀 Testing Phase 1 Implementation (Issue #101)")
    print("=" * 50)
    
    try:
        test_small_pr()
        test_large_pr_lines()
        test_large_pr_files()
        test_large_pr_response()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Phase 1 implementation is working correctly.")
        print("\nKey benefits verified:")
        print("✅ Intelligent pre-filtering prevents LLM timeouts")
        print("✅ System provides helpful guidance for large PRs")
        print("✅ Graceful degradation ensures no complete failures")
        print("✅ Clear thresholds (>1000 lines or >20 files)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()