"""
AI Doom Loop Detector for Vibe Coding Safety Net

Detects when developers get stuck in unproductive AI conversation loops,
analysis paralysis, and decision cycles without making concrete progress.
Designed to prevent the most expensive failure mode in AI-assisted development:
infinite planning and analysis without execution.

Key Detection Patterns:
1. Repeated topic analysis without decisions
2. Extended conversation sessions on same issues
3. Analysis tools called repeatedly without implementation
4. Time-sink patterns in decision-making processes
5. Overthinking symptoms in text content

Real-time Integration:
- Passive monitoring via MCP call tracking
- Automatic integration into existing LLM tools
- Contextual warnings during normal workflow
- Momentum restoration suggestions
"""

import time
import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class LoopSeverity(Enum):
    """Severity levels for doom loop detection"""

    NONE = "none"
    CAUTION = "caution"  # 15-20 minutes on same topic
    WARNING = "warning"  # 20-30 minutes, repeated calls
    CRITICAL = "critical"  # 30+ minutes, clear loops
    EMERGENCY = "emergency"  # 60+ minutes, intervention needed


@dataclass
class LoopPattern:
    """A detected doom loop pattern"""

    pattern_type: str
    severity: LoopSeverity
    duration_minutes: int
    evidence: List[str]
    topic: str
    intervention_suggestions: List[str]
    time_wasted_estimate: str


@dataclass
class SessionState:
    """Tracks the current MCP session state for doom loop detection"""

    session_id: str
    start_time: float
    mcp_calls: List[Dict[str, Any]] = field(default_factory=list)
    topics_discussed: Set[str] = field(default_factory=set)
    repeated_calls: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    decision_patterns: List[str] = field(default_factory=list)
    last_concrete_action: Optional[float] = None

    @property
    def session_duration_minutes(self) -> int:
        """Get current session duration in minutes"""
        return int((time.time() - self.start_time) / 60)


class DoomLoopDetector:
    """
    Detects AI doom loops and analysis paralysis patterns.

    This detector monitors MCP sessions and conversation patterns to identify
    when developers are stuck in unproductive loops. It integrates seamlessly
    with existing tools to provide contextual warnings and intervention suggestions.

    Detection Strategies:
    1. Temporal patterns (time spent on same topics)
    2. Repetition patterns (same tools called repeatedly)
    3. Decision paralysis patterns (analysis without action)
    4. Text analysis patterns (overthinking language)
    5. Progress indicators (lack of concrete steps)
    """

    def __init__(self):
        """Initialize the doom loop detector"""
        self.current_session = None
        self.detection_patterns = self._initialize_detection_patterns()
        self.intervention_strategies = self._initialize_interventions()

    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new MCP session for tracking"""
        if session_id is None:
            session_id = f"session_{int(time.time())}"

        self.current_session = SessionState(
            session_id=session_id, start_time=time.time()
        )

        logger.info(f"Started doom loop tracking for session {session_id}")
        return session_id

    def track_mcp_call(
        self,
        tool_name: str,
        content: str = "",
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an MCP tool call for pattern analysis"""
        if not self.current_session:
            self.start_session()

        call_data = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "content": content[:500],  # Truncate for memory efficiency
            "context": context[:200],
            "metadata": metadata or {},
        }

        self.current_session.mcp_calls.append(call_data)
        self.current_session.repeated_calls[tool_name] += 1

        # Extract and track topics
        topics = self._extract_topics(content, context)
        self.current_session.topics_discussed.update(topics)

        # Track decision patterns
        decision_text = self._extract_decision_language(content, context)
        if decision_text:
            self.current_session.decision_patterns.append(decision_text)

    def analyze_current_session(self) -> Optional[LoopPattern]:
        """
        Analyze the current session for doom loop patterns.

        Returns the most severe loop pattern detected, or None if session is healthy.
        """
        if not self.current_session:
            return None

        detected_patterns = []

        # Check temporal patterns
        temporal_pattern = self._check_temporal_patterns()
        if temporal_pattern:
            detected_patterns.append(temporal_pattern)

        # Check repetition patterns
        repetition_pattern = self._check_repetition_patterns()
        if repetition_pattern:
            detected_patterns.append(repetition_pattern)

        # Check decision paralysis
        paralysis_pattern = self._check_decision_paralysis()
        if paralysis_pattern:
            detected_patterns.append(paralysis_pattern)

        # Check topic cycling
        cycling_pattern = self._check_topic_cycling()
        if cycling_pattern:
            detected_patterns.append(cycling_pattern)

        # Return most severe pattern
        if detected_patterns:
            most_severe = max(
                detected_patterns, key=lambda p: self._severity_score(p.severity)
            )
            return most_severe

        return None

    def get_intervention_recommendation(
        self, loop_pattern: LoopPattern
    ) -> Dict[str, Any]:
        """
        Get specific intervention recommendations based on detected pattern.

        Provides actionable steps to break out of the doom loop.
        """
        base_recommendation = {
            "severity": loop_pattern.severity.value,
            "message": self._generate_intervention_message(loop_pattern),
            "immediate_actions": loop_pattern.intervention_suggestions,
            "time_budget": self._suggest_time_budget(loop_pattern),
            "decision_forcing": self._generate_decision_forcing_questions(loop_pattern),
        }

        # Add severity-specific recommendations
        if loop_pattern.severity == LoopSeverity.CRITICAL:
            base_recommendation["urgent_actions"] = [
                "🚨 STOP: Set 15-minute timer for final decision",
                "Pick the simplest option that works",
                "Start implementation immediately",
                "Validate with real usage, not more analysis",
            ]
        elif loop_pattern.severity == LoopSeverity.EMERGENCY:
            base_recommendation["emergency_intervention"] = [
                "🆘 EMERGENCY STOP: You've been in analysis for 1+ hours",
                "Step away from computer for 10 minutes",
                "When you return: pick ANY viable option and implement",
                "Perfect is the enemy of done",
            ]

        return base_recommendation

    def check_text_for_loop_patterns(
        self, text: str, context: str = ""
    ) -> Optional[LoopPattern]:
        """
        Analyze text content for doom loop language patterns.

        This can be used standalone or integrated into existing text analysis tools.
        """
        full_text = f"{text} {context}".lower()

        # Check for analysis paralysis language
        paralysis_indicators = [
            r"we need to (?:decide|choose|figure out|analyze|evaluate)",
            r"should we (?:also )?(?:use|implement|go with|consider)",
            r"\b(?:comparing|evaluating|analyzing)\b",
            r"on the other hand",
            r"but then again",
            r"however, we could also",
            r"what if we (?:instead|also|additionally)",
            r"pros and cons of",
            r"trade-?offs? (?:of|between|for)",
        ]

        paralysis_count = sum(
            1 for pattern in paralysis_indicators if re.search(pattern, full_text)
        )

        # Check for decision cycling language
        cycling_indicators = [
            r"(?:back to|returning to|revisiting) (?:the|our) (?:original|previous)",
            r"(?:again|once more|another) (?:look|approach|consideration)",
            r"(?:maybe|perhaps|potentially) we should reconsider",
            r"(?:actually|wait|hold on), what about",
        ]

        cycling_count = sum(
            1 for pattern in cycling_indicators if re.search(pattern, full_text)
        )

        # Check for overthinking patterns
        overthinking_indicators = [
            r"(?:complex|complicated|sophisticated) (?:solution|approach|architecture)",
            r"(?:edge case|corner case|what if) (?:scenario|situation)",
            r"(?:future|scale|enterprise|production) (?:proof|ready|considerations)",
            r"(?:architecture|design) (?:patterns?|principles?)",
            r"(?:best practice|industry standard|proper way)",
        ]

        overthinking_count = sum(
            1 for pattern in overthinking_indicators if re.search(pattern, full_text)
        )

        # Calculate severity based on indicators
        total_indicators = paralysis_count + cycling_count + overthinking_count

        positive_signals = self._count_positive_progress_signals(full_text)

        # Strong evidence of action orientation should suppress mild signals
        if positive_signals >= 3 and total_indicators <= 4:
            return None

        adjusted_indicators = total_indicators

        if positive_signals >= 2:
            adjusted_indicators = max(0, adjusted_indicators - 1)
        if positive_signals >= 4:
            adjusted_indicators = max(0, adjusted_indicators - 1)

        if adjusted_indicators >= 5:
            severity = LoopSeverity.CRITICAL
        elif adjusted_indicators >= 3:
            severity = LoopSeverity.WARNING
        elif adjusted_indicators >= 2:
            severity = LoopSeverity.CAUTION
        else:
            return None

        # Generate evidence
        evidence = []
        if paralysis_count >= 2:
            evidence.append(
                f"Analysis paralysis language detected ({paralysis_count} indicators)"
            )
        if cycling_count >= 1:
            evidence.append(
                f"Decision cycling patterns detected ({cycling_count} indicators)"
            )
        if overthinking_count >= 2:
            evidence.append(
                f"Overthinking patterns detected ({overthinking_count} indicators)"
            )

        return LoopPattern(
            pattern_type="text_analysis_paralysis",
            severity=severity,
            duration_minutes=0,  # Text analysis doesn't have duration
            evidence=evidence,
            topic="decision_making",
            intervention_suggestions=self._get_text_based_interventions(severity),
            time_wasted_estimate="Estimated analysis time: 15-30 minutes",
        )

    def get_session_health_report(self) -> Dict[str, Any]:
        """Get a comprehensive health report for the current session"""
        if not self.current_session:
            return {
                "status": "no_active_session",
                "doom_loop_detected": False,
                "health_score": 100,
                "recommendations": None,
            }

        loop_pattern = self.analyze_current_session()
        status = "doom_loop_detected" if loop_pattern else "healthy_session"

        return {
            "status": status,
            "session_id": self.current_session.session_id,
            "duration_minutes": self.current_session.session_duration_minutes,
            "total_mcp_calls": len(self.current_session.mcp_calls),
            "unique_tools_used": len(
                set(call["tool_name"] for call in self.current_session.mcp_calls)
            ),
            "topics_discussed": len(self.current_session.topics_discussed),
            "most_used_tools": self._get_top_used_tools(),
            "doom_loop_detected": loop_pattern is not None,
            "loop_pattern": loop_pattern.pattern_type if loop_pattern else None,
            "severity": loop_pattern.severity.value if loop_pattern else "none",
            "health_score": self._calculate_health_score(),
            "recommendations": (
                self.get_intervention_recommendation(loop_pattern)
                if loop_pattern
                else None
            ),
        }

    def _check_temporal_patterns(self) -> Optional[LoopPattern]:
        """Check for time-based doom loop patterns"""
        duration = self.current_session.session_duration_minutes

        if duration >= 60:
            return LoopPattern(
                pattern_type="extended_session",
                severity=LoopSeverity.EMERGENCY,
                duration_minutes=duration,
                evidence=[
                    f"Session running for {duration} minutes without clear progress"
                ],
                topic="time_management",
                intervention_suggestions=[
                    "Take immediate break",
                    "Implement simplest working solution",
                    "Set hard decision deadline (15 minutes)",
                ],
                time_wasted_estimate=f"Potential waste: {max(0, duration - 30)} minutes",
            )
        elif duration >= 30:
            return LoopPattern(
                pattern_type="long_session",
                severity=LoopSeverity.CRITICAL,
                duration_minutes=duration,
                evidence=[
                    f"Extended session ({duration} minutes) suggests analysis paralysis"
                ],
                topic="session_management",
                intervention_suggestions=[
                    "Make decision in next 10 minutes",
                    "Choose simplest viable option",
                    "Start prototyping immediately",
                ],
                time_wasted_estimate=f"Risk: {duration - 20} minutes beyond productive threshold",
            )
        elif duration >= 20:
            return LoopPattern(
                pattern_type="medium_session",
                severity=LoopSeverity.WARNING,
                duration_minutes=duration,
                evidence=[
                    f"Session length ({duration} minutes) approaching analysis paralysis"
                ],
                topic="time_awareness",
                intervention_suggestions=[
                    "Set 15-minute decision deadline",
                    "List concrete next steps",
                    "Avoid perfect solution trap",
                ],
                time_wasted_estimate="Approaching unproductive threshold",
            )

        return None

    def _check_repetition_patterns(self) -> Optional[LoopPattern]:
        """Check for repeated tool usage patterns"""
        repeated_tools = {
            tool: count
            for tool, count in self.current_session.repeated_calls.items()
            if count >= 3
        }

        if not repeated_tools:
            return None

        max_repetitions = max(repeated_tools.values())
        most_repeated_tool = max(repeated_tools.keys(), key=lambda t: repeated_tools[t])

        if max_repetitions >= 5:
            severity = LoopSeverity.CRITICAL
        elif max_repetitions >= 4:
            severity = LoopSeverity.WARNING
        else:
            severity = LoopSeverity.CAUTION

        return LoopPattern(
            pattern_type="tool_repetition",
            severity=severity,
            duration_minutes=self.current_session.session_duration_minutes,
            evidence=[
                f"Tool '{most_repeated_tool}' called {max_repetitions} times",
                f"Multiple tools repeated: {list(repeated_tools.keys())}",
            ],
            topic="analysis_loops",
            intervention_suggestions=[
                "Stop analyzing - start implementing",
                f"Avoid using {most_repeated_tool} again today",
                "Make decision based on current information",
            ],
            time_wasted_estimate=f"Repetitive analysis: ~{max_repetitions * 3} minutes",
        )

    def _check_decision_paralysis(self) -> Optional[LoopPattern]:
        """Check for decision paralysis patterns in conversation"""
        if len(self.current_session.decision_patterns) >= 3:
            return LoopPattern(
                pattern_type="decision_paralysis",
                severity=LoopSeverity.WARNING,
                duration_minutes=self.current_session.session_duration_minutes,
                evidence=[
                    f"Multiple decision-making discussions ({len(self.current_session.decision_patterns)})",
                    "Repeated 'should we' or 'what if' patterns",
                ],
                topic="decision_making",
                intervention_suggestions=[
                    "Pick any viable option and test it",
                    "Set 10-minute decision timer",
                    "Use coin flip for close decisions",
                ],
                time_wasted_estimate="Decision paralysis overhead: 10-20 minutes",
            )

        return None

    def _check_topic_cycling(self) -> Optional[LoopPattern]:
        """Check if the same topics are being discussed repeatedly"""
        if (
            len(self.current_session.topics_discussed) <= 2
            and len(self.current_session.mcp_calls) >= 5
        ):
            return LoopPattern(
                pattern_type="topic_cycling",
                severity=LoopSeverity.WARNING,
                duration_minutes=self.current_session.session_duration_minutes,
                evidence=[
                    f"Only {len(self.current_session.topics_discussed)} topics in {len(self.current_session.mcp_calls)} calls",
                    "Potential circular discussion pattern",
                ],
                topic="focus_management",
                intervention_suggestions=[
                    "Move to different topic or take action",
                    "List what you've already decided",
                    "Focus on one specific implementation step",
                ],
                time_wasted_estimate="Topic cycling overhead: 5-15 minutes",
            )

        return None

    def _extract_topics(self, content: str, context: str) -> Set[str]:
        """Extract main topics from content for tracking"""
        text = f"{content} {context}".lower()

        # Common technical topics
        topics = set()
        topic_patterns = {
            "authentication": r"\b(?:auth|login|jwt|oauth|token|session)\b",
            "database": r"\b(?:db|database|sql|postgres|mysql|mongo)\b",
            "api": r"\b(?:api|rest|graphql|endpoint|service)\b",
            "frontend": r"\b(?:react|vue|angular|ui|interface|component)\b",
            "deployment": r"\b(?:deploy|docker|k8s|kubernetes|aws|cloud)\b",
            "testing": r"\b(?:test|testing|unittest|pytest|jest)\b",
            "architecture": r"\b(?:architecture|design|pattern|structure)\b",
        }

        for topic, pattern in topic_patterns.items():
            if re.search(pattern, text):
                topics.add(topic)

        return topics

    def _extract_decision_language(self, content: str, context: str) -> Optional[str]:
        """Extract decision-related language patterns"""
        text = f"{content} {context}".lower()

        decision_patterns = [
            r"should we (?:use|implement|go with)",
            r"what if we (?:instead|also)",
            r"we need to (?:decide|choose)",
            r"comparing (?:options|approaches)",
        ]

        for pattern in decision_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _count_positive_progress_signals(self, full_text: str) -> int:
        """Count phrases that indicate concrete momentum and execution."""
        positive_signals = 0

        action_plan_patterns = [
            r"next steps?:",
            r"action plan:",
            r"roadmap:",
        ]

        if any(re.search(pattern, full_text) for pattern in action_plan_patterns):
            positive_signals += 1

        if (
            len(re.findall(r"step\s*\d+", full_text)) >= 2
            or len(re.findall(r"\b[0-9]+\.\s", full_text)) >= 2
        ):
            positive_signals += 1

        if re.search(
            r"\b(?:i['’]?m|we['’]?re|we are|i am)\s+(?:going with|choosing|picking|locking in)",
            full_text,
        ) or re.search(r"\bdecided to\b", full_text):
            positive_signals += 1

        if re.search(
            r"\b(today|tomorrow|this week|next week|by (?:end of )?(?:day|week))\b",
            full_text,
        ):
            positive_signals += 1

        if re.search(r"\bimplement(?:ation|ing)?\b", full_text) or re.search(
            r"\b(ship|deliver|deploy|launch|build)\b", full_text
        ):
            positive_signals += 1

        if re.search(r"\bvalidate\b.*\b(real|production|users|data)\b", full_text):
            positive_signals += 1

        return positive_signals

    def _get_top_used_tools(self) -> List[Dict[str, Any]]:
        """Get the most frequently used tools in this session"""
        tool_counts = self.current_session.repeated_calls
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"tool": tool, "count": count} for tool, count in sorted_tools[:5]]

    def _calculate_health_score(self) -> int:
        """Calculate a health score (0-100) for the current session"""
        if not self.current_session:
            return 100

        score = 100
        duration = self.current_session.session_duration_minutes

        # Penalize long sessions
        if duration > 30:
            score -= 40
        elif duration > 20:
            score -= 20
        elif duration > 15:
            score -= 10

        # Penalize tool repetition
        max_repetitions = (
            max(self.current_session.repeated_calls.values())
            if self.current_session.repeated_calls
            else 0
        )
        if max_repetitions > 5:
            score -= 30
        elif max_repetitions > 3:
            score -= 15

        # Penalize decision patterns
        if len(self.current_session.decision_patterns) > 3:
            score -= 20

        # Penalize topic cycling
        if (
            len(self.current_session.topics_discussed) <= 2
            and len(self.current_session.mcp_calls) >= 5
        ):
            score -= 15

        return max(0, score)

    def _severity_score(self, severity: LoopSeverity) -> int:
        """Convert severity to numeric score for comparison"""
        severity_scores = {
            LoopSeverity.NONE: 0,
            LoopSeverity.CAUTION: 1,
            LoopSeverity.WARNING: 2,
            LoopSeverity.CRITICAL: 3,
            LoopSeverity.EMERGENCY: 4,
        }
        return severity_scores.get(severity, 0)

    def _generate_intervention_message(self, loop_pattern: LoopPattern) -> str:
        """Generate a human-friendly intervention message"""
        messages = {
            LoopSeverity.CAUTION: f"⚠️ Heads up: You've been {loop_pattern.pattern_type.replace('_', ' ')} for {loop_pattern.duration_minutes} minutes. Consider making a decision soon.",
            LoopSeverity.WARNING: f"🚨 Warning: Detected {loop_pattern.pattern_type.replace('_', ' ')} pattern. Time to choose and move forward.",
            LoopSeverity.CRITICAL: f"🆘 Critical: You're in a {loop_pattern.pattern_type.replace('_', ' ')} loop. Take action now to avoid time waste.",
            LoopSeverity.EMERGENCY: f"🚨 EMERGENCY: {loop_pattern.duration_minutes}+ minutes in analysis paralysis. STOP and implement something NOW.",
        }
        return messages.get(loop_pattern.severity, "Unknown severity level detected.")

    def _suggest_time_budget(self, loop_pattern: LoopPattern) -> str:
        """Suggest time budgets based on pattern severity"""
        budgets = {
            LoopSeverity.CAUTION: "Budget: 10 more minutes for decision, then implement",
            LoopSeverity.WARNING: "Budget: 5 more minutes for decision, then start coding",
            LoopSeverity.CRITICAL: "Budget: 2 minutes to pick option, start immediately",
            LoopSeverity.EMERGENCY: "Budget: ZERO - implement any viable solution now",
        }
        return budgets.get(loop_pattern.severity, "Set a firm time limit")

    def _generate_decision_forcing_questions(
        self, loop_pattern: LoopPattern
    ) -> List[str]:
        """Generate questions to force decision-making"""
        return [
            "What's the simplest solution that solves 80% of the problem?",
            "What would you implement if you only had 2 hours left?",
            "Which option would you choose if perfect wasn't an option?",
            "What's the worst case if you pick the 'wrong' option?",
            "Can you validate your choice with real usage in the next hour?",
        ]

    def _get_text_based_interventions(self, severity: LoopSeverity) -> List[str]:
        """Get intervention suggestions based on text analysis severity"""
        base_suggestions = [
            "Pick the simplest option that works",
            "Set 15-minute decision timer",
            "Start with MVP, iterate later",
        ]

        if severity == LoopSeverity.CRITICAL:
            base_suggestions.extend(
                [
                    "STOP analyzing - start implementing",
                    "Use coin flip for close decisions",
                    "Perfect is the enemy of done",
                ]
            )

        return base_suggestions

    def _initialize_detection_patterns(self) -> Dict[str, Any]:
        """Initialize doom loop detection patterns"""
        return {
            "temporal_thresholds": {
                "caution": 15,  # minutes
                "warning": 20,
                "critical": 30,
                "emergency": 60,
            },
            "repetition_thresholds": {
                "caution": 3,  # repeated tool calls
                "warning": 4,
                "critical": 5,
            },
            "decision_paralysis_threshold": 3,  # number of decision patterns
            "topic_cycling_threshold": 2,  # unique topics with 5+ calls
        }

    def _initialize_interventions(self) -> Dict[str, List[str]]:
        """Initialize intervention strategies"""
        return {
            "time_management": [
                "Set hard deadlines for decisions",
                "Use timeboxing for analysis",
                "Take breaks every 25 minutes",
            ],
            "decision_making": [
                "Use decision matrices for complex choices",
                "Apply 80/20 rule - pick good enough",
                "Consider reversibility of decisions",
            ],
            "implementation_focus": [
                "Start with simplest working version",
                "Validate with real users quickly",
                "Iterate based on actual feedback",
            ],
        }


# Global detector instance for MCP integration
_doom_loop_detector = None


def get_doom_loop_detector() -> DoomLoopDetector:
    """Get or create the global doom loop detector instance"""
    global _doom_loop_detector
    if _doom_loop_detector is None:
        _doom_loop_detector = DoomLoopDetector()
    return _doom_loop_detector
