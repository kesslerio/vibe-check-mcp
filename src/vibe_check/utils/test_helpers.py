"""Test helper utilities for vibe check validation."""

def format_test_result(result: bool, message: str) -> str:
    """Format test result with status indicator.
    
    Args:
        result: Boolean test result
        message: Descriptive message about the test
        
    Returns:
        Formatted string with status indicator
    """
    status = "✅ PASS" if result else "❌ FAIL"
    return f"{status}: {message}"


def validate_pattern_detection(detected_patterns: list, expected_count: int) -> bool:
    """Validate that pattern detection found expected number of patterns.
    
    Args:
        detected_patterns: List of detected anti-patterns
        expected_count: Expected number of patterns to find
        
    Returns:
        True if counts match, False otherwise
    """
    return len(detected_patterns) == expected_count