"""
Vibe Check Mentor - Collaborative Reasoning Tool

Combines vibe-check pattern detection with collaborative reasoning to provide
senior engineer feedback through multiple engineering perspectives.

Inspired by Clear-Thought's collaborative reasoning patterns with native implementation
for vibe-check educational coaching.
"""

# Standard library
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Literal, Union
import json
import logging
import secrets

# Local imports
from ..core.pattern_detector import PatternDetector
from ..core.vibe_coaching import VibeCoachingFramework, CoachingTone
from ..tools.analyze_text_nollm import analyze_text_demo
from ..utils.logging_framework import get_vibe_logger

logger = logging.getLogger(__name__)
vibe_logger = get_vibe_logger("vibe_mentor")

# Cache interrupt logger to avoid creating new instances on every call
_interrupt_logger = get_vibe_logger("mentor_interrupt")


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
            return any(p.get("pattern_type") == pattern_type for p in patterns if isinstance(p, dict))
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
        self._enhanced_mode = True  # Flag to enable enhanced reasoning

    def create_session(
        self,
        topic: str,
        personas: Optional[List[PersonaData]] = None,
        session_id: Optional[str] = None,
    ) -> CollaborativeReasoningSession:
        """Initialize a new collaborative reasoning session"""

        session_id = session_id or f"mentor-session-{int(datetime.now().timestamp())}-{secrets.token_hex(4)}"

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

        # Use enhanced reasoning if available
        if self._enhanced_mode:
            try:
                from .vibe_mentor_enhanced import EnhancedVibeMentorEngine
                enhanced_engine = EnhancedVibeMentorEngine(self)
                return enhanced_engine.generate_contribution(
                    session, persona, detected_patterns, context
                )
            except ImportError:
                logger.warning("Enhanced reasoning not available, falling back to basic mode")
                self._enhanced_mode = False

        # Fallback to original reasoning
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
            base_response = InfrastructurePatternHandler.get_senior_engineer_response()
            # Enhance with topic-specific context
            enhanced_content = f"{base_response[1]} Specifically for '{topic}', I'd recommend checking if there's an official SDK or documented API that handles this use case."
            return (base_response[0], enhanced_content, base_response[2])

        # Handle custom solution patterns with topic context
        base_response = CustomSolutionHandler.get_senior_engineer_insight(topic)
        # Add specific technical concerns based on topic keywords
        if any(keyword in topic.lower() for keyword in ["api", "integration", "service"]):
            enhanced_content = f"{base_response[1]} For integrations like '{topic}', I always check the official documentation first - it often shows simpler approaches than what we initially consider."
            return (base_response[0], enhanced_content, base_response[2])
        
        return base_response

    def _reason_as_product_engineer(
        self, patterns: List[Dict[str, Any]], topic: str
    ) -> tuple[str, str, float]:
        """Generate product engineer perspective focused on rapid delivery"""

        # If patterns detected, focus on rapid prototyping with topic context
        if patterns:
            base_response = ProductEngineerHandler.get_rapid_delivery_response()
            # Add topic-specific user value consideration
            enhanced_content = f"{base_response[1]} For '{topic}', let's focus on what users actually need rather than what's technically interesting to build."
            return (base_response[0], enhanced_content, base_response[2])

        # Otherwise, handle based on topic with specific context
        base_response = ProductEngineerHandler.get_planning_challenge(topic)
        # Add product-specific concerns based on topic
        if any(keyword in topic.lower() for keyword in ["build", "create", "implement"]):
            enhanced_content = f"{base_response[1]} Before building '{topic}', have we validated this solves a real user problem? I'd rather ship something imperfect that users love than something perfect they don't need."
            return (base_response[0], enhanced_content, base_response[2])
        
        return base_response

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

    def generate_interrupt_intervention(
        self,
        query: str,
        phase: str,
        primary_pattern: Dict[str, Any],
        pattern_confidence: float,
    ) -> Dict[str, Any]:
        """
        Generate a focused interrupt intervention based on detected patterns and phase.
        Returns a single question/suggestion for quick decision guidance.
        """
        _interrupt_logger.progress("Generating quick intervention", "⚡")
        
        pattern_type = primary_pattern.get("pattern_type", "unknown")
        _interrupt_logger.info(f"Analyzing {pattern_type} pattern in {phase} phase", "🔍")
        
        # Try to use enhanced interrupt generation
        if self._enhanced_mode:
            try:
                from .vibe_mentor_enhanced import ContextExtractor, TechnicalContext
                tech_context = ContextExtractor.extract_context(query)
                
                # Generate more specific interrupts based on technical context
                if tech_context.technologies:
                    tech = tech_context.technologies[0]
                    if pattern_type == "infrastructure_without_implementation":
                        return {
                            "question": f"Have you checked if {tech} provides an official SDK or Docker image?",
                            "severity": "high",
                            "suggestion": f"Check {tech}'s official docs/GitHub for SDK",
                            "pattern_type": pattern_type,
                            "confidence": pattern_confidence
                        }
                    elif pattern_type == "custom_solution_preferred":
                        return {
                            "question": f"Is there a {tech} library that already handles this?",
                            "severity": "medium", 
                            "suggestion": f"Search '{tech} {tech_context.specific_features[0] if tech_context.specific_features else 'library'}' on GitHub",
                            "pattern_type": pattern_type,
                            "confidence": pattern_confidence
                        }
                
                # Specific feature-based interrupts
                if tech_context.specific_features:
                    feature = tech_context.specific_features[0]
                    return {
                        "question": f"Have you validated that users actually need {feature}?",
                        "severity": "medium",
                        "suggestion": f"Build minimal {feature} MVP first",
                        "pattern_type": pattern_type,
                        "confidence": pattern_confidence
                    }
                
            except Exception as e:
                logger.debug(f"Enhanced interrupt generation failed: {e}, using basic mode")
        
        # Phase-specific questions mapped to patterns
        phase_questions = {
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
        
        # Get phase-specific question
        questions = phase_questions.get(phase, phase_questions["planning"])
        question = questions.get(pattern_type, questions["default"])
        
        # Determine severity based on pattern confidence and type
        severity_map = {
            "infrastructure_without_implementation": "high",
            "custom_solution_preferred": "medium",
            "documentation_neglect": "medium",
            "complexity_escalation": "low",
        }
        severity = severity_map.get(pattern_type, "low")
        
        # Generate quick suggestion based on pattern
        suggestions = {
            "infrastructure_without_implementation": 
                "Check docs.api.com/sdks first",
            "custom_solution_preferred":
                "Try the standard approach",
            "documentation_neglect":
                "Review official documentation",
            "complexity_escalation":
                "Consider YAGNI principle",
            "default":
                "Validate with simpler approach"
        }
        suggestion = suggestions.get(pattern_type, suggestions["default"])
        
        # Adjust suggestion based on specific keywords in query
        if "http" in query.lower() or "client" in query.lower():
            suggestion = "Check for official SDK with retry/auth handling"
        elif "auth" in query.lower():
            suggestion = "Use established auth library (OAuth2, JWT)"
        elif "abstract" in query.lower() or "layer" in query.lower():
            suggestion = "Start concrete, abstract only when patterns emerge"
        
        result = {
            "question": question,
            "severity": severity,
            "suggestion": suggestion,
            "pattern_type": pattern_type,
            "confidence": pattern_confidence
        }
        
        _interrupt_logger.success(f"Generated {severity} priority intervention for {pattern_type}")
        return result

    def cleanup_old_sessions(self, max_sessions: int = 50) -> None:
        """
        Clean up old sessions to prevent memory leaks.
        
        Args:
            max_sessions: Maximum number of sessions to keep in memory
        """
        if len(self.sessions) > max_sessions:
            # Sort sessions by last update time and keep the most recent
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].iteration,  # Use iteration as proxy for recency
                reverse=True
            )
            
            # Keep only the most recent sessions
            sessions_to_keep = dict(sorted_sessions[:max_sessions])
            removed_count = len(self.sessions) - len(sessions_to_keep)
            
            self.sessions = sessions_to_keep
            logger.info(f"Cleaned up {removed_count} old mentor sessions")


def _generate_summary(vibe_level: str, detected_patterns: List[Dict[str, Any]], 
                     synthesis: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a quick summary based on vibe level, patterns, and collaborative insights.
    
    Args:
        vibe_level: Assessed vibe level from pattern detection
        detected_patterns: List of detected anti-patterns
        synthesis: Optional synthesis from collaborative reasoning
        
    Returns:
        Summary that reflects both pattern detection and persona concerns
    """
    # Check if personas identified concerns even if patterns weren't detected
    persona_concerns = []
    if synthesis:
        persona_concerns = synthesis.get("primary_concerns", [])
        consensus_points = synthesis.get("consensus_points", [])
        
        # Check if consensus indicates concerns
        concern_indicators = ["avoid", "concern", "risk", "problem", "issue", "anti-pattern"]
        has_consensus_concerns = any(
            any(indicator in point.lower() for indicator in concern_indicators)
            for point in consensus_points
        )
    else:
        has_consensus_concerns = False
    
    # Generate summary based on patterns AND persona feedback
    if detected_patterns:
        pattern_types = [p["pattern_type"] for p in detected_patterns]
        if "infrastructure_without_implementation" in pattern_types:
            return "Consider using official SDK instead of custom implementation"
        elif any("custom" in pt for pt in pattern_types):
            return "Explore standard solutions before building custom"
        else:
            return "Some patterns detected - check recommendations below"
    elif persona_concerns or has_consensus_concerns:
        # Personas identified concerns even without pattern detection
        return "Engineering team has concerns - review collaborative insights"
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


def cleanup_mentor_engine() -> None:
    """Clear global engine state for testing/cleanup"""
    global _mentor_engine
    _mentor_engine = None
