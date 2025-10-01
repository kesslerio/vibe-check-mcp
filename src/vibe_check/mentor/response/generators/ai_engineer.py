"""
AI engineer persona response generator.

Generates responses from the AI engineer perspective,
focusing on modern tooling, AI integration, and tool-augmented development.
"""

from typing import Any, Dict, List, Optional, Tuple

from vibe_check.mentor.models.config import ConfidenceScores
from vibe_check.mentor.models.session import ContributionData
from vibe_check.mentor.patterns.handlers.ai_engineer import AIEngineerHandler
from .base_generator import BasePersonaGenerator


class AIEngineerGenerator(BasePersonaGenerator):
    """Generates AI engineer perspective responses"""
    
    def _get_base_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None,
        project_context: Optional[Any] = None
    ) -> Tuple[str, str, float]:
        """Get base response for AI engineer with project awareness"""
        # Synthesize if there are previous contributions
        if previous_contributions:
            return AIEngineerHandler.get_synthesis_response(previous_contributions)
        
        # Default to integration insight
        return AIEngineerHandler.get_integration_insight(topic or "")
    
    def _enhance_response_for_patterns(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        patterns: List[Dict[str, Any]],
        project_context: Optional[Any] = None
    ) -> Tuple[str, str, float]:
        """AI engineer doesn't have pattern-specific enhancements currently"""
        return base_response
    
    def _enhance_response_for_keywords(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        project_context: Optional[Any] = None
    ) -> Tuple[str, str, float]:
        """Enhance response based on topic keywords"""
        ai_keywords = ["integration", "ai", "mcp", "claude", "tool"]
        if self.has_topic_keywords(topic, ai_keywords):
            # For AI-related topics, use specialized integration insight
            return AIEngineerHandler.get_integration_insight(topic)
        
        return base_response