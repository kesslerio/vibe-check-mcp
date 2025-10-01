"""
Central registry for pattern handlers.

Provides a centralized way to map patterns to their appropriate handlers
and coordinate pattern-based response generation.
"""

from typing import Any, Dict, List

from .handlers.infrastructure import InfrastructurePatternHandler
from .handlers.custom_solution import CustomSolutionHandler
from .handlers.product_engineer import ProductEngineerHandler
from .handlers.ai_engineer import AIEngineerHandler


class PatternHandlerRegistry:
    """Central registry for pattern→response mapping"""

    def __init__(self):
        self.handlers = {
            "infrastructure_without_implementation": InfrastructurePatternHandler,
            "custom_solution_preferred": CustomSolutionHandler,
            "product_engineer": ProductEngineerHandler,
            "ai_engineer": AIEngineerHandler,
        }

    def get_handler(self, pattern_type: str):
        """Get the appropriate handler for a pattern type"""
        return self.handlers.get(pattern_type)

    def has_pattern(self, patterns: List[Dict[str, Any]], pattern_type: str) -> bool:
        """Check if a specific pattern type exists in the patterns list"""
        try:
            return any(
                p.get("pattern_type") == pattern_type
                for p in patterns
                if isinstance(p, dict)
            )
        except (TypeError, AttributeError):
            return False

    def get_applicable_handlers(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Get list of pattern types that have applicable handlers"""
        applicable = []
        for pattern in patterns:
            if isinstance(pattern, dict):
                pattern_type = pattern.get("pattern_type")
                if pattern_type and pattern_type in self.handlers:
                    applicable.append(pattern_type)
        return applicable
