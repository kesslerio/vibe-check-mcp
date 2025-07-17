"""
Product engineer pattern handler.

Handles product engineer perspective responses focused on
user value, rapid delivery, and pragmatic solutions.
"""

from typing import Tuple

from ...models.config import ConfidenceScores, ExperienceStrings
from .base import PatternHandler


class ProductEngineerHandler(PatternHandler):
    """Handles product engineer perspective responses"""

    @staticmethod
    def get_rapid_delivery_response() -> Tuple[str, str, float]:
        return (
            "suggestion",
            "Let's not overthink this! What's the fastest way to deliver value to users? "
            "I'd build a quick prototype with the official tools, get it in front of users this week, "
            "and iterate based on real feedback. Remember, users don't care about our architecture - "
            "they care about solving their problems.",
            ConfidenceScores.VERY_HIGH,
        )

    @staticmethod
    def get_planning_challenge(topic: str) -> Tuple[str, str, float]:
        if PatternHandler.has_topic_keywords(topic, ["planning", "architecture"]):
            return (
                "challenge",
                "Are we solving a real user problem or just satisfying our engineering desires? "
                f"I've shipped {ExperienceStrings.PRODUCT_ENGINEER_FEATURES}, and the ones that succeed focus on user value, not technical elegance. "
                "Can we validate this with users before investing heavily in the implementation?",
                ConfidenceScores.HIGH,
            )
        return (
            "observation",
            "This sounds good from a product perspective! Can we ship something basic this week and iterate? "
            "In my startup experience, the first version is never perfect - but it teaches us what users actually need.",
            ConfidenceScores.GOOD,
        )