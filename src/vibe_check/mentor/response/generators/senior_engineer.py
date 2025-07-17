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
from .base_generator import BasePersonaGenerator


class SeniorEngineerGenerator(BasePersonaGenerator):
    """Generates senior engineer perspective responses"""
    
    def _get_base_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Get base response for senior engineer"""
        # Default to custom solution handler
        return CustomSolutionHandler.get_senior_engineer_insight(topic)
    
    def _enhance_response_for_patterns(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        patterns: List[Dict[str, Any]]
    ) -> Tuple[str, str, float]:
        """Enhance response based on detected patterns"""
        # Check for infrastructure-without-implementation pattern
        if self.has_pattern(patterns, "infrastructure_without_implementation"):
            infra_response = InfrastructurePatternHandler.get_senior_engineer_response()
            enhancement = f"Specifically for '{topic}', I'd recommend checking if there's an official SDK or documented API that handles this use case."
            return self._enhance_content(infra_response, enhancement)
        
        return base_response
    
    def _enhance_response_for_keywords(
        self,
        base_response: Tuple[str, str, float],
        topic: str
    ) -> Tuple[str, str, float]:
        """Enhance response based on topic keywords"""
        integration_keywords = ["api", "integration", "service"]
        if self.has_topic_keywords(topic, integration_keywords):
            enhancement = f"For integrations like '{topic}', I always check the official documentation first - it often shows simpler approaches than what we initially consider."
            return self._enhance_content(base_response, enhancement)
        
        return base_response