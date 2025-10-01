import logging
from typing import Dict, Any
from vibe_check.server.core import mcp
from vibe_check.tools.doom_loop_analysis import analyze_text_for_doom_loops, get_session_health_analysis, force_doom_loop_intervention, reset_session_tracking as reset_session

logger = logging.getLogger(__name__)

def register_productivity_tools(mcp_instance):
    """Registers productivity tools with the MCP server."""
    mcp_instance.add_tool(analyze_doom_loops)
    mcp_instance.add_tool(session_health_check)
    mcp_instance.add_tool(productivity_intervention)
    mcp_instance.add_tool(reset_session_tracking)

@mcp.tool()
def analyze_doom_loops(
    content: str,
    context: str = "",
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    🔄 AI Doom Loop Detection and Analysis Paralysis Prevention.
    
    Detects when developers get stuck in unproductive AI conversation loops,
    decision paralysis, and endless analysis cycles. Provides immediate
    intervention suggestions to restore development momentum.
    
    Features:
    - 🕵️ Pattern Detection: Identifies analysis paralysis language patterns
    - ⏱️ Session Analysis: Monitors MCP session for time-sink behaviors
    - 🚨 Real-time Alerts: Warns about productivity-killing cycles
    - 💡 Intervention: Concrete steps to break out of doom loops
    
    Use this tool for: "analyze for analysis paralysis", "check for doom loops", "productivity check"
    
    Args:
        content: Text content to analyze (issue, PR, conversation)
        context: Additional context (comments, related discussions)
        analysis_type: Type of analysis (quick/standard/comprehensive)
        
    Returns:
        Doom loop analysis with intervention recommendations
    """
    logger.info(f"Doom loop analysis requested for {len(content)} characters")
    
    try:
        
        # Analyze text for doom loop patterns
        text_analysis = analyze_text_for_doom_loops(content, context, "analyze_doom_loops")
        
        # Get session health context
        session_health = get_session_health_analysis()
        
        # Combine results
        result = {
            "status": "analysis_complete",
            "text_analysis": text_analysis,
            "session_health": session_health,
            "analysis_type": "doom_loop_detection"
        }
        
        # Determine overall recommendation
        text_severity = text_analysis.get("severity", "none")
        session_severity = session_health.get("severity", "none")
        
        severity_scores = {"none": 0, "caution": 1, "warning": 2, "critical": 3, "emergency": 4}
        overall_severity = max(severity_scores.get(text_severity, 0), severity_scores.get(session_severity, 0))
        
        if overall_severity >= 3:
            result["urgent_intervention"] = {
                "message": "🚨 CRITICAL: Doom loop detected - immediate action required",
                "actions": [
                    "STOP all analysis immediately",
                    "Pick ANY viable option from current discussion",
                    "Set 10-minute implementation timer",
                    "Focus on shipping, not perfecting"
                ]
            }
        elif overall_severity >= 2:
            result["intervention_suggested"] = {
                "message": "⚠️ WARNING: Analysis paralysis patterns detected",
                "actions": [
                    "Set 15-minute decision deadline",
                    "Choose simplest working solution",
                    "Start implementation this hour"
                ]
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Doom loop analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "fallback_guidance": [
                "If stuck in analysis: Set 15-minute timer and make any decision",
                "Perfect is the enemy of done - ship something working",
                "Take 10-minute break and return with implementation focus"
            ]
        }

@mcp.tool()
def session_health_check() -> Dict[str, Any]:
    """
    🏥 MCP Session Health and Productivity Analysis.
    
    Provides comprehensive health analysis of your current MCP session to detect
    doom loops, analysis paralysis, and productivity anti-patterns. Monitors
    tool usage patterns, session duration, and decision-making cycles.
    
    Features:
    - 📊 Health Score: 0-100 productivity score for current session
    - ⏱️ Time Analysis: Session duration and time allocation patterns
    - 🔄 Pattern Detection: Repeated tool usage and topic cycling
    - 📈 Trend Analysis: Productivity trajectory and improvement suggestions
    
    Use this tool for: "check my productivity", "session health", "am I in a loop?"
    
    Returns:
        Comprehensive session health report with recommendations
    """
    logger.info("Session health check requested")
    
    try:
        
        health_report = get_session_health_analysis()
        
        # Add user-friendly summary
        if health_report["status"] == "no_active_session":
            return {
                "status": "no_session",
                "message": "✅ No active session - fresh start available",
                "recommendation": "Session tracking will begin with your next tool call"
            }
        
        health_score = health_report.get("health_score", 100)
        duration = health_report.get("duration_minutes", 0)
        
        # Generate health assessment
        if health_score >= 90:
            health_emoji = "🟢"
            health_status = "Excellent"
        elif health_score >= 70:
            health_emoji = "🟡"
            health_status = "Good"
        elif health_score >= 50:
            health_emoji = "🟠"
            health_status = "Caution"
        else:
            health_emoji = "🔴"
            health_status = "Critical"
        
        # Add assessment to report
        health_report["health_assessment"] = {
            "emoji": health_emoji,
            "status": health_status,
            "summary": f"{health_emoji} {health_status} ({health_score}/100) - {duration}min session"
        }
        
        return health_report
        
    except Exception as e:
        logger.error(f"Session health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Health check failed - assume session is healthy and continue working"
        }

@mcp.tool()
def productivity_intervention() -> Dict[str, Any]:
    """
    🆘 Emergency Productivity Intervention and Loop Breaking.
    
    Forces immediate productivity intervention to break out of analysis paralysis,
    doom loops, and decision cycles. Use when you recognize you're stuck or
    when other tools suggest critical intervention is needed.
    
    Features:
    - 🚨 Emergency Stop: Immediate halt to analysis and planning
    - ⚡ Action Forcing: Concrete next steps with time limits
    - 🎯 Decision Support: Simplified decision-making frameworks
    - 🔄 Momentum Reset: Fresh start with implementation focus
    
    Use this tool for: "I'm stuck", "break the loop", "emergency productivity", "force decision"
    
    Returns:
        Emergency intervention with mandatory next steps
    """
    logger.info("Productivity intervention requested")
    
    try:
        
        intervention = force_doom_loop_intervention()
        
        # Add additional emergency guidance
        intervention["emergency_protocol"] = {
            "step_1": "🛑 STOP: Close this analysis immediately",
            "step_2": "⏰ Set 5-minute timer for final decision",
            "step_3": "✅ Pick FIRST viable option from discussion",
            "step_4": "🚀 Start implementing immediately (no more planning)",
            "step_5": "📊 Validate with real usage within 1 hour"
        }
        
        intervention["mantras"] = [
            "Done is better than perfect",
            "Ship something, iterate everything",
            "Perfect is the enemy of shipped",
            "Start ugly, make it beautiful later"
        ]
        
        return intervention
        
    except Exception as e:
        logger.error(f"Productivity intervention failed: {e}")
        return {
            "status": "emergency_fallback",
            "message": "🆘 INTERVENTION ACTIVATED",
            "immediate_actions": [
                "STOP reading this - start implementing NOW",
                "Pick any solution that works",
                "Set 10-minute implementation timer",
                "Ship first, optimize later"
            ]
        }

@mcp.tool()
def reset_session_tracking() -> Dict[str, Any]:
    """
    🔄 Reset Session Tracking for Fresh Start.
    
    Resets MCP session tracking to start fresh after completing implementations,
    breaking out of doom loops, or reaching natural stopping points. Useful
    for beginning new tasks with clean productivity metrics.
    
    Features:
    - 🆕 Fresh Start: Clean session state for new tasks
    - 📊 Previous Summary: Report on completed session metrics
    - ⚡ Momentum Reset: Clear tracking for productivity restart
    - 🎯 Focus Renewal: Begin with implementation-first mindset
    
    Use this tool for: "fresh start", "reset tracking", "new session", "clean slate"
    
    Returns:
        Reset confirmation with previous session summary
    """
    logger.info("Session tracking reset requested")
    
    try:
        
        reset_result = reset_session()
        
        # Add motivational messaging
        reset_result["fresh_start_guidance"] = {
            "mindset": "🎯 Implementation-first approach",
            "time_budget": "⏰ Time-box decisions to 15 minutes max",
            "success_metrics": "📈 Measure progress by code shipped, not analysis depth",
            "remember": "🚀 Build fast, iterate faster"
        }
        
        return reset_result
        
    except Exception as e:
        logger.error(f"Session reset failed: {e}")
        return {
            "status": "manual_reset",
            "message": "✅ Consider this a fresh start - track your own productivity",
            "guidance": "Focus on implementation over analysis for next session"
        }
