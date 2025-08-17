"""
Validation module for vibe-check-mcp testing and benchmarking.

This module contains validation tools, pattern detection utilities,
and performance benchmarking code used for testing the core
anti-pattern detection engine.
"""

from .detect_patterns import PatternDetector
from .timing_utils import PerformanceTimer, timed_function

__all__ = [
    "PatternDetector", 
    "PerformanceTimer", 
    "timed_function"
]