"""
Constants and configuration values.

Centralized constants for the collaborative reasoning system,
including stage progression, keywords, and thresholds.
"""

from typing import Dict, List

# Session management
DEFAULT_MAX_SESSIONS = 50

# Stage progression
STAGE_PROGRESSION = {
    "problem-definition": "ideation",
    "ideation": "critique", 
    "critique": "integration",
    "integration": "decision",
    "decision": "reflection",
    "reflection": "reflection",  # Terminal stage
}

# Stage-specific contribution suggestions
STAGE_SUGGESTIONS = {
    "problem-definition": ["observation", "question"],
    "ideation": ["suggestion", "insight"],
    "critique": ["concern", "challenge"],
    "integration": ["synthesis", "insight"],
    "decision": ["synthesis", "suggestion"],
    "reflection": ["observation", "insight"],
}

# Consensus detection keywords
CONSENSUS_KEYWORDS = [
    "official",
    "sdk",
    "simple", 
    "prototype",
    "user",
    "feedback",
]

# Concern indicators for synthesis
CONCERN_INDICATORS = [
    "avoid",
    "concern",
    "risk", 
    "problem",
    "issue",
    "anti-pattern"
]

# Pattern severity mapping
PATTERN_SEVERITY_MAP = {
    "infrastructure_without_implementation": "high",
    "custom_solution_preferred": "medium", 
    "documentation_neglect": "medium",
    "complexity_escalation": "low",
}

# Default suggestions by pattern
PATTERN_SUGGESTIONS = {
    "infrastructure_without_implementation": "Check docs.api.com/sdks first",
    "custom_solution_preferred": "Try the standard approach",
    "documentation_neglect": "Review official documentation", 
    "complexity_escalation": "Consider YAGNI principle",
    "default": "Validate with simpler approach"
}

# Phase-specific intervention questions
PHASE_QUESTIONS = {
    "planning": {
        "infrastructure_without_implementation": 
            "Have you checked if an official SDK exists for this?",
        "custom_solution_preferred":
            "Would a simpler solution achieve the same user value?",
        "documentation_neglect":
            "Have you reviewed the official documentation first?",
        "complexity_escalation":
            "Is this complexity solving a real problem or a hypothetical one?",
        "default":
            "Have you validated this approach with the simplest possible solution?"
    },
    "implementation": {
        "infrastructure_without_implementation":
            "This abstraction adds complexity - is it solving a real problem?",
        "custom_solution_preferred":
            "Consider using the standard library function instead",
        "documentation_neglect":
            "The official docs show a simpler approach - have you tried it?",
        "complexity_escalation":
            "Could this be done with half the code?",
        "default":
            "Is there a more direct way to implement this?"
    },
    "review": {
        "infrastructure_without_implementation":
            "Does this match the original requirements?",
        "custom_solution_preferred":
            "What would happen if we removed this custom layer?",
        "documentation_neglect":
            "How does this compare to the documented approach?",
        "complexity_escalation":
            "Which parts of this could be simplified?",
        "default":
            "Have we introduced unnecessary complexity?"
    }
}