"""
Senior engineer persona response generator.

Generates responses from the senior engineer perspective,
focusing on maintainability, best practices, and proven solutions.
"""

from typing import Any, Dict, List, Optional, Tuple

from ...models.config import ConfidenceScores, ExperienceStrings
from ...models.session import ContributionData
from ...patterns.handlers.infrastructure import InfrastructurePatternHandler
from ...patterns.handlers.custom_solution import CustomSolutionHandler


class SeniorEngineerGenerator:
    """Generates senior engineer perspective responses"""
    
    def generate_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Generate senior engineer perspective based on patterns and topic"""

        # Check for infrastructure-without-implementation pattern
        if self._has_pattern(patterns, "infrastructure_without_implementation"):
            base_response = InfrastructurePatternHandler.get_senior_engineer_response()
            # Enhance with topic-specific context
            enhanced_content = f"{base_response[1]} Specifically for '{topic}', I'd recommend checking if there's an official SDK or documented API that handles this use case."
            return (base_response[0], enhanced_content, base_response[2])

        # Handle custom solution patterns with topic context
        base_response = CustomSolutionHandler.get_senior_engineer_insight(topic)
        # Add specific technical concerns based on topic keywords
        if any(keyword in topic.lower() for keyword in ["api", "integration", "service"]):
            enhanced_content = f"{base_response[1]} For integrations like '{topic}', I always check the official documentation first - it often shows simpler approaches than what we initially consider."
            return (base_response[0], enhanced_content, base_response[2])
        
        return base_response
    
    def _has_pattern(self, patterns: List[Dict[str, Any]], pattern_type: str) -> bool:
        """Check if a specific pattern type exists in the patterns list"""
        try:
            return any(p.get("pattern_type") == pattern_type for p in patterns if isinstance(p, dict))
        except (TypeError, AttributeError):
            return False