"""
Session state progression tracking.

Handles advancing through different stages of collaborative reasoning
and managing stage-specific logic.
"""

from typing import Dict, List

from vibe_check.mentor.models.session import CollaborativeReasoningSession


class StateTracker:
    """Tracks and manages progression through reasoning stages"""

    # Stage progression mapping
    STAGE_PROGRESSION = {
        "problem-definition": "ideation",
        "ideation": "critique",
        "critique": "integration",
        "integration": "decision",
        "decision": "reflection",
        "reflection": "reflection",  # Terminal stage
    }

    # Suggested contribution types for each stage
    STAGE_SUGGESTIONS = {
        "problem-definition": ["observation", "question"],
        "ideation": ["suggestion", "insight"],
        "critique": ["concern", "challenge"],
        "integration": ["synthesis", "insight"],
        "decision": ["synthesis", "suggestion"],
        "reflection": ["observation", "insight"],
    }

    @staticmethod
    def advance_stage(session: CollaborativeReasoningSession) -> str:
        """Advance to the next stage in the reasoning process"""

        session.stage = StateTracker.STAGE_PROGRESSION.get(session.stage, "reflection")
        session.iteration += 1

        # Update suggested contribution types based on stage
        session.suggested_contribution_types = StateTracker.STAGE_SUGGESTIONS.get(
            session.stage, ["observation"]
        )

        return session.stage

    @staticmethod
    def is_terminal_stage(session: CollaborativeReasoningSession) -> bool:
        """Check if session is in a terminal stage"""
        return session.stage == "reflection"

    @staticmethod
    def get_stage_description(stage: str) -> str:
        """Get human-readable description of a stage"""
        descriptions = {
            "problem-definition": "Understanding the problem space",
            "ideation": "Generating potential solutions",
            "critique": "Evaluating and challenging proposals",
            "integration": "Synthesizing insights and perspectives",
            "decision": "Reaching consensus on approach",
            "reflection": "Final analysis and recommendations",
        }
        return descriptions.get(stage, "Unknown stage")

    @staticmethod
    def get_next_stage(current_stage: str) -> str:
        """Get the next stage without modifying session"""
        return StateTracker.STAGE_PROGRESSION.get(current_stage, "reflection")
