#!/usr/bin/env python3
"""
Standalone pattern detection validation - NO infrastructure dependencies

This script validates our core anti-pattern detection algorithms BEFORE
building any server infrastructure. It directly addresses the Infrastructure-
Without-Implementation anti-pattern by proving detection works first.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from validation.timing_utils import PerformanceTimer


class PatternDetector:
    """Standalone anti-pattern detector for validation"""

    def __init__(self, patterns_file: str = None):
        if patterns_file is None:
            patterns_file = Path(__file__).parent.parent / "data" / "anti_patterns.json"

        with open(patterns_file) as f:
            pattern_data = json.load(f)

        # Extract version information if present
        self.schema_version = pattern_data.get("schema_version", "1.0.0")
        self.data_version = pattern_data.get("data_version", "1.0.0")

        # Extract pattern definitions (exclude version fields)
        self.patterns = {
            key: value
            for key, value in pattern_data.items()
            if key not in ["schema_version", "data_version"]
        }

    def get_version_info(self) -> Dict[str, str]:
        """Get version information for the pattern database"""
        return {
            "schema_version": self.schema_version,
            "data_version": self.data_version,
        }

    def detect_infrastructure_without_implementation(
        self, content: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        Detect infrastructure-without-implementation pattern

        This is our core detection method that must work before any framework.
        """
        pattern_config = self.patterns["infrastructure_without_implementation"]
        full_text = f"{content} {context}".lower()

        evidence = []
        confidence = 0.0

        # Check positive indicators
        for indicator in pattern_config["indicators"]:
            if re.search(indicator["regex"], full_text, re.IGNORECASE):
                evidence.append(indicator["description"])
                confidence += indicator["weight"]

        # Check negative indicators (reduce confidence if found)
        for neg_indicator in pattern_config.get("negative_indicators", []):
            if re.search(neg_indicator["regex"], full_text, re.IGNORECASE):
                confidence += neg_indicator["weight"]  # weight is negative

        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        detected = confidence >= pattern_config["detection_threshold"]

        return {
            "detected": detected,
            "confidence": confidence,
            "evidence": evidence,
            "pattern_type": "infrastructure_without_implementation",
            "pattern_version": pattern_config.get("version", "1.0.0"),
            "threshold": pattern_config["detection_threshold"],
        }

    def detect_all_patterns(
        self, content: str, context: str = ""
    ) -> List[Dict[str, Any]]:
        """Detect all anti-patterns in given content"""
        detected_patterns = []

        for pattern_id, pattern_config in self.patterns.items():
            result = self._detect_single_pattern(content, context, pattern_config)
            if result["detected"]:
                detected_patterns.append(result)

        return detected_patterns

    def _detect_single_pattern(
        self, content: str, context: str, pattern_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect a single pattern type"""
        full_text = f"{content} {context}".lower()
        evidence = []
        confidence = 0.0

        # Check positive indicators
        for indicator in pattern_config["indicators"]:
            if re.search(indicator["regex"], full_text, re.IGNORECASE):
                evidence.append(indicator["description"])
                confidence += indicator["weight"]

        # Check negative indicators
        for neg_indicator in pattern_config.get("negative_indicators", []):
            if re.search(neg_indicator["regex"], full_text, re.IGNORECASE):
                confidence += neg_indicator["weight"]

        confidence = max(0.0, min(1.0, confidence))
        detected = confidence >= pattern_config["detection_threshold"]

        return {
            "detected": detected,
            "confidence": confidence,
            "evidence": evidence,
            "pattern_type": pattern_config["id"],
            "pattern_version": pattern_config.get("version", "1.0.0"),
            "threshold": pattern_config["detection_threshold"],
        }


def validate_with_cognee_case() -> Dict[str, Any]:
    """
    Validate detection using the known Cognee failure case

    This MUST detect the pattern since it's a documented failure.
    """
    # Load the Cognee case study
    case_study_path = Path(__file__).parent.parent / "data" / "cognee_case_study.json"
    with open(case_study_path) as f:
        case_study = json.load(f)

    detector = PatternDetector()

    # Test with the example text from case study
    test_text = case_study["example_detection_text"]
    result = detector.detect_infrastructure_without_implementation(test_text)

    # Validate against expected results
    expected = case_study["expected_detection"]

    validation_passed = (
        result["detected"] == expected["should_detect"]
        and result["confidence"] >= expected["minimum_confidence"]
    )

    return {
        "test_name": "cognee_case_validation",
        "test_text": test_text,
        "expected_detection": expected["should_detect"],
        "actual_detection": result["detected"],
        "expected_min_confidence": expected["minimum_confidence"],
        "actual_confidence": result["confidence"],
        "evidence": result["evidence"],
        "validation_passed": validation_passed,
        "details": result,
    }


def validate_with_good_case() -> Dict[str, Any]:
    """
    Validate that good architectural decisions are NOT flagged

    This should have low confidence and NOT detect the pattern.
    """
    good_example = """
    We need to integrate with Stripe for payments.
    I've reviewed the official Stripe SDK documentation and it supports
    all our use cases. We'll use stripe.checkout.Session.create() 
    as recommended in their integration guide. The official examples
    show exactly how to handle our payment flow.
    """

    detector = PatternDetector()
    result = detector.detect_infrastructure_without_implementation(good_example)

    # This should NOT detect the pattern (good architecture)
    expected_detection = False
    validation_passed = (
        result["detected"] == expected_detection
        and result["confidence"] < 0.3  # Low confidence for good cases
    )

    return {
        "test_name": "good_case_validation",
        "test_text": good_example.strip(),
        "expected_detection": expected_detection,
        "actual_detection": result["detected"],
        "actual_confidence": result["confidence"],
        "evidence": result["evidence"],
        "validation_passed": validation_passed,
        "details": result,
    }


def validate_additional_cases() -> List[Dict[str, Any]]:
    """Validate with additional test cases"""
    test_cases = [
        {
            "name": "Custom HTTP client",
            "text": "Let's build our own HTTP client with retry logic instead of using the requests library",
            "should_detect": True,
            "min_confidence": 0.5,
        },
        {
            "name": "SDK research done",
            "text": "After testing the official SDK and reviewing the documentation, it meets our needs perfectly",
            "should_detect": False,
            "max_confidence": 0.3,
        },
        {
            "name": "Avoiding SDK without reason",
            "text": "We should avoid using their SDK and implement our own API wrapper for better control",
            "should_detect": True,
            "min_confidence": 0.6,
        },
        {
            "name": "Standard approach first",
            "text": "Let's start with the standard integration approach as shown in their documentation",
            "should_detect": False,
            "max_confidence": 0.2,
        },
        {
            "name": "Custom without research",
            "text": "I think we need to create our own custom integration since their SDK might not work",
            "should_detect": True,
            "min_confidence": 0.5,
        },
    ]

    detector = PatternDetector()
    results = []

    for case in test_cases:
        result = detector.detect_infrastructure_without_implementation(case["text"])

        if case["should_detect"]:
            validation_passed = (
                result["detected"] and result["confidence"] >= case["min_confidence"]
            )
        else:
            validation_passed = not result["detected"] and result[
                "confidence"
            ] <= case.get("max_confidence", 0.4)

        results.append(
            {
                "test_name": case["name"],
                "test_text": case["text"],
                "expected_detection": case["should_detect"],
                "actual_detection": result["detected"],
                "confidence": result["confidence"],
                "evidence": result["evidence"],
                "validation_passed": validation_passed,
            }
        )

    return results


def run_comprehensive_validation() -> Dict[str, Any]:
    """Run all validation tests and provide summary"""
    # Initialize performance timer
    timer = PerformanceTimer()
    timer.start_session()

    print("=" * 60)
    print("ANTI-PATTERN DETECTION VALIDATION")
    print("Testing core detection algorithms BEFORE building infrastructure")
    print("=" * 60)

    # Test 1: Cognee case (known failure)
    print("\n1. COGNEE CASE VALIDATION (Known Failure)")
    print("-" * 40)
    with timer.time_operation("cognee_case_validation"):
        cognee_result = validate_with_cognee_case()

    status = "✅ PASS" if cognee_result["validation_passed"] else "❌ FAIL"
    print(f"Status: {status}")
    print(f"Expected: {cognee_result['expected_detection']}")
    print(f"Actual: {cognee_result['actual_detection']}")
    print(
        f"Confidence: {cognee_result['actual_confidence']:.2f} (min: {cognee_result['expected_min_confidence']:.2f})"
    )
    print(f"Evidence: {cognee_result['evidence']}")

    # Test 2: Good case (should not detect)
    print("\n2. GOOD CASE VALIDATION (Should Not Detect)")
    print("-" * 40)
    with timer.time_operation("good_case_validation"):
        good_result = validate_with_good_case()

    status = "✅ PASS" if good_result["validation_passed"] else "❌ FAIL"
    print(f"Status: {status}")
    print(f"Expected: {good_result['expected_detection']}")
    print(f"Actual: {good_result['actual_detection']}")
    print(f"Confidence: {good_result['actual_confidence']:.2f}")
    print(f"Evidence: {good_result['evidence']}")

    # Test 3: Additional cases
    print("\n3. ADDITIONAL TEST CASES")
    print("-" * 40)
    with timer.time_operation("additional_test_cases"):
        additional_results = validate_additional_cases()

    passed_count = 0
    for i, result in enumerate(additional_results, 1):
        status = "✅ PASS" if result["validation_passed"] else "❌ FAIL"
        print(f"{i}. {result['test_name']}: {status}")
        print(
            f"   Confidence: {result['confidence']:.2f}, Detected: {result['actual_detection']}"
        )
        if result["validation_passed"]:
            passed_count += 1

    # Overall summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    total_tests = 2 + len(additional_results)  # Cognee + Good + Additional
    passed_tests = (
        (1 if cognee_result["validation_passed"] else 0)
        + (1 if good_result["validation_passed"] else 0)
        + passed_count
    )

    accuracy = (passed_tests / total_tests) * 100

    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Required: 80%+ for Phase 1 gate")

    overall_pass = accuracy >= 80.0
    if overall_pass:
        print("\n🎉 VALIDATION PASSED!")
        print("✅ Core detection algorithms validated")
        print("✅ Safe to proceed to Phase 1: Core Detection Engine")
    else:
        print("\n⚠️  VALIDATION FAILED")
        print("❌ Detection algorithms need refinement")
        print("❌ DO NOT proceed to Phase 1 until this passes")

    # End timing session and print performance summary
    total_time = timer.end_session()
    timer.print_summary(threshold=1.0, verbose=True)

    return {
        "overall_passed": overall_pass,
        "accuracy": accuracy,
        "tests_passed": passed_tests,
        "total_tests": total_tests,
        "cognee_result": cognee_result,
        "good_result": good_result,
        "additional_results": additional_results,
        "performance_summary": timer.get_summary(threshold=1.0),
        "total_execution_time": total_time,
    }


if __name__ == "__main__":
    validation_results = run_comprehensive_validation()

    # Exit with appropriate code
    exit(0 if validation_results["overall_passed"] else 1)
