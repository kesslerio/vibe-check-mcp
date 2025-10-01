"""
Custom solution pattern handler.

Handles custom solution patterns and API client decisions,
promoting standard solutions over custom implementations.
"""

import logging
from typing import Tuple

from vibe_check.mentor.models.config import ConfidenceScores

logger = logging.getLogger(__name__)
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

        # Enhanced: Check for specific technical decision patterns
        if PatternHandler.has_topic_keywords(
            topic,
            [
                "option",
                "approach",
                "choose",
                "decision",
                "vs",
                "or",
                "better",
                "should",
            ],
        ):
            # Extract options if present (e.g., "Option A", "Option B", etc.)
            import re

            try:
                # Validate and compile pattern safely
                pattern = re.compile(
                    r"option [a-c]|approach [a-c]|[a-c]\)", re.IGNORECASE
                )
                options_match = pattern.findall(topic.lower())
            except re.error as e:
                # Handle regex compilation error gracefully
                logger.warning(f"Regex pattern error in CustomSolutionHandler: {e}")
                options_match = []

            if options_match:
                return (
                    "insight",
                    f"Let me analyze the specific options you've presented. Each approach has trade-offs: "
                    f"Consider evaluating them against: 1) Implementation complexity, 2) Maintenance burden, "
                    f"3) Performance requirements, 4) Team expertise, 5) Future scalability needs. "
                    f"Based on the context you've provided, I'd need to understand the specific constraints "
                    f"and requirements to give targeted advice on which option best fits your use case.",
                    ConfidenceScores.GOOD,
                )

            return (
                "suggestion",
                f"For this technical decision, let's apply a structured approach: "
                f"1) Define clear success criteria, 2) List constraints (time, resources, skills), "
                f"3) Evaluate each option against these criteria, 4) Consider maintenance implications, "
                f"5) Start with a proof-of-concept for the most promising approach. "
                f"The best solution often emerges from practical experimentation rather than theoretical analysis.",
                ConfidenceScores.GOOD,
            )

        # Enhanced: Check for data/field related queries
        if PatternHandler.has_topic_keywords(
            topic,
            ["field", "data", "deduplicate", "duplicate", "merge", "combine", "filter"],
        ):
            return (
                "insight",
                f"For data field operations, consider these principles: "
                f"1) Preserve data integrity - never lose information without explicit user consent, "
                f"2) Make operations reversible when possible, 3) Log all transformations for debugging, "
                f"4) Validate data at boundaries, 5) Consider performance impacts on large datasets. "
                f"The specific approach depends on your data volume, quality requirements, and user expectations.",
                ConfidenceScores.GOOD,
            )

        # Enhanced: Check for architecture/design queries
        if PatternHandler.has_topic_keywords(
            topic,
            [
                "architecture",
                "design",
                "pattern",
                "structure",
                "system",
                "microservice",
                "monolith",
            ],
        ):
            return (
                "insight",
                f"For architectural decisions, start with the simplest approach that could work: "
                f"1) Begin with a modular monolith - easier to refactor than distributed systems, "
                f"2) Extract services only when you have clear boundaries and scaling needs, "
                f"3) Focus on clean interfaces between modules, 4) Invest in observability early, "
                f"5) Design for replaceability, not reusability. Most 'future-proof' architectures become technical debt.",
                ConfidenceScores.HIGH,
            )

        # Default response - but more contextual
        return (
            "suggestion",
            f"Looking at your specific question, I recommend starting with the simplest solution that addresses "
            f"your immediate needs. We can iterate based on real-world usage patterns. Focus on: "
            f"1) Clear interfaces, 2) Comprehensive tests, 3) Good documentation, "
            f"4) Making it easy to change later. The best code is code that's easy to delete when requirements change.",
            ConfidenceScores.GOOD,
        )
