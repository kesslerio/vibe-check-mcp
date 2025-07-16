"""
Infrastructure pattern handler.

Handles infrastructure-without-implementation pattern responses
focusing on SDK-first approaches and proven solutions.
"""

from typing import Tuple

from ...models.config import ConfidenceScores, ExperienceStrings
from .base import PatternHandler


class InfrastructurePatternHandler(PatternHandler):
    """Handles infrastructure-without-implementation pattern responses"""

    @staticmethod
    def get_senior_engineer_response() -> Tuple[str, str, float]:
        return (
            "concern",
            f"This looks like infrastructure-first thinking. In my experience spanning {ExperienceStrings.SENIOR_ENGINEER_YEARS}, "
            "we should always start with working API calls before building abstractions. "
            "I strongly recommend following the official SDK examples first - they handle edge cases "
            "we'll inevitably miss in custom implementations.",
            ConfidenceScores.VERY_HIGH,
        )