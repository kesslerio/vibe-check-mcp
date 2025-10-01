"""
Vibe Check Mentor - Collaborative Reasoning Tool

Refactored modular implementation that combines vibe-check pattern detection
with collaborative reasoning to provide senior engineer feedback through
multiple engineering perspectives.

This is the main interface that orchestrates the modular components.

## Usage Patterns

### Production Usage (Singleton)
```python
# Standard production usage - uses singleton pattern
engine = get_mentor_engine()
result = engine.process_query(query)
```

### Testing Usage (Simple Dependency Injection)
```python  
# Testing with mocked dependencies
mock_detector = MockPatternDetector()
engine = create_mentor_engine(
    test_mode=True,
    pattern_detector=mock_detector
)
result = engine.process_query(query)
```

## Architecture Decision: Simple Test Factory vs Full DI

This module uses a **simple test factory pattern** instead of full dependency injection
based on collaborative reasoning that concluded full DI would be overengineering 
for a 1-2 developer team with no current singleton pain.

**Benefits of current approach:**
- 80% of DI benefits with 20% of effort (1 day vs 3-5 days)
- Zero production risk (singleton unchanged)  
- Enables comprehensive testing with mocks
- Clear upgrade path when/if problems emerge

**Upgrade to full DI only when experiencing:**
- Testing difficulties with global state
- Memory leaks from mentor sessions
- Concurrency race conditions  
- Team growth (3+ developers)
- Environment-specific configuration needs

*"Sometimes the best architecture decision is knowing when NOT to architect."*
"""

# Standard library
import logging
import secrets
from typing import Dict, Any, List, Optional

# Local imports - core functionality
from vibe_check.core.pattern_detector import PatternDetector
from vibe_check.core.vibe_coaching import VibeCoachingFramework, CoachingTone
from vibe_check.tools.analyze_text_nollm import analyze_text_demo
from vibe_check.utils.logging_framework import get_vibe_logger

# Local imports - modular mentor components
from vibe_check.mentor.models.persona import PersonaData
from vibe_check.mentor.models.session import CollaborativeReasoningSession, ContributionData
from vibe_check.mentor.models.config import DEFAULT_PERSONAS, DEFAULT_MAX_SESSIONS, ConfidenceScores
from vibe_check.mentor.session.manager import SessionManager
from vibe_check.mentor.session.state_tracker import StateTracker
from vibe_check.mentor.session.synthesis import SessionSynthesizer
from vibe_check.mentor.response.coordinator import ResponseCoordinator
from vibe_check.mentor.response.formatters.console import ConsoleFormatter
from vibe_check.mentor.config.constants import (
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
        self._enhanced_mode = True  # Re-enabled for better context-aware responses (Issue fix)
        
        # Backward compatibility attributes
        self.DEFAULT_PERSONAS = DEFAULT_PERSONAS

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
        project_context: Optional[Any] = None,
        file_contexts: Optional[List[Any]] = None,
    ) -> ContributionData:
        """Generate a contribution from a persona based on their characteristics"""
        
        # Use enhanced reasoning if available
        if self._enhanced_mode:
            try:
                from .vibe_mentor_enhanced import EnhancedVibeMentorEngine
                import asyncio
                enhanced_engine = EnhancedVibeMentorEngine(self)
                
                # Handle async call properly
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're in an async context, we can't use run_until_complete
                        logger.warning("Cannot run async enhanced mode from async context, falling back to basic mode")
                        self._enhanced_mode = False
                    else:
                        return loop.run_until_complete(enhanced_engine.generate_contribution(
                            session, persona, detected_patterns, context, project_context, file_contexts
                        ))
                except RuntimeError:
                    # No event loop running, create one
                    return asyncio.run(enhanced_engine.generate_contribution(
                        session, persona, detected_patterns, context, project_context, file_contexts
                    ))
            except ImportError as e:
                logger.warning(f"Enhanced reasoning not available: {str(e)}, falling back to basic mode")
                self._enhanced_mode = False
            except Exception as e:
                logger.error(f"Enhanced reasoning failed: {str(e)}, falling back to basic mode")
                self._enhanced_mode = False

        # Use modular response coordinator with project context
        return self.response_coordinator.generate_contribution(
            session, persona, detected_patterns, context, project_context
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


class TestMentorEngine(VibeMentorEngine):
    """
    Test version of VibeMentorEngine that supports dependency injection.
    
    Allows mocking dependencies for comprehensive testing while maintaining
    the same interface as the production VibeMentorEngine.
    """
    
    def __init__(
        self,
        session_manager=None,
        response_coordinator=None, 
        pattern_detector=None,
        **kwargs
    ):
        # Don't call super().__init__() to avoid creating default dependencies
        
        # Inject provided dependencies or create defaults
        self.session_manager = session_manager or SessionManager()
        self.response_coordinator = response_coordinator or ResponseCoordinator()
        self.pattern_detector = pattern_detector or PatternDetector()
        
        # Enhanced mode disabled for test isolation (avoid async complexity in tests)
        self._enhanced_mode = kwargs.get('enhanced_mode', False)
        
        # Backward compatibility attributes
        self.DEFAULT_PERSONAS = DEFAULT_PERSONAS


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


def create_mentor_engine(
    test_mode: bool = False, 
    **test_doubles: Any
) -> VibeMentorEngine:
    """
    Factory for creating mentor engines with optional test dependency injection.
    
    This provides 80% of dependency injection benefits with 20% of the effort,
    following the YAGNI principle for small teams without current singleton pain.
    
    Args:
        test_mode: If True, creates a test engine with injected dependencies
        **test_doubles: Optional mock dependencies (pattern_detector, session_manager, etc.)
        
    Returns:
        VibeMentorEngine instance - either singleton for production or test instance
        
    Usage:
        # Production (unchanged)
        engine = get_mentor_engine()
        
        # Testing (new capability)  
        mock_detector = MockPatternDetector()
        engine = create_mentor_engine(
            test_mode=True,
            pattern_detector=mock_detector
        )
        
    Future: Upgrade to full dependency injection only when experiencing:
    - Testing difficulties with global state
    - Memory leaks from mentor sessions  
    - Concurrency race conditions
    - Team growth (3+ developers)
    - Environment-specific configuration needs
    """
    if test_mode:
        # Return test engine with injected dependencies
        return TestMentorEngine(**test_doubles)
    else:
        # Production path: use existing singleton (zero risk)
        return get_mentor_engine()
