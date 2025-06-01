#!/usr/bin/env python3
"""
Comprehensive validation using sample code files
Tests detection algorithms against realistic examples
"""

import sys
from pathlib import Path
from detect_patterns import PatternDetector

def test_sample_files():
    """Test detection against sample code files"""
    detector = PatternDetector()
    
    # Test bad examples (should detect)
    print("Testing BAD examples (should detect patterns):")
    print("-" * 50)
    
    bad_examples_file = Path(__file__).parent / "sample_code" / "bad_examples.py"
    with open(bad_examples_file) as f:
        content = f.read()
    
    # Extract the example strings
    import re
    examples = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    
    bad_results = []
    for i, example in enumerate(examples[1:], 1):  # Skip docstring
        if "Title:" in example:
            result = detector.detect_infrastructure_without_implementation(example)
            should_detect = True
            passed = result["detected"] and result["confidence"] >= 0.5
            
            print(f"{i}. {'✅ PASS' if passed else '❌ FAIL'} - Confidence: {result['confidence']:.2f}")
            print(f"   Evidence: {result['evidence']}")
            bad_results.append(passed)
    
    print(f"\nBad examples: {sum(bad_results)}/{len(bad_results)} passed")
    
    # Test good examples (should NOT detect)
    print("\nTesting GOOD examples (should NOT detect patterns):")
    print("-" * 50)
    
    good_examples_file = Path(__file__).parent / "sample_code" / "good_examples.py"
    with open(good_examples_file) as f:
        content = f.read()
    
    examples = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    
    good_results = []
    for i, example in enumerate(examples[1:], 1):  # Skip docstring
        if "Title:" in example:
            result = detector.detect_infrastructure_without_implementation(example)
            should_not_detect = True
            passed = not result["detected"] and result["confidence"] < 0.4
            
            print(f"{i}. {'✅ PASS' if passed else '❌ FAIL'} - Confidence: {result['confidence']:.2f}")
            if result["evidence"]:
                print(f"   Evidence: {result['evidence']}")
            good_results.append(passed)
    
    print(f"\nGood examples: {sum(good_results)}/{len(good_results)} passed")
    
    # Overall summary
    total_passed = sum(bad_results) + sum(good_results)
    total_tests = len(bad_results) + len(good_results)
    accuracy = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 50)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("\n🎉 COMPREHENSIVE VALIDATION PASSED!")
        return True
    else:
        print("\n⚠️  COMPREHENSIVE VALIDATION FAILED")
        return False

if __name__ == "__main__":
    success = test_sample_files()
    sys.exit(0 if success else 1)