"""
Vibe Check Mentor - Collaborative Reasoning Tool

Combines vibe-check pattern detection with collaborative reasoning to provide
senior engineer feedback through multiple engineering perspectives.

Inspired by Clear-Thought's collaborative reasoning patterns with native implementation
for vibe-check educational coaching.
"""

from typing import Dict, Any, List, Optional, Literal, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import secrets
from datetime import datetime

from ..core.vibe_coaching import VibeCoachingFramework, CoachingTone
from ..core.pattern_detector import PatternDetector
from ..tools.analyze_text_nollm import analyze_text_demo

logger = logging.getLogger(__name__)


# Confidence score constants
class ConfidenceScores:
    """Constants for confidence levels in persona responses"""

    VERY_HIGH = 0.92
    HIGH = 0.88
    GOOD = 0.85
    MODERATE = 0.82
    ACCEPTABLE = 0.70


class PatternHandler:
    """Base class for handling specific patterns in persona reasoning"""

    @staticmethod
    def has_pattern(patterns: List[Dict[str, Any]], pattern_type: str) -> bool:
        """Check if a specific pattern type exists in the patterns list"""
        try:
            return any(p.get("pattern_type") == pattern_type for p in patterns)
        except (TypeError, AttributeError):
            return False

    @staticmethod
    def has_topic_keywords(topic: str, keywords: List[str]) -> bool:
        """Check if topic contains any of the specified keywords"""
        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in keywords)


class InfrastructurePatternHandler(PatternHandler):
    """Handles infrastructure-without-implementation pattern responses"""

    @staticmethod
    def get_senior_engineer_response() -> tuple[str, str, float]:
        return (
            "concern",
            "This looks like infrastructure-first thinking. In my experience spanning 15 years, "
            "we should always start with working API calls before building abstractions. "
            "I strongly recommend following the official SDK examples first - they handle edge cases "
            "we'll inevitably miss in custom implementations.",
            ConfidenceScores.VERY_HIGH,
        )


class CustomSolutionHandler(PatternHandler):
    """Handles custom solution patterns and API client decisions"""

    @staticmethod
    def get_senior_engineer_insight(topic: str) -> tuple[str, str, float]:
        if PatternHandler.has_topic_keywords(
            topic, ["custom", "http", "client", "api"]
        ):
            return (
                "insight",
                "Building custom HTTP clients is rarely necessary and often a maintenance burden. "
                "Most services provide official SDKs that handle retry logic, authentication, rate limiting, "
                "and error handling. Let's check for an official solution first - it could save weeks of work.",
                ConfidenceScores.HIGH,
            )
        return (
            "suggestion",
            "For long-term maintainability, I suggest starting with the simplest solution that works. "
            "We can always add complexity later if truly needed. Focus on clear documentation, "
            "standard patterns, and making it easy for the next developer to understand.",
            ConfidenceScores.GOOD,
        )


class ProductEngineerHandler(PatternHandler):
    """Handles product engineer perspective responses"""

    @staticmethod
    def get_rapid_delivery_response() -> tuple[str, str, float]:
        return (
            "suggestion",
            "Let's not overthink this! What's the fastest way to deliver value to users? "
            "I'd build a quick prototype with the official tools, get it in front of users this week, "
            "and iterate based on real feedback. Remember, users don't care about our architecture - "
            "they care about solving their problems.",
            ConfidenceScores.VERY_HIGH,
        )

    @staticmethod
    def get_planning_challenge(topic: str) -> tuple[str, str, float]:
        if PatternHandler.has_topic_keywords(topic, ["planning", "architecture"]):
            return (
                "challenge",
                "Are we solving a real user problem or just satisfying our engineering desires? "
                "I've shipped 50+ features, and the ones that succeed focus on user value, not technical elegance. "
                "Can we validate this with users before investing heavily in the implementation?",
                ConfidenceScores.HIGH,
            )
        return (
            "observation",
            "This sounds good from a product perspective! Can we ship something basic this week and iterate? "
            "In my startup experience, the first version is never perfect - but it teaches us what users actually need.",
            ConfidenceScores.GOOD,
        )


class AIEngineerHandler(PatternHandler):
    """Handles AI engineer perspective responses"""

    @staticmethod
    def get_integration_insight(topic: str) -> tuple[str, str, float]:
        if PatternHandler.has_topic_keywords(topic, ["integration", "ai"]):
            return (
                "insight",
                "Modern AI services provide excellent SDKs that handle the complexity for us. "
                "For example, Claude's SDK manages streaming, tool use, context windows, and retry logic. "
                "Custom implementations often miss critical edge cases like token limits, rate limiting, "
                "and proper error handling that the official SDK handles elegantly.",
                ConfidenceScores.HIGH,
            )
        return (
            "suggestion",
            "Consider how AI tools can accelerate this work. MCP tools can provide immediate feedback, "
            "GitHub Copilot can generate boilerplate, and LLMs can help validate our approach. "
            "Why build from scratch when AI can help us prototype 10x faster?",
            ConfidenceScores.MODERATE,
        )

    @staticmethod
    def get_synthesis_response(
        previous_contributions: List["ContributionData"],
    ) -> tuple[str, str, float]:
        if previous_contributions:
            return (
                "synthesis",
                "Building on the previous points, I see a pattern here: we're considering building "
                "infrastructure before proving the basic functionality. Modern AI tools can accelerate "
                "our development - MCP tools, GitHub Copilot, and structured prompts can help generate "
                "boilerplate and catch anti-patterns early. Let's leverage these tools.",
                ConfidenceScores.GOOD,
            )
        return AIEngineerHandler.get_integration_insight("")


# Borrowing Clear-Thought's data structures (adapted to Python)
@dataclass
class PersonaData:
    """Engineering persona definition - borrowed from Clear-Thought"""

    id: str
    name: str
    expertise: List[str]
    background: str
    perspective: str
    biases: List[str]
    communication: Dict[str, str]  # {"style": "...", "tone": "..."}


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
class DisagreementData:
    """Structured disagreement between personas"""

    topic: str
    positions: List[
        Dict[str, Any]
    ]  # [{"personaId": "...", "position": "...", "arguments": [...]}]


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


class VibeMentorEngine:
    """
    Native collaborative reasoning engine for vibe-check mentor.
    Combines Clear-Thought's data structures with vibe-check pattern detection.
    """

    # Engineering personas adapted for vibe-check context
    DEFAULT_PERSONAS = [
        PersonaData(
            id="senior_engineer",
            name="Senior Software Engineer",
            expertise=[
                "Architecture",
                "Best practices",
                "Technical debt",
                "Maintainability",
            ],
            background="15 years building scalable systems, seen countless anti-patterns",
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
            background="Startup experience, shipped 50+ features under tight deadlines",
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

    def __init__(self):
        self.sessions: Dict[str, CollaborativeReasoningSession] = {}
        self.pattern_detector = PatternDetector()

    def create_session(
        self,
        topic: str,
        personas: Optional[List[PersonaData]] = None,
        session_id: Optional[str] = None,
    ) -> CollaborativeReasoningSession:
        """Initialize a new collaborative reasoning session"""

        session_id = session_id or f"mentor-session-{secrets.token_hex(8)}"

        session = CollaborativeReasoningSession(
            topic=topic,
            personas=personas or self.DEFAULT_PERSONAS,
            contributions=[],
            stage="problem-definition",
            active_persona_id=self.DEFAULT_PERSONAS[0].id,
            session_id=session_id,
            iteration=0,
            suggested_contribution_types=["observation", "question"],
        )

        self.sessions[session_id] = session
        return session

    def generate_contribution(
        self,
        session: CollaborativeReasoningSession,
        persona: PersonaData,
        detected_patterns: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> ContributionData:
        """
        Generate a contribution from a persona based on their characteristics.
        This is our enhancement over Clear-Thought - actual reasoning generation.
        """

        # Analyze context for persona-specific insights
        contribution_type, content, confidence = self._reason_as_persona(
            persona, session.topic, detected_patterns, session.contributions, context
        )

        contribution = ContributionData(
            persona_id=persona.id,
            content=content,
            type=contribution_type,
            confidence=confidence,
            reference_ids=self._find_references(content, session.contributions),
        )

        return contribution

    def _reason_as_persona(
        self,
        persona: PersonaData,
        topic: str,
        patterns: List[Dict[str, Any]],
        previous_contributions: List["ContributionData"],
        context: Optional[str],
    ) -> tuple[str, str, float]:
        """
        Simulate persona reasoning based on their expertise and biases.
        Returns: (contribution_type, content, confidence)
        """

        if persona.id == "senior_engineer":
            return self._reason_as_senior_engineer(patterns, topic)
        elif persona.id == "product_engineer":
            return self._reason_as_product_engineer(patterns, topic)
        elif persona.id == "ai_engineer":
            return self._reason_as_ai_engineer(patterns, topic, previous_contributions)

        # Default response for unknown personas
        return (
            "observation",
            f"From my {persona.name} perspective with expertise in {', '.join(persona.expertise[:2])}, "
            f"this requires careful consideration of trade-offs.",
            ConfidenceScores.ACCEPTABLE,
        )

    def _reason_as_senior_engineer(
        self, patterns: List[Dict[str, Any]], topic: str
    ) -> tuple[str, str, float]:
        """Generate senior engineer perspective based on patterns and topic"""

        # Check for infrastructure-without-implementation pattern
        if InfrastructurePatternHandler.has_pattern(
            patterns, "infrastructure_without_implementation"
        ):
            return InfrastructurePatternHandler.get_senior_engineer_response()

        # Handle custom solution patterns
        return CustomSolutionHandler.get_senior_engineer_insight(topic)

    def _reason_as_product_engineer(
        self, patterns: List[Dict[str, Any]], topic: str
    ) -> tuple[str, str, float]:
        """Generate product engineer perspective focused on rapid delivery"""

        # If patterns detected, focus on rapid prototyping
        if patterns:
            return ProductEngineerHandler.get_rapid_delivery_response()

        # Otherwise, handle based on topic
        return ProductEngineerHandler.get_planning_challenge(topic)

    def _reason_as_ai_engineer(
        self,
        patterns: List[Dict[str, Any]],
        topic: str,
        previous_contributions: List["ContributionData"],
    ) -> tuple[str, str, float]:
        """Generate AI engineer perspective focused on modern tooling"""

        # Check for AI/integration topics first
        if PatternHandler.has_topic_keywords(topic, ["integration", "ai"]):
            return AIEngineerHandler.get_integration_insight(topic)

        # Synthesize if there are previous contributions
        if previous_contributions:
            return AIEngineerHandler.get_synthesis_response(previous_contributions)

        # Default AI engineer suggestion
        return AIEngineerHandler.get_integration_insight("")

    def advance_stage(self, session: CollaborativeReasoningSession) -> str:
        """Advance to the next stage in the reasoning process"""

        stage_progression = {
            "problem-definition": "ideation",
            "ideation": "critique",
            "critique": "integration",
            "integration": "decision",
            "decision": "reflection",
            "reflection": "reflection",  # Terminal stage
        }

        session.stage = stage_progression.get(session.stage, "reflection")
        session.iteration += 1

        # Update suggested contribution types based on stage
        stage_suggestions = {
            "problem-definition": ["observation", "question"],
            "ideation": ["suggestion", "insight"],
            "critique": ["concern", "challenge"],
            "integration": ["synthesis", "insight"],
            "decision": ["synthesis", "suggestion"],
            "reflection": ["observation", "insight"],
        }

        session.suggested_contribution_types = stage_suggestions.get(
            session.stage, ["observation"]
        )

        return session.stage

    def synthesize_session(
        self, session: CollaborativeReasoningSession
    ) -> Dict[str, Any]:
        """
        Synthesize the collaborative reasoning session into actionable insights.
        This is our key value-add over Clear-Thought's simple state tracking.
        """

        # Group contributions by type
        contributions_by_type = {}
        for contrib in session.contributions:
            if contrib.type not in contributions_by_type:
                contributions_by_type[contrib.type] = []
            contributions_by_type[contrib.type].append(contrib)

        # Extract consensus points (similar content from multiple personas)
        consensus = []
        all_content = [c.content.lower() for c in session.contributions]

        # Simple consensus detection based on keyword overlap
        consensus_keywords = [
            "official",
            "sdk",
            "simple",
            "prototype",
            "user",
            "feedback",
        ]
        for keyword in consensus_keywords:
            if sum(1 for content in all_content if keyword in content) >= 2:
                consensus.append(f"Use {keyword} approaches when available")

        # Identify key insights (high confidence insights and syntheses)
        key_insights = []
        for contrib in session.contributions:
            if contrib.type in ["insight", "synthesis"] and contrib.confidence > 0.85:
                key_insights.append(contrib.content)

        # Find disagreements
        disagreements = []
        concerns = contributions_by_type.get("concern", [])
        challenges = contributions_by_type.get("challenge", [])

        if concerns or challenges:
            for item in concerns + challenges:
                # Check if there's a counter-position
                disagreements.append(
                    {
                        "topic": "Implementation approach",
                        "positions": [
                            {
                                "personaId": item.persona_id,
                                "position": item.content,
                                "arguments": [item.content],
                            }
                        ],
                    }
                )

        # Generate final recommendation
        if session.stage in ["decision", "reflection"]:
            # Prioritize synthesis contributions
            syntheses = contributions_by_type.get("synthesis", [])
            if syntheses:
                final_rec = syntheses[-1].content
            else:
                final_rec = "Based on the discussion, start with the simplest official solution and iterate."
            session.final_recommendation = final_rec

        # Build comprehensive summary
        return {
            "session_summary": {
                "topic": session.topic,
                "stage": session.stage,
                "iterations": session.iteration,
                "total_contributions": len(session.contributions),
            },
            "consensus_points": consensus,
            "key_insights": key_insights[:3],  # Top 3
            "primary_concerns": [c.content for c in concerns[:2]],
            "disagreements": disagreements,
            "recommendations": {
                "immediate_actions": [
                    "Research official SDK/documentation",
                    "Create minimal proof of concept",
                    "Validate with real data",
                    "Get early user feedback",
                ],
                "avoid": [
                    "Building custom infrastructure first",
                    "Over-engineering the solution",
                    "Skipping official documentation",
                    "Making assumptions without validation",
                ],
            },
            "final_recommendation": session.final_recommendation,
        }

    def format_session_output(self, session: CollaborativeReasoningSession) -> str:
        """
        Format session for display - inspired by Clear-Thought's chalk formatting.
        Using ANSI codes for terminal colors.
        """

        BLUE = "\033[34m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        output = f"\n{BOLD}{BLUE}🧠 Collaborative Reasoning Session{RESET}\n"
        output += f"{BOLD}{GREEN}Topic:{RESET} {session.topic}\n"
        output += f"{BOLD}{YELLOW}Stage:{RESET} {session.stage} (Iteration: {session.iteration})\n"

        # Active persona
        active_persona = next(
            (p for p in session.personas if p.id == session.active_persona_id), None
        )
        if active_persona:
            output += f"\n{BOLD}{MAGENTA}Active Persona:{RESET} {active_persona.name}\n"
            output += (
                f"{BOLD}{CYAN}Expertise:{RESET} {', '.join(active_persona.expertise)}\n"
            )
            output += f"{BOLD}{CYAN}Perspective:{RESET} {active_persona.perspective}\n"

        # Contributions
        if session.contributions:
            output += f"\n{BOLD}{GREEN}Contributions:{RESET}\n"
            for contrib in session.contributions:
                persona = next(
                    (p for p in session.personas if p.id == contrib.persona_id), None
                )
                persona_name = persona.name if persona else contrib.persona_id

                output += f"\n{BOLD}{persona_name} ({contrib.type}, confidence: {contrib.confidence:.2f}):{RESET}\n"
                output += f"{contrib.content}\n"

        # Consensus points
        if session.consensus_points:
            output += f"\n{BOLD}{GREEN}Consensus Points:{RESET}\n"
            for i, point in enumerate(session.consensus_points, 1):
                output += f"{BOLD}{i}.{RESET} {point}\n"

        # Key insights
        if session.key_insights:
            output += f"\n{BOLD}{YELLOW}Key Insights:{RESET}\n"
            for i, insight in enumerate(session.key_insights, 1):
                output += f"{BOLD}{i}.{RESET} {insight}\n"

        # Final recommendation
        if session.final_recommendation:
            output += f"\n{BOLD}{CYAN}Final Recommendation:{RESET}\n"
            output += f"{session.final_recommendation}\n"

        return output

    def _find_references(
        self, content: str, contributions: List[ContributionData]
    ) -> List[str]:
        """Find contributions that this content references"""
        references = []
        content_lower = content.lower()

        for contrib in contributions:
            # Simple reference detection based on keyword overlap
            if any(
                word in content_lower for word in contrib.content.lower().split()[:5]
            ):
                references.append(f"{contrib.persona_id}_{contrib.type}")

        return references


def _generate_summary(vibe_level: str, detected_patterns: List[Dict[str, Any]]) -> str:
    """Generate a quick summary based on vibe level and patterns"""
    if detected_patterns:
        pattern_types = [p["pattern_type"] for p in detected_patterns]
        if "infrastructure_without_implementation" in pattern_types:
            return "Consider using official SDK instead of custom implementation"
        elif any("custom" in pt for pt in pattern_types):
            return "Explore standard solutions before building custom"
        else:
            return "Some patterns detected - check recommendations below"
    else:
        return "No concerning patterns detected - looking good!"


# Engine singleton for session management
_mentor_engine = None


def get_mentor_engine() -> VibeMentorEngine:
    """Get or create the global mentor engine instance"""
    global _mentor_engine
    if _mentor_engine is None:
        _mentor_engine = VibeMentorEngine()
    return _mentor_engine
