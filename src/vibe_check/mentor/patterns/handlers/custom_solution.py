"""
Custom solution pattern handler.

Handles custom solution patterns and API client decisions,
promoting standard solutions over custom implementations.
"""

from typing import Tuple

from ...models.config import ConfidenceScores
from .base import PatternHandler


class CustomSolutionHandler(PatternHandler):
    """Handles custom solution patterns and API client decisions"""

    @staticmethod
    def get_senior_engineer_insight(topic: str) -> Tuple[str, str, float]:
        if PatternHandler.has_topic_keywords(
            topic, ["custom", "http", "client", "api"]
        ):
            return (
                "insight",
                "Building custom HTTP clients is rarely necessary and often a maintenance burden. "
                "Most services provide official SDKs that handle retry logic, authentication, rate limiting, "
                "and error handling. Let's check for an official solution first - it could save weeks of work.",
                ConfidenceScores.HIGH,
            )
        return (
            "suggestion",
            "For long-term maintainability, I suggest starting with the simplest solution that works. "
            "We can always add complexity later if truly needed. Focus on clear documentation, "
            "standard patterns, and making it easy for the next developer to understand.",
            ConfidenceScores.GOOD,
        )