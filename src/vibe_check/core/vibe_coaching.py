"""
Vibe Check Educational Coaching Framework

Provides friendly, practical coaching guidance for developers based on detected
engineering patterns and vibe assessment. Transforms technical anti-pattern
language into encouraging, educational content that helps developers learn.

This implements the educational coaching framework described in Issue #40.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field

from .educational_content import DetailLevel
from .pattern_detector import DetectionResult


class LearningLevel(Enum):
    """Learning progression levels for coaching"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CoachingTone(Enum):
    """Coaching tone styles"""

    ENCOURAGING = "encouraging"
    DIRECT = "direct"
    SUPPORTIVE = "supportive"


@dataclass
class CoachingRecommendation:
    """Individual coaching recommendation with context"""

    title: str
    description: str
    action_items: List[str]
    learning_resources: List[str]
    prevention_checklist: List[str]
    real_world_example: Optional[str] = None
    common_mistakes: List[str] = field(default_factory=list)


class VibeCoachingFramework:
    """
    Comprehensive educational coaching framework for vibe checks.

    Provides practical, encouraging guidance that helps developers learn
    best practices while avoiding common engineering pitfalls.
    """

    def __init__(self):
        """Initialize the coaching framework"""
        self.coaching_patterns = self._load_coaching_patterns()

    def generate_coaching_recommendations(
        self,
        vibe_level: str,
        detected_patterns: List[DetectionResult],
        issue_context: Dict[str, Any],
        detail_level: DetailLevel = DetailLevel.STANDARD,
        learning_level: LearningLevel = LearningLevel.INTERMEDIATE,
        tone: CoachingTone = CoachingTone.ENCOURAGING,
    ) -> List[CoachingRecommendation]:
        """
        Generate comprehensive coaching recommendations based on vibe assessment.

        Args:
            vibe_level: Overall vibe assessment (good_vibes, needs_research, etc.)
            detected_patterns: List of detected technical patterns
            issue_context: Issue context and metadata
            detail_level: Level of educational detail
            learning_level: Target learning level
            tone: Coaching tone preference

        Returns:
            List of structured coaching recommendations
        """
        recommendations = []

        # Generate vibe-specific coaching
        vibe_coaching = self._generate_vibe_specific_coaching(
            vibe_level, tone, learning_level
        )
        if vibe_coaching:
            recommendations.append(vibe_coaching)

        # Generate pattern-specific coaching
        for pattern in detected_patterns:
            if pattern.detected and pattern.confidence > 0.6:
                pattern_coaching = self._generate_pattern_coaching(
                    pattern, issue_context, detail_level, learning_level, tone
                )
                if pattern_coaching:
                    recommendations.append(pattern_coaching)

        # Generate general learning recommendations
        general_coaching = self._generate_general_learning_recommendations(
            issue_context, detected_patterns, learning_level, tone
        )
        if general_coaching:
            recommendations.extend(general_coaching)

        return recommendations

    def _generate_vibe_specific_coaching(
        self, vibe_level: str, tone: CoachingTone, learning_level: LearningLevel
    ) -> Optional[CoachingRecommendation]:
        """Generate coaching specific to the overall vibe assessment"""

        coaching_templates = {
            "good_vibes": {
                "title": "🎯 Ready to Roll!",
                "description": "This issue has great vibes! Your approach looks solid and well-thought-out.",
                "action_items": [
                    "Proceed with implementation following your plan",
                    "Set up tests early to validate your approach",
                    "Consider breaking large tasks into smaller milestones",
                    "Document key decisions and learnings as you go",
                ],
                "learning_resources": [
                    "Best practices for iterative development",
                    "Test-driven development fundamentals",
                    "Documentation-as-code principles",
                ],
                "prevention_checklist": [
                    "Regular progress check-ins",
                    "Early feedback loops",
                    "Continuous integration setup",
                    "Clear acceptance criteria validation",
                ],
            },
            "needs_research": {
                "title": "🔍 Time to Do Some Homework!",
                "description": "Great question! Let's do some research first to build on what already exists instead of reinventing wheels.",
                "action_items": [
                    "Search for existing solutions and libraries in this domain",
                    "Read official documentation and getting-started guides",
                    "Find working examples and tutorials",
                    "Identify what tools are already in your project",
                    "Document your research findings before coding",
                ],
                "learning_resources": [
                    "How to research existing solutions effectively",
                    "Reading technical documentation strategies",
                    "Evaluating third-party libraries and tools",
                    "Standing on the shoulders of giants: using existing work",
                ],
                "prevention_checklist": [
                    "Always check official docs first",
                    "Search GitHub for similar implementations",
                    "Look for community solutions and patterns",
                    "Understand the problem domain before building",
                ],
                "real_world_example": "Before building a custom authentication system, developers typically research existing solutions like Auth0, Firebase Auth, or Supabase Auth. This research phase prevents reinventing complex security patterns.",
            },
            "needs_poc": {
                "title": "🧪 Show Me the Magic!",
                "description": "Love the ambition! Let's prove the core functionality works with real data before building the full architecture.",
                "action_items": [
                    "Create a minimal proof-of-concept with actual APIs",
                    "Test basic functionality with real data (not mocks)",
                    "Validate key assumptions with working code",
                    "Document what works and what doesn't",
                    "Only then design the full architecture",
                ],
                "learning_resources": [
                    "Proof-of-concept development strategies",
                    "API integration testing patterns",
                    "Rapid prototyping techniques",
                    "Validating assumptions with code",
                ],
                "prevention_checklist": [
                    "Start with basic API calls, not infrastructure",
                    "Use real data, not placeholder values",
                    "Test the happy path first",
                    "Prove integration works before scaling",
                    "Document POC learnings thoroughly",
                ],
                "real_world_example": "When integrating with a new AI service, start with a simple script that calls the API with real data. Prove it works, understand the response format, then build the full integration.",
                "common_mistakes": [
                    "Building infrastructure before proving basic functionality",
                    "Using mock data instead of real API responses",
                    "Designing complex architecture without understanding the API",
                    "Skipping the POC phase due to time pressure",
                ],
            },
            "complex_vibes": {
                "title": "⚖️ Let's Simplify This Journey",
                "description": "This feels pretty sophisticated! Have we considered if there's a simpler path that achieves the same goals?",
                "action_items": [
                    "Question whether this complexity is truly necessary",
                    "Try the simplest approach that could possibly work",
                    "Break complex problems into smaller, manageable pieces",
                    "Document why simple solutions aren't sufficient",
                    "Ensure complexity is proportional to business value",
                ],
                "learning_resources": [
                    "YAGNI (You Aren't Gonna Need It) principle",
                    "Occam's Razor in software engineering",
                    "Breaking down complex problems",
                    "Balancing simplicity and functionality",
                ],
                "prevention_checklist": [
                    "Start with the simplest solution",
                    "Add complexity only when proven necessary",
                    "Justify each layer of abstraction",
                    "Consider maintainability and understandability",
                    "Measure complexity against business value",
                ],
                "real_world_example": "Instead of building a complex microservices architecture for a small app, start with a simple monolith and only split into services when you hit real scaling needs.",
                "common_mistakes": [
                    "Over-engineering solutions for simple problems",
                    "Adding abstraction layers 'just in case'",
                    "Building for imaginary future requirements",
                    "Choosing complex tools when simple ones suffice",
                ],
            },
            "bad_vibes": {
                "title": "🚨 Hold Up - Let's Reset!",
                "description": "This looks like it might be building infrastructure without proving the basics work. Let's step back and start with fundamentals.",
                "action_items": [
                    "STOP building infrastructure and start with basic API usage",
                    "Focus on proving core functionality first",
                    "Read the official documentation and follow standard patterns",
                    "Create a working example with real data",
                    "Come back to architecture after basics work",
                ],
                "learning_resources": [
                    "API-first development principles",
                    "Learning from the Cognee failure retrospective",
                    "Infrastructure-without-implementation anti-pattern",
                    "Focusing on business value over technical complexity",
                ],
                "prevention_checklist": [
                    "Never build infrastructure before API usage",
                    "Always start with official SDK examples",
                    "Prove functionality before optimization",
                    "Focus on user value, not technical elegance",
                    "Question every piece of custom infrastructure",
                ],
                "real_world_example": "The Cognee integration failed because developers spent 2+ years building custom HTTP servers instead of using cognee.add() → cognee.cognify() → cognee.search(). Basic API usage should always come first.",
                "common_mistakes": [
                    "Building custom solutions when standard APIs exist",
                    "Infrastructure-first thinking",
                    "Solving symptoms instead of root causes",
                    "Not following official documentation patterns",
                ],
            },
        }

        template = coaching_templates.get(vibe_level)
        if not template:
            return None

        # Convert sequences to proper types
        title = (
            template["title"]
            if isinstance(template["title"], str)
            else " ".join(template["title"])
        )
        description = (
            template["description"]
            if isinstance(template["description"], str)
            else " ".join(template["description"])
        )
        action_items = (
            template["action_items"]
            if isinstance(template["action_items"], list)
            else list(template["action_items"])
        )
        learning_resources = (
            template["learning_resources"]
            if isinstance(template["learning_resources"], list)
            else list(template["learning_resources"])
        )
        prevention_checklist = (
            template["prevention_checklist"]
            if isinstance(template["prevention_checklist"], list)
            else list(template["prevention_checklist"])
        )
        real_world_example_raw = template.get("real_world_example")
        if real_world_example_raw is None:
            real_world_example = None
        elif isinstance(real_world_example_raw, str):
            real_world_example = real_world_example_raw
        else:
            real_world_example = " ".join(real_world_example_raw)
        common_mistakes = template.get("common_mistakes", [])
        if not isinstance(common_mistakes, list):
            common_mistakes = list(common_mistakes) if common_mistakes else []

        # Adjust tone based on preference
        if tone == CoachingTone.DIRECT:
            description = self._make_more_direct(description)
        elif tone == CoachingTone.SUPPORTIVE:
            description = self._make_more_supportive(description)

        return CoachingRecommendation(
            title=title,
            description=description,
            action_items=action_items,
            learning_resources=learning_resources,
            prevention_checklist=prevention_checklist,
            real_world_example=real_world_example,
            common_mistakes=common_mistakes,
        )

    def _generate_pattern_coaching(
        self,
        pattern: DetectionResult,
        issue_context: Dict[str, Any],
        detail_level: DetailLevel,
        learning_level: LearningLevel,
        tone: CoachingTone,
    ) -> Optional[CoachingRecommendation]:
        """Generate coaching specific to detected patterns"""

        pattern_coaching = {
            "infrastructure_without_implementation": {
                "title": "🏗️ Foundation Without Function Alert",
                "description": "It looks like this might be planning infrastructure before proving basic functionality. Let's start with working examples first!",
                "action_items": [
                    "Start with the simplest possible working example",
                    "Use official SDKs and standard patterns",
                    "Prove basic functionality with real data",
                    "Document what works before building abstractions",
                    "Build infrastructure only after basics are proven",
                ],
                "learning_resources": [
                    "API-first development methodology",
                    "MVP (Minimum Viable Product) principles",
                    "The importance of working software over comprehensive documentation",
                ],
                "prevention_checklist": [
                    "Always start with basic API calls",
                    "Use real data, not mock data",
                    "Follow official getting-started guides",
                    "Build infrastructure only when needed",
                    "Focus on user value first",
                ],
            },
            "symptom_driven_development": {
                "title": "🎯 Root Cause Focus",
                "description": "This might be addressing symptoms rather than the underlying cause. Let's dig deeper to find the real issue!",
                "action_items": [
                    "Ask 'why' five times to find the root cause",
                    "Look for related issues that might share the same cause",
                    "Consider if fixing the root cause eliminates this issue",
                    "Validate that this is the real problem to solve",
                    "Focus solutions on fundamental causes",
                ],
                "learning_resources": [
                    "Root cause analysis techniques",
                    "5 Whys methodology",
                    "Systems thinking in software engineering",
                ],
                "prevention_checklist": [
                    "Always ask why the problem exists",
                    "Look for patterns across multiple issues",
                    "Focus on causes, not effects",
                    "Validate problem understanding before solving",
                    "Consider systemic solutions",
                ],
            },
            "over_engineering": {
                "title": "🔧 Simplicity First",
                "description": "This solution might be more complex than needed. Let's explore simpler approaches that could work just as well!",
                "action_items": [
                    "Question every layer of abstraction",
                    "Try the simplest solution first",
                    "Add complexity only when proven necessary",
                    "Consider maintainability and team understanding",
                    "Measure complexity against business value",
                ],
                "learning_resources": [
                    "KISS principle (Keep It Simple, Stupid)",
                    "Technical debt and maintainability",
                    "Building for today's needs, not tomorrow's guesses",
                ],
                "prevention_checklist": [
                    "Start simple, add complexity when needed",
                    "Justify every abstraction layer",
                    "Consider team's ability to maintain",
                    "Focus on immediate business needs",
                    "Avoid premature optimization",
                ],
            },
        }

        coaching = pattern_coaching.get(pattern.pattern_type)
        if not coaching:
            return None

        # Convert sequences to proper types
        title = (
            coaching["title"]
            if isinstance(coaching["title"], str)
            else " ".join(coaching["title"])
        )
        description = (
            coaching["description"]
            if isinstance(coaching["description"], str)
            else " ".join(coaching["description"])
        )
        action_items = (
            coaching["action_items"]
            if isinstance(coaching["action_items"], list)
            else list(coaching["action_items"])
        )
        learning_resources = (
            coaching["learning_resources"]
            if isinstance(coaching["learning_resources"], list)
            else list(coaching["learning_resources"])
        )
        prevention_checklist = (
            coaching["prevention_checklist"]
            if isinstance(coaching["prevention_checklist"], list)
            else list(coaching["prevention_checklist"])
        )

        return CoachingRecommendation(
            title=title,
            description=description,
            action_items=action_items,
            learning_resources=learning_resources,
            prevention_checklist=prevention_checklist,
        )

    def _generate_general_learning_recommendations(
        self,
        issue_context: Dict[str, Any],
        detected_patterns: List[DetectionResult],
        learning_level: LearningLevel,
        tone: CoachingTone,
    ) -> List[CoachingRecommendation]:
        """Generate general learning and improvement recommendations"""

        recommendations = []

        # Learning opportunity based on issue complexity
        if len(detected_patterns) > 0:
            recommendations.append(
                CoachingRecommendation(
                    title="📚 Learning Opportunity",
                    description="This issue provides great learning opportunities! Here's how to maximize your growth.",
                    action_items=[
                        "Document your decision-making process",
                        "Note what worked and what didn't",
                        "Share learnings with the team",
                        "Consider pair programming for complex parts",
                        "Reflect on the process after completion",
                    ],
                    learning_resources=[
                        "Reflective practice in software development",
                        "Technical journaling and documentation",
                        "Knowledge sharing best practices",
                    ],
                    prevention_checklist=[
                        "Always document key decisions",
                        "Reflect on lessons learned",
                        "Share knowledge with others",
                        "Build learning into the development process",
                        "Create artifacts for future reference",
                    ],
                )
            )

        # Collaboration and feedback recommendations
        recommendations.append(
            CoachingRecommendation(
                title="🤝 Collaboration and Feedback",
                description="Great engineering happens in teams! Here's how to leverage collective wisdom.",
                action_items=[
                    "Get early feedback on your approach",
                    "Consider pairing on complex parts",
                    "Share progress regularly with stakeholders",
                    "Ask for code reviews on key components",
                    "Document decisions for team visibility",
                ],
                learning_resources=[
                    "Effective code review practices",
                    "Pair programming techniques",
                    "Stakeholder communication strategies",
                ],
                prevention_checklist=[
                    "Never work in isolation too long",
                    "Get feedback early and often",
                    "Communicate progress and blockers",
                    "Use team knowledge and experience",
                    "Make decisions transparent to others",
                ],
            )
        )

        return recommendations

    def _make_more_direct(self, text: str) -> str:
        """Adjust text for more direct tone"""
        # Remove softening language and make more direct
        replacements = {
            "might be": "is",
            "could be": "is",
            "This looks like it might": "This",
            "Let's": "You should",
            "Consider": "Do",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _make_more_supportive(self, text: str) -> str:
        """Adjust text for more supportive tone"""
        # Add more encouraging and supportive language
        if not text.startswith("I understand"):
            text = "I understand this can be challenging. " + text

        text = text.replace("This", "I see that this")
        text = text.replace("Let's", "Together, let's")

        return text

    def _load_coaching_patterns(self) -> Dict[str, Any]:
        """Load coaching patterns and templates"""
        # This could be loaded from a configuration file in a real implementation
        return {
            "encouragement_phrases": [
                "Great question!",
                "Love the thinking here!",
                "This is a common challenge that many developers face.",
                "You're on the right track!",
                "This shows good engineering instincts.",
            ],
            "learning_focus_areas": [
                "API-first development",
                "Iterative improvement",
                "Simple solutions first",
                "User value focus",
                "Team collaboration",
            ],
        }


# Global coaching framework instance
_coaching_framework = None


def get_vibe_coaching_framework() -> VibeCoachingFramework:
    """Get or create coaching framework instance"""
    global _coaching_framework
    if _coaching_framework is None:
        _coaching_framework = VibeCoachingFramework()
    return _coaching_framework
