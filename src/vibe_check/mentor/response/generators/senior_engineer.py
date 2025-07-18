"""
Senior engineer persona response generator.

Generates responses from the senior engineer perspective,
focusing on maintainability, best practices, and proven solutions.
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from ...models.config import ConfidenceScores, ExperienceStrings
from ...models.session import ContributionData
from ...patterns.handlers.infrastructure import InfrastructurePatternHandler
from ...patterns.handlers.custom_solution import CustomSolutionHandler
from .base_generator import BasePersonaGenerator

if TYPE_CHECKING:
    from ....tools.contextual_documentation import AnalysisContext


class SeniorEngineerGenerator(BasePersonaGenerator):
    """Generates senior engineer perspective responses"""
    
    def _get_base_response(
        self,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List[ContributionData],
        context: Optional[str] = None,
        project_context: Optional[Any] = None
    ) -> Tuple[str, str, float]:
        """Get base response for senior engineer with project context awareness"""
        # Check if we have project context and detected libraries
        from ....tools.contextual_documentation import AnalysisContext
        if isinstance(project_context, AnalysisContext):
            detected_libraries = list(project_context.library_docs.keys())
            if detected_libraries:
                # Provide library-aware advice
                lib_context = f"I see you're working with {', '.join(detected_libraries[:3])}."
                base_response = CustomSolutionHandler.get_senior_engineer_insight(topic)
                contribution_type, content, confidence = base_response
                enhanced_content = f"{lib_context} {content}"
                return (contribution_type, enhanced_content, confidence)
        
        # Default to custom solution handler
        return CustomSolutionHandler.get_senior_engineer_insight(topic)
    
    def _enhance_response_for_patterns(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        patterns: List[Dict[str, Any]],
        project_context: Optional[Any] = None
    ) -> Tuple[str, str, float]:
        """Enhance response based on detected patterns and project context"""
        # Check for infrastructure-without-implementation pattern
        if self.has_pattern(patterns, "infrastructure_without_implementation"):
            infra_response = InfrastructurePatternHandler.get_senior_engineer_response()
            
            # Add library-specific guidance if available
            enhancement = f"Specifically for '{topic}', I'd recommend checking if there's an official SDK or documented API that handles this use case."
            
            from ....tools.contextual_documentation import AnalysisContext
            if isinstance(project_context, AnalysisContext):
                detected_libraries = list(project_context.library_docs.keys())
                if detected_libraries:
                    enhancement += f" Given your use of {', '.join(detected_libraries[:2])}, there might be existing integrations or official libraries."
            
            return self._enhance_content(infra_response, enhancement)
        
        return base_response
    
    def _enhance_response_for_keywords(
        self,
        base_response: Tuple[str, str, float],
        topic: str,
        project_context: Optional[Any] = None
    ) -> Tuple[str, str, float]:
        """Enhance response based on topic keywords and project context"""
        integration_keywords = ["api", "integration", "service"]
        if self.has_topic_keywords(topic, integration_keywords):
            enhancement = f"For integrations like '{topic}', I always check the official documentation first - it often shows simpler approaches than what we initially consider."
            
            # Add project-specific advice if context available
            from ....tools.contextual_documentation import AnalysisContext
            if isinstance(project_context, AnalysisContext):
                conventions = project_context.project_conventions
                if conventions.get('technology_stack'):
                    enhancement += f" In your tech stack ({', '.join(conventions['technology_stack'][:2])}), there are likely established patterns."
            
            return self._enhance_content(base_response, enhancement)
        
        return base_response