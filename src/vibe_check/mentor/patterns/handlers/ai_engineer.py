"""
AI engineer pattern handler.

Handles AI engineer perspective responses focused on
modern tooling, AI integration, and tool-augmented development.
"""

from typing import List, Tuple

from vibe_check.mentor.models.config import ConfidenceScores
from vibe_check.mentor.models.session import ContributionData
from .base import PatternHandler


class AIEngineerHandler(PatternHandler):
    """Handles AI engineer perspective responses"""

    @staticmethod
    def get_integration_insight(topic: str) -> Tuple[str, str, float]:
        if PatternHandler.has_topic_keywords(topic, ["integration", "ai"]):
            return (
                "insight",
                "Modern AI services provide excellent SDKs that handle the complexity for us. "
                "For example, Claude's SDK manages streaming, tool use, context windows, and retry logic. "
                "Custom implementations often miss critical edge cases like token limits, rate limiting, "
                "and proper error handling that the official SDK handles elegantly.",
                ConfidenceScores.HIGH,
            )
        return (
            "suggestion",
            "Consider how AI tools can accelerate this work. MCP tools can provide immediate feedback, "
            "GitHub Copilot can generate boilerplate, and LLMs can help validate our approach. "
            "Why build from scratch when AI can help us prototype 10x faster?",
            ConfidenceScores.MODERATE,
        )

    @staticmethod
    def get_synthesis_response(
        previous_contributions: List[ContributionData],
    ) -> Tuple[str, str, float]:
        if previous_contributions:
            return (
                "synthesis",
                "Building on the previous points, I see a pattern here: we're considering building "
                "infrastructure before proving the basic functionality. Modern AI tools can accelerate "
                "our development - MCP tools, GitHub Copilot, and structured prompts can help generate "
                "boilerplate and catch anti-patterns early. Let's leverage these tools.",
                ConfidenceScores.GOOD,
            )
        return AIEngineerHandler.get_integration_insight("")
