"""
Configuration constants and default values.

Contains confidence scores, experience strings, and other constants
used throughout the collaborative reasoning system.
"""

from typing import List

from .persona import PersonaData


# Configuration Constants
DEFAULT_MAX_SESSIONS = 50  # Maximum number of mentor sessions to keep in memory
SESSION_TIMESTAMP_FORMAT = (
    "mentor-session-{timestamp}-{token}"  # Format for session IDs
)
REFERENCE_DETECTION_WORD_COUNT = 5  # Number of words to check for reference detection


class ExperienceStrings:
    """Constants for experience descriptions in persona responses"""

    SENIOR_ENGINEER_YEARS = "15 years"
    PRODUCT_ENGINEER_FEATURES = "50+ features"


class ConfidenceScores:
    """Constants for confidence levels in persona responses"""

    VERY_HIGH = 0.92
    HIGH = 0.88
    GOOD = 0.85
    MODERATE = 0.82
    MEDIUM = 0.78  # Added for compatibility with response_strategies
    ACCEPTABLE = 0.70


# Default personas for the collaborative reasoning system
DEFAULT_PERSONAS: List[PersonaData] = [
    PersonaData(
        id="senior_engineer",
        name="Senior Software Engineer",
        expertise=[
            "Architecture",
            "Best practices",
            "Technical debt",
            "Maintainability",
        ],
        background=f"{ExperienceStrings.SENIOR_ENGINEER_YEARS} building scalable systems, seen countless anti-patterns",
        perspective="Maintainability and proven solutions over novel approaches",
        biases=[
            "Prefers established patterns",
            "Risk-averse",
            "Documentation-focused",
        ],
        communication={"style": "Direct", "tone": "Professional"},
    ),
    PersonaData(
        id="product_engineer",
        name="Product Engineer",
        expertise=[
            "MVP development",
            "User value",
            "Rapid iteration",
            "Feature delivery",
        ],
        background=f"Startup experience, shipped {ExperienceStrings.PRODUCT_ENGINEER_FEATURES} under tight deadlines",
        perspective="Ship fast, iterate based on feedback, perfect is the enemy of done",
        biases=["Favors speed over perfection", "User-focused", "Pragmatic"],
        communication={"style": "Pragmatic", "tone": "Energetic"},
    ),
    PersonaData(
        id="ai_engineer",
        name="AI/ML Engineer",
        expertise=[
            "AI integration",
            "Prompt engineering",
            "MCP tools",
            "LLM patterns",
        ],
        background="Deep learning research, extensive Claude and GPT integrations",
        perspective="Human-AI collaboration patterns, tool-augmented development",
        biases=[
            "Excited about AI capabilities",
            "Pattern-focused",
            "Tool-first thinking",
        ],
        communication={"style": "Analytical", "tone": "Precise"},
    ),
]
