"""
Configuration management for collaborative reasoning.

This module provides centralized configuration, constants,
and template management for the mentor system.
"""

from .constants import (
    DEFAULT_MAX_SESSIONS,
    STAGE_PROGRESSION,
    STAGE_SUGGESTIONS,
    CONSENSUS_KEYWORDS,
    CONCERN_INDICATORS,
)

__all__ = [
    "DEFAULT_MAX_SESSIONS",
    "STAGE_PROGRESSION",
    "STAGE_SUGGESTIONS",
    "CONSENSUS_KEYWORDS",
    "CONCERN_INDICATORS",
]
