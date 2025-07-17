"""
Product engineer persona response generator.

Generates responses from the product engineer perspective,
focusing on user value, rapid delivery, and pragmatic solutions.
"""

from typing import Any, Dict, List, Optional, Tuple

from ...models.config import ConfidenceScores, ExperienceStrings
from ...models.session import ContributionData
from ...patterns.handlers.product_engineer import ProductEngineerHandler
from .base_generator import BasePersonaGenerator


class ProductEngineerGenerator(BasePersonaGenerator):
    """Generates product engineer perspective responses"""
    
    def _get_base_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Get base response for product engineer"""
        # Default to planning challenge response
        return ProductEngineerHandler.get_planning_challenge(topic)
    
    def _enhance_response_for_patterns(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        patterns: List[Dict[str, Any]]
    ) -> Tuple[str, str, float]:
        """Enhance response based on detected patterns"""
        # If any patterns detected, focus on rapid prototyping
        if patterns:
            rapid_response = ProductEngineerHandler.get_rapid_delivery_response()
            enhancement = f"For '{topic}', let's focus on what users actually need rather than what's technically interesting to build."
            return self._enhance_content(rapid_response, enhancement)
        
        return base_response
    
    def _enhance_response_for_keywords(
        self,
        base_response: Tuple[str, str, float],
        topic: str
    ) -> Tuple[str, str, float]:
        """Enhance response based on topic keywords"""
        build_keywords = ["build", "create", "implement"]
        if self.has_topic_keywords(topic, build_keywords):
            enhancement = f"Before building '{topic}', have we validated this solves a real user problem? I'd rather ship something imperfect that users love than something perfect they don't need."
            return self._enhance_content(base_response, enhancement)
        
        return base_response