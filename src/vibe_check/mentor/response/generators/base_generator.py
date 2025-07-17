"""
Base generator for persona response generation.

Provides common functionality for all persona generators to reduce duplication.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ...models.session import ContributionData
from ...patterns.base import PatternHandler


class BasePersonaGenerator(PatternHandler, ABC):
    """Base class for all persona response generators"""
    
    def generate_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        Generate a response from this persona.
        
        Args:
            topic: The topic being discussed
            patterns: Detected patterns from vibe check
            previous_contributions: Previous contributions in the session
            context: Additional context from the user
            
        Returns:
            Tuple of (contribution_type, content, confidence)
        """
        # Get base response from the persona-specific implementation
        base_response = self._get_base_response(topic, patterns, previous_contributions, context)
        
        # Check for pattern-specific enhancements
        enhanced_response = self._enhance_response_for_patterns(
            base_response, topic, patterns
        )
        
        # Check for keyword-specific enhancements
        final_response = self._enhance_response_for_keywords(
            enhanced_response, topic
        )
        
        return final_response
    
    @abstractmethod
    def _get_base_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Get the base response specific to this persona"""
        pass
    
    @abstractmethod
    def _enhance_response_for_patterns(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        patterns: List[Dict[str, Any]]
    ) -> Tuple[str, str, float]:
        """Enhance response based on detected patterns"""
        pass
    
    @abstractmethod
    def _enhance_response_for_keywords(
        self,
        base_response: Tuple[str, str, float],
        topic: str
    ) -> Tuple[str, str, float]:
        """Enhance response based on topic keywords"""
        pass
    
    def _enhance_content(
        self,
        base_response: Tuple[str, str, float],
        enhancement: str
    ) -> Tuple[str, str, float]:
        """
        Helper to enhance response content while preserving type and confidence.
        
        Args:
            base_response: Original response tuple
            enhancement: Text to append to the content
            
        Returns:
            Enhanced response tuple
        """
        contribution_type, content, confidence = base_response
        enhanced_content = f"{content} {enhancement}"
        return (contribution_type, enhanced_content, confidence)