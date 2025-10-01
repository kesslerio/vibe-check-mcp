"""
Response coordination for multi-persona reasoning.

Coordinates the generation of contributions from different personas
and manages the integration with pattern detection.
"""

import logging
from typing import Any, Dict, List, Optional

from vibe_check.mentor.models.config import REFERENCE_DETECTION_WORD_COUNT
from vibe_check.mentor.models.persona import PersonaData
from vibe_check.mentor.models.session import (
    CollaborativeReasoningSession,
    ContributionData,
)
from .generators.senior_engineer import SeniorEngineerGenerator
from .generators.product_engineer import ProductEngineerGenerator
from .generators.ai_engineer import AIEngineerGenerator

logger = logging.getLogger(__name__)


class ResponseCoordinator:
    """Coordinates response generation from multiple personas"""

    def __init__(self):
        try:
            self.generators = {
                "senior_engineer": SeniorEngineerGenerator(),
                "product_engineer": ProductEngineerGenerator(),
                "ai_engineer": AIEngineerGenerator(),
            }
        except Exception as e:
            logger.error(f"Failed to initialize response generators: {str(e)}")
            raise RuntimeError(
                f"Response coordinator initialization failed: {str(e)}"
            ) from e

    def generate_contribution(
        self,
        session: CollaborativeReasoningSession,
        persona: PersonaData,
        detected_patterns: List[Dict[str, Any]],
        context: Optional[str] = None,
        project_context: Optional[Any] = None,
        file_contexts: Optional[List[Any]] = None,
    ) -> ContributionData:
        """
        Generate a contribution from a persona based on their characteristics.
        This is our enhancement over Clear-Thought - actual reasoning generation.
        """

        # Input validation
        if not session:
            raise ValueError("Session cannot be None")

        if not persona:
            raise ValueError("Persona cannot be None")

        if detected_patterns is None:
            detected_patterns = []

        # Get the appropriate generator for this persona
        generator = self.generators.get(persona.id)
        if not generator:
            # Fallback for unknown personas
            return self._generate_fallback_contribution(
                persona, session.topic, detected_patterns
            )

        # Generate contribution using the specific persona generator with project context
        contribution_type, content, confidence = generator.generate_response(
            session.topic,
            detected_patterns,
            session.contributions,
            context,
            project_context,
        )

        contribution = ContributionData(
            persona_id=persona.id,
            content=content,
            type=contribution_type,
            confidence=confidence,
            reference_ids=self._find_references(content, session.contributions),
        )

        return contribution

    def _generate_fallback_contribution(
        self, persona: PersonaData, topic: str, patterns: List[Dict[str, Any]]
    ) -> ContributionData:
        """Generate a fallback contribution for unknown personas"""
        from ..models.config import ConfidenceScores

        return ContributionData(
            persona_id=persona.id,
            content=f"From my {persona.name} perspective with expertise in {', '.join(persona.expertise[:2])}, "
            f"this requires careful consideration of trade-offs.",
            type="observation",
            confidence=ConfidenceScores.ACCEPTABLE,
        )

    def _find_references(
        self, content: str, contributions: List[ContributionData]
    ) -> List[str]:
        """Find contributions that this content references"""
        references = []
        content_lower = content.lower()

        for contrib in contributions:
            # Simple reference detection based on keyword overlap
            if any(
                word in content_lower
                for word in contrib.content.lower().split()[
                    :REFERENCE_DETECTION_WORD_COUNT
                ]
            ):
                references.append(f"{contrib.persona_id}_{contrib.type}")

        return references
