"""
Session and contribution data models.

Contains data structures for managing collaborative reasoning sessions
and individual contributions from personas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional

from .persona import PersonaData
from .responses import DisagreementData


@dataclass
class ContributionData:
    """Single contribution in collaborative reasoning"""

    persona_id: str
    content: str
    type: Literal[
        "observation",
        "question", 
        "insight",
        "concern",
        "suggestion",
        "challenge",
        "synthesis",
    ]
    confidence: float
    reference_ids: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CollaborativeReasoningSession:
    """Complete session state - inspired by Clear-Thought"""

    topic: str
    personas: List[PersonaData]
    contributions: List[ContributionData]
    stage: Literal[
        "problem-definition",
        "ideation", 
        "critique",
        "integration",
        "decision",
        "reflection",
    ]
    active_persona_id: str
    session_id: str
    iteration: int
    consensus_points: List[str] = field(default_factory=list)
    disagreements: List[DisagreementData] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    final_recommendation: Optional[str] = None
    next_contribution_needed: bool = True
    suggested_contribution_types: List[str] = field(default_factory=list)