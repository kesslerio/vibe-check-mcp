"""
AI engineer persona response generator.

Generates responses from the AI engineer perspective,
focusing on modern tooling, AI integration, and tool-augmented development.
"""

from typing import Any, Dict, List, Optional, Tuple

from ...models.config import ConfidenceScores
from ...models.session import ContributionData
from ...patterns.handlers.ai_engineer import AIEngineerHandler


class AIEngineerGenerator:
    """Generates AI engineer perspective responses"""
    
    def generate_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Generate AI engineer perspective focused on modern tooling"""

        # Check for AI/integration topics first
        if self._has_topic_keywords(topic, ["integration", "ai"]):
            return AIEngineerHandler.get_integration_insight(topic)

        # Synthesize if there are previous contributions
        if previous_contributions:
            return AIEngineerHandler.get_synthesis_response(previous_contributions)

        # Default AI engineer suggestion
        return AIEngineerHandler.get_integration_insight("")
    
    def _has_topic_keywords(self, topic: str, keywords: List[str]) -> bool:
        """Check if topic contains any of the specified keywords"""
        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in keywords)