"""
Doom Loop Analysis MCP Tools

Real-time MCP tools for detecting AI doom loops and analysis paralysis.
These tools integrate seamlessly with the development workflow to provide
automatic intervention suggestions when developers get stuck in unproductive
AI conversation cycles.

MCP Integration Features:
- Automatic session tracking across tool calls
- Passive doom loop detection during normal workflow
- Contextual warnings in existing tool responses
- Standalone analysis tools for explicit checking
- Intervention recommendations with concrete next steps
"""

import logging
import time
from typing import Dict, Any, Optional

from vibe_check.core.doom_loop_detector import (
    get_doom_loop_detector,
    LoopSeverity,
    LoopPattern,
)

logger = logging.getLogger(__name__)

# Global session tracking state
_session_tracker = {"active": False, "last_call_time": None, "session_started": None}


def track_mcp_call(
    tool_name: str,
    content: str = "",
    context: str = "",
    auto_start_session: bool = True,
) -> None:
    """
    Track an MCP tool call for doom loop detection.

    This function should be called by all MCP tools to enable automatic
    doom loop detection. It's lightweight and won't impact tool performance.

    Args:
        tool_name: Name of the MCP tool being called
        content: Main content being analyzed
        context: Additional context information
        auto_start_session: Whether to automatically start session tracking
    """
    global _session_tracker

    detector = get_doom_loop_detector()

    # Auto-start session if needed
    if auto_start_session and not detector.current_session:
        detector.start_session()
        _session_tracker["active"] = True
        _session_tracker["session_started"] = time.time()

    # Track the call
    if detector.current_session:
        detector.track_mcp_call(
            tool_name=tool_name,
            content=content,
            context=context,
            metadata={"auto_tracked": True},
        )
        _session_tracker["last_call_time"] = time.time()


def get_doom_loop_context_for_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get doom loop context that can be embedded in tool responses.

    This provides contextual doom loop warnings that can be automatically
    included in LLM tool responses without requiring explicit user calls.

    Returns:
        Dictionary with doom loop context or None if no issues detected
    """
    detector = get_doom_loop_detector()

    if not detector.current_session:
        return None

    # Check for doom loops
    loop_pattern = detector.analyze_current_session()

    if not loop_pattern:
        return None

    # Only provide context for certain severity levels
    if loop_pattern.severity in [
        LoopSeverity.WARNING,
        LoopSeverity.CRITICAL,
        LoopSeverity.EMERGENCY,
    ]:
        return {
            "doom_loop_detected": True,
            "severity": loop_pattern.severity.value,
            "warning_message": _format_contextual_warning(loop_pattern),
            "quick_suggestions": loop_pattern.intervention_suggestions[
                :2
            ],  # Top 2 suggestions
            "should_show_warning": True,
        }

    return None


def analyze_text_for_doom_loops(
    text: str, context: str = "", tool_name: str = "text_analysis"
) -> Dict[str, Any]:
    """
    Analyze text content for doom loop patterns.

    This can be called standalone or integrated into existing text analysis tools
    to detect analysis paralysis language patterns.

    Args:
        text: Text content to analyze
        context: Additional context
        tool_name: Name of calling tool (for tracking)

    Returns:
        Doom loop analysis results
    """
    detector = get_doom_loop_detector()

    # Track this analysis call
    track_mcp_call(tool_name, text, context)

    # Analyze text for loop patterns
    text_pattern = detector.check_text_for_loop_patterns(text, context)

    # Also check session patterns
    session_pattern = detector.analyze_current_session()

    # Choose the most severe pattern
    primary_pattern = None
    if text_pattern and session_pattern:
        primary_pattern = (
            text_pattern
            if detector._severity_score(text_pattern.severity)
            > detector._severity_score(session_pattern.severity)
            else session_pattern
        )
    elif text_pattern:
        primary_pattern = text_pattern
    elif session_pattern:
        primary_pattern = session_pattern

    if primary_pattern:
        return {
            "status": "doom_loop_detected",
            "pattern_type": primary_pattern.pattern_type,
            "severity": primary_pattern.severity.value,
            "evidence": primary_pattern.evidence,
            "intervention": detector.get_intervention_recommendation(primary_pattern),
            "analysis_type": "text_and_session_analysis",
        }
    else:
        return {
            "status": "healthy_analysis",
            "message": "No doom loop patterns detected",
            "suggestions": [
                "Continue with current approach",
                "Consider setting time limits for decisions",
                "Focus on concrete next steps",
            ],
        }


def get_session_health_analysis() -> Dict[str, Any]:
    """
    Get comprehensive health analysis for the current MCP session.

    This provides a detailed view of the current session state and any
    detected doom loop patterns.

    Returns:
        Comprehensive session health report
    """
    detector = get_doom_loop_detector()

    if not detector.current_session:
        return {
            "status": "no_active_session",
            "message": "No active MCP session found",
            "suggestion": "Session tracking will start automatically with your next tool call",
        }

    health_report = detector.get_session_health_report()

    # Add user-friendly formatting
    if health_report["doom_loop_detected"]:
        health_report["user_message"] = _format_health_message(health_report)
        health_report["action_required"] = health_report["severity"] in [
            "critical",
            "emergency",
        ]
    else:
        health_report["user_message"] = (
            f"✅ Session health: Good ({health_report['health_score']}/100)"
        )
        health_report["action_required"] = False

    return health_report


def force_doom_loop_intervention() -> Dict[str, Any]:
    """
    Force an immediate doom loop intervention.

    This can be called when the user explicitly wants to break out of
    analysis paralysis or when external systems detect problematic patterns.

    Returns:
        Emergency intervention recommendations
    """
    detector = get_doom_loop_detector()

    # Create emergency intervention regardless of detected patterns
    emergency_pattern = LoopPattern(
        pattern_type="forced_intervention",
        severity=LoopSeverity.EMERGENCY,
        duration_minutes=(
            detector.current_session.session_duration_minutes
            if detector.current_session
            else 0
        ),
        evidence=["Manual intervention requested"],
        topic="productivity",
        intervention_suggestions=[
            "🚨 IMMEDIATE ACTION REQUIRED",
            "Pick ANY viable solution and start implementing",
            "Set 5-minute timer for final decision",
            "Ignore perfect solutions - focus on working solutions",
        ],
        time_wasted_estimate="Unknown - intervention requested",
    )

    intervention = detector.get_intervention_recommendation(emergency_pattern)

    return {
        "status": "emergency_intervention_activated",
        "message": "🆘 Emergency productivity intervention activated",
        "intervention": intervention,
        "mandatory_actions": [
            "Stop all analysis immediately",
            "Choose simplest viable option",
            "Start implementation in next 5 minutes",
            "Validate with real usage, not more planning",
        ],
    }


def reset_session_tracking() -> Dict[str, Any]:
    """
    Reset session tracking (useful after implementing solutions).

    This allows starting fresh after breaking out of doom loops or
    completing implementation milestones.

    Returns:
        Reset confirmation
    """
    global _session_tracker

    detector = get_doom_loop_detector()

    old_session_info = {
        "duration": (
            detector.current_session.session_duration_minutes
            if detector.current_session
            else 0
        ),
        "calls": (
            len(detector.current_session.mcp_calls) if detector.current_session else 0
        ),
    }

    # Clear current session state; next tool call will auto-start a new session
    detector.current_session = None

    _session_tracker = {
        "active": False,
        "last_call_time": None,
        "session_started": None,
    }

    return {
        "status": "session_reset_complete",
        "new_session_id": None,
        "previous_session": old_session_info,
        "message": "✅ Fresh start! Session tracking will resume on your next tool call.",
    }


def _format_contextual_warning(loop_pattern: LoopPattern) -> str:
    """Format a contextual warning for embedding in tool responses"""
    warnings = {
        LoopSeverity.WARNING: f"⚠️ **Analysis Alert**: {loop_pattern.pattern_type.replace('_', ' ').title()} detected. Consider making a decision soon.",
        LoopSeverity.CRITICAL: f"🚨 **Productivity Warning**: You've been in {loop_pattern.pattern_type.replace('_', ' ')} for {loop_pattern.duration_minutes}+ minutes. Time to choose and implement.",
        LoopSeverity.EMERGENCY: f"🆘 **EMERGENCY**: {loop_pattern.duration_minutes}+ minutes in analysis paralysis. STOP and implement something NOW.",
    }

    base_warning = warnings.get(loop_pattern.severity, "Doom loop detected")

    # Add first intervention suggestion
    if loop_pattern.intervention_suggestions:
        base_warning += f" Suggestion: {loop_pattern.intervention_suggestions[0]}"

    return base_warning


def _format_health_message(health_report: Dict[str, Any]) -> str:
    """Format user-friendly health message"""
    severity = health_report["severity"]
    duration = health_report["duration_minutes"]
    health_score = health_report["health_score"]

    if severity == "emergency":
        return f"🆘 EMERGENCY: {duration}+ minutes in analysis paralysis. Take immediate action!"
    elif severity == "critical":
        return f"🚨 CRITICAL: Productivity crisis detected. Health score: {health_score}/100"
    elif severity == "warning":
        return (
            f"⚠️ WARNING: Analysis patterns detected. Health score: {health_score}/100"
        )
    else:
        return f"ℹ️ CAUTION: Consider time limits. Health score: {health_score}/100"


# Integration helpers for existing tools
def enhance_tool_response_with_doom_loop_context(
    tool_response: Dict[str, Any], tool_name: str, content_analyzed: str = ""
) -> Dict[str, Any]:
    """
    Enhance an existing tool response with doom loop context.

    This can be used by existing MCP tools to automatically include
    doom loop warnings without changing their core functionality.

    Args:
        tool_response: Original tool response
        tool_name: Name of the tool
        content_analyzed: Content that was analyzed by the tool

    Returns:
        Enhanced response with doom loop context if applicable
    """
    # Track this tool call
    track_mcp_call(tool_name, content_analyzed)

    # Get doom loop context
    doom_context = get_doom_loop_context_for_tool(tool_name)

    if doom_context and doom_context["should_show_warning"]:
        # Create enhanced response
        enhanced_response = tool_response.copy()

        # Add doom loop section to response
        enhanced_response["doom_loop_alert"] = {
            "warning": doom_context["warning_message"],
            "suggestions": doom_context["quick_suggestions"],
            "severity": doom_context["severity"],
        }

        # For LLM responses, add to the text output
        if "analysis" in enhanced_response or "message" in enhanced_response:
            warning_text = (
                f"\n\n---\n## ⚠️ Productivity Alert\n{doom_context['warning_message']}\n"
            )

            if "analysis" in enhanced_response:
                enhanced_response["analysis"] += warning_text
            elif "message" in enhanced_response:
                enhanced_response["message"] += warning_text

        return enhanced_response

    return tool_response
