"""
Vibe Check Mentor - Modular collaborative reasoning system.

This package provides a refactored, modular implementation of the vibe mentor
system, breaking down the original monolithic vibe_mentor.py into focused modules.
"""

from .models.persona import PersonaData
from .models.session import CollaborativeReasoningSession, ContributionData
from .models.responses import DisagreementData
from .models.config import ConfidenceScores, ExperienceStrings

__all__ = [
    "PersonaData",
    "CollaborativeReasoningSession",
    "ContributionData",
    "DisagreementData",
    "ConfidenceScores",
    "ExperienceStrings",
]

# Backwards compatibility: inject deprecated modules into sys.modules
# so imports like "from vibe_check.mentor.mcp_sampling_patch import X" work
import sys
from . import deprecated

sys.modules["vibe_check.mentor.mcp_sampling_patch"] = deprecated.mcp_sampling_patch
sys.modules["vibe_check.mentor.mcp_sampling_secure"] = deprecated.mcp_sampling_secure
sys.modules["vibe_check.mentor.mcp_sampling_optimized"] = deprecated.mcp_sampling_optimized
sys.modules["vibe_check.mentor.mcp_sampling_ultrafast"] = deprecated.mcp_sampling_ultrafast
sys.modules["vibe_check.mentor.mcp_sampling_migration"] = deprecated.mcp_sampling_migration
