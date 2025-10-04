"""Unified VibeLevel enum shared across mentor components."""

from enum import Enum


class VibeLevel(str, Enum):
    """High-level vibe assessment outcomes for mentoring flows."""

    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    CONCERNING = "concerning"
    PROBLEMATIC = "problematic"
    RESOLVED = "resolved"
    RES = "resolved"  # Backwards-compatible alias
    GOOD_VIBES = "good_vibes"
    NEEDS_RESEARCH = "research_needed"
    RESEARCH_NEEDED = "research_needed"
    NEEDS_POC = "needs_poc"
    COMPLEX_VIBES = "complex_vibes"
    BAD_VIBES = "bad_vibes"


__all__ = ["VibeLevel"]
