"""
Vibe Check Mentor - Collaborative Reasoning Tool

Refactored modular implementation that combines vibe-check pattern detection
with collaborative reasoning to provide senior engineer feedback through
multiple engineering perspectives.

This is the main interface that orchestrates the modular components.
"""

# Standard library
import logging
import secrets
from typing import Dict, Any, List, Optional

# Local imports - core functionality
from ..core.pattern_detector import PatternDetector
from ..core.vibe_coaching import VibeCoachingFramework, CoachingTone
from ..tools.analyze_text_nollm import analyze_text_demo
from ..utils.logging_framework import get_vibe_logger

# Local imports - modular mentor components
from ..mentor.models.persona import PersonaData
from ..mentor.models.session import CollaborativeReasoningSession, ContributionData
from ..mentor.models.config import DEFAULT_PERSONAS, DEFAULT_MAX_SESSIONS, ConfidenceScores
from ..mentor.session.manager import SessionManager
from ..mentor.session.state_tracker import StateTracker
from ..mentor.session.synthesis import SessionSynthesizer
from ..mentor.response.coordinator import ResponseCoordinator
from ..mentor.response.formatters.console import ConsoleFormatter
from ..mentor.config.constants import (
    PATTERN_SEVERITY_MAP, 
    PATTERN_SUGGESTIONS,
    PHASE_QUESTIONS,
    CONCERN_INDICATORS
)

logger = logging.getLogger(__name__)
vibe_logger = get_vibe_logger("vibe_mentor")

# Cache interrupt logger to avoid creating new instances on every call
_interrupt_logger = get_vibe_logger("mentor_interrupt")


class VibeMentorEngine:
    """
    Refactored collaborative reasoning engine using modular components.
    
    This class now orchestrates the extracted modules rather than implementing
    all functionality directly, following the Single Responsibility Principle.
    """

    def __init__(self):
        # Core components - dependency injection for better modularity
        self.session_manager = SessionManager()
        self.response_coordinator = ResponseCoordinator() 
        self.pattern_detector = PatternDetector()
        self._enhanced_mode = True  # Flag to enable enhanced reasoning

    # Delegate session management to SessionManager
    def create_session(
        self,
        topic: str,
        personas: Optional[List[PersonaData]] = None,
        session_id: Optional[str] = None,
    ) -> CollaborativeReasoningSession:
        """Initialize a new collaborative reasoning session"""
        return self.session_manager.create_session(topic, personas, session_id)

    # Delegate response generation to ResponseCoordinator  
    def generate_contribution(
        self,
        session: CollaborativeReasoningSession,
        persona: PersonaData,
        detected_patterns: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> ContributionData:
        """Generate a contribution from a persona based on their characteristics"""
        
        # Use enhanced reasoning if available
        if self._enhanced_mode:
            try:
                from .vibe_mentor_enhanced import EnhancedVibeMentorEngine
                enhanced_engine = EnhancedVibeMentorEngine(self)
                return enhanced_engine.generate_contribution(
                    session, persona, detected_patterns, context
                )
            except ImportError as e:
                logger.warning(f"Enhanced reasoning not available: {str(e)}, falling back to basic mode")
                self._enhanced_mode = False
            except Exception as e:
                logger.error(f"Enhanced reasoning failed: {str(e)}, falling back to basic mode")
                self._enhanced_mode = False

        # Use modular response coordinator
        return self.response_coordinator.generate_contribution(
            session, persona, detected_patterns, context
        )

    # Delegate state management to StateTracker
    def advance_stage(self, session: CollaborativeReasoningSession) -> str:
        """Advance to the next stage in the reasoning process"""
        return StateTracker.advance_stage(session)

    # Delegate synthesis to SessionSynthesizer  
    def synthesize_session(self, session: CollaborativeReasoningSession) -> Dict[str, Any]:
        """Synthesize the collaborative reasoning session into actionable insights"""
        return SessionSynthesizer.synthesize_session(session)

    # Delegate formatting to ConsoleFormatter
    def format_session_output(self, session: CollaborativeReasoningSession) -> str:
        """Format session for display using ANSI colors"""
        return ConsoleFormatter.format_session_output(session)

    # Delegate session cleanup to SessionManager
    def cleanup_old_sessions(self, max_sessions: int = DEFAULT_MAX_SESSIONS) -> None:
        """Clean up old sessions to prevent memory leaks"""
        self.session_manager.cleanup_old_sessions(max_sessions)

    # Direct access to sessions for backward compatibility
    @property
    def sessions(self) -> Dict[str, CollaborativeReasoningSession]:
        """Access to sessions for backward compatibility"""
        return self.session_manager.sessions

    def generate_interrupt_intervention(
        self,
        query: str,
        phase: str,
        primary_pattern: Dict[str, Any],
        pattern_confidence: float,
    ) -> Dict[str, Any]:
        """
        Generate a focused interrupt intervention based on detected patterns and phase.
        Uses modular configuration for cleaner implementation.
        """
        # Generate correlation ID for this interrupt
        interrupt_id = f"interrupt-{secrets.token_hex(4)}"
        _interrupt_logger.progress(f"Generating quick intervention [{interrupt_id}]", "⚡")
        
        pattern_type = primary_pattern.get("pattern_type", "unknown")
        _interrupt_logger.info(f"Analyzing {pattern_type} pattern in {phase} phase", "🔍")
        
        # Try enhanced mode first
        if self._enhanced_mode:
            try:
                from .vibe_mentor_enhanced import ContextExtractor
                tech_context = ContextExtractor.extract_context(query)
                
                if tech_context.technologies:
                    tech = tech_context.technologies[0]
                    if pattern_type == "infrastructure_without_implementation":
                        return self._create_intervention_response(
                            f"Have you checked if {tech} provides an official SDK or Docker image?",
                            "high",
                            f"Check {tech}'s official docs/GitHub for SDK",
                            pattern_type,
                            pattern_confidence,
                            interrupt_id
                        )
                        
            except Exception as e:
                logger.debug(f"Enhanced interrupt generation failed [{interrupt_id}]: {e}")
        
        # Use modular configuration for basic mode
        questions = PHASE_QUESTIONS.get(phase, PHASE_QUESTIONS["planning"])
        question = questions.get(pattern_type, questions["default"])
        
        severity = PATTERN_SEVERITY_MAP.get(pattern_type, "low")
        suggestion = PATTERN_SUGGESTIONS.get(pattern_type, PATTERN_SUGGESTIONS["default"])
        
        # Adjust suggestion based on query keywords
        if "http" in query.lower() or "client" in query.lower():
            suggestion = "Check for official SDK with retry/auth handling"
        elif "auth" in query.lower():
            suggestion = "Use established auth library (OAuth2, JWT)"
        elif "abstract" in query.lower() or "layer" in query.lower():
            suggestion = "Start concrete, abstract only when patterns emerge"
        
        return self._create_intervention_response(
            question, severity, suggestion, pattern_type, pattern_confidence, interrupt_id
        )
    
    def _create_intervention_response(
        self, question: str, severity: str, suggestion: str, 
        pattern_type: str, confidence: float, interrupt_id: str
    ) -> Dict[str, Any]:
        """Create standardized intervention response"""
        result = {
            "question": question,
            "severity": severity,
            "suggestion": suggestion,
            "pattern_type": pattern_type,
            "confidence": confidence,
            "interrupt_id": interrupt_id
        }
        
        _interrupt_logger.success(f"Generated {severity} priority intervention for {pattern_type} [{interrupt_id}]")
        return result


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
        
        # Check if consensus indicates concerns using modular configuration
        has_consensus_concerns = any(
            any(indicator in point.lower() for indicator in CONCERN_INDICATORS)
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
