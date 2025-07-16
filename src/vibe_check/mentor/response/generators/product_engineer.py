"""
Product engineer persona response generator.

Generates responses from the product engineer perspective,
focusing on user value, rapid delivery, and pragmatic solutions.
"""

from typing import Any, Dict, List, Optional, Tuple

from ...models.config import ConfidenceScores, ExperienceStrings
from ...models.session import ContributionData
from ...patterns.handlers.product_engineer import ProductEngineerHandler


class ProductEngineerGenerator:
    """Generates product engineer perspective responses"""
    
    def generate_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Generate product engineer perspective focused on rapid delivery"""

        # If patterns detected, focus on rapid prototyping with topic context
        if patterns:
            base_response = ProductEngineerHandler.get_rapid_delivery_response()
            # Add topic-specific user value consideration
            enhanced_content = f"{base_response[1]} For '{topic}', let's focus on what users actually need rather than what's technically interesting to build."
            return (base_response[0], enhanced_content, base_response[2])

        # Otherwise, handle based on topic with specific context
        base_response = ProductEngineerHandler.get_planning_challenge(topic)
        # Add product-specific concerns based on topic
        if any(keyword in topic.lower() for keyword in ["build", "create", "implement"]):
            enhanced_content = f"{base_response[1]} Before building '{topic}', have we validated this solves a real user problem? I'd rather ship something imperfect that users love than something perfect they don't need."
            return (base_response[0], enhanced_content, base_response[2])
        
        return base_response