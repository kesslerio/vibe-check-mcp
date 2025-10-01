"""
Base pattern handler class.

Provides common functionality for all pattern handlers in the
collaborative reasoning system.
"""

from typing import Any, Dict, List


class PatternHandler:
    """Base class for handling specific patterns in persona reasoning"""

    @staticmethod
    def has_pattern(patterns: List[Dict[str, Any]], pattern_type: str) -> bool:
        """Check if a specific pattern type exists in the patterns list"""
        try:
            return any(
                p.get("pattern_type") == pattern_type
                for p in patterns
                if isinstance(p, dict)
            )
        except (TypeError, AttributeError):
            return False

    @staticmethod
    def has_topic_keywords(topic: str, keywords: List[str]) -> bool:
        """Check if topic contains any of the specified keywords"""
        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in keywords)
