import logging
import secrets
from typing import Dict, Any, Optional
from vibe_check.tools.vibe_mentor_enhanced import get_enhanced_mentor_engine
from vibe_check.tools.vibe_mentor import _generate_summary
from vibe_check.core.vibe_coaching import VibeCoachingFramework, CoachingTone

logger = logging.getLogger(__name__)


def get_reasoning_engine():
    """Returns the enhanced mentor engine instance with response relevance validation."""
    return get_enhanced_mentor_engine()


async def generate_response(
    engine,
    query: str,
    context: Optional[str],
    session_id: Optional[str],
    reasoning_depth: str,
    continue_session: bool,
    mode: str,
    phase: str,
    analysis_result: Dict[str, Any],
    workspace_warning: str,
    ctx: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generates the final response from the mentor."""

    vibe_level = analysis_result["vibe_level"]
    pattern_confidence = analysis_result["pattern_confidence"]
    detected_patterns = analysis_result["detected_patterns"]

    if mode == "interrupt":
        interrupt_needed = pattern_confidence > 0.7
        if interrupt_needed and detected_patterns:
            primary_pattern = detected_patterns[0]
            interrupt_response = engine.generate_interrupt_intervention(
                query=query,
                phase=phase,
                primary_pattern=primary_pattern,
                pattern_confidence=pattern_confidence,
            )
            return {
                "status": "success",
                "mode": "interrupt",
                "interrupt": True,
                "question": interrupt_response["question"],
                "severity": interrupt_response["severity"],
                "suggestion": interrupt_response["suggestion"],
                "session_id": session_id or f"interrupt-{secrets.token_hex(4)}",
                "pattern_detected": primary_pattern.get("pattern_type", "unknown"),
                "confidence": pattern_confidence,
                "phase": phase,
                "can_escalate": True,
                "escalation_hint": "Use mode='standard' with same session_id for full analysis",
            }
        else:
            return {
                "status": "success",
                "mode": "interrupt",
                "interrupt": False,
                "proceed": True,
                "affirmation": _get_phase_affirmation(phase, query),
                "confidence": pattern_confidence,
                "phase": phase,
            }

    if continue_session and session_id and session_id in engine.sessions:
        session = engine.sessions[session_id]
        session.topic = query
        logger.info(f"Continuing session {session_id} with new topic: {query}")
    else:
        if session_id and not continue_session:
            session = engine.create_session(topic=query, session_id=session_id)
            logger.info(f"Created new session with provided ID: {session_id}")
        else:
            session = engine.create_session(topic=query)
            logger.info(f"Created new session with generated ID: {session.session_id}")

    contribution_counts = {"quick": 1, "standard": 2, "comprehensive": 3}
    num_contributions = contribution_counts.get(reasoning_depth, 2)

    for i in range(num_contributions):
        if i < len(session.personas):
            persona = session.personas[i]
            session.active_persona_id = persona.id

            contribution = await engine.generate_contribution(
                session=session,
                persona=persona,
                detected_patterns=detected_patterns,
                context=context,
                project_context=analysis_result.get("project_context"),
                file_contexts=analysis_result.get("file_contexts"),
                ctx=ctx,  # Pass FastMCP context for response relevance validation
            )

            session.contributions.append(contribution)

            if reasoning_depth == "comprehensive" and i < num_contributions - 1:
                engine.advance_stage(session)

    synthesis = engine.synthesize_session(session)
    engine.cleanup_old_sessions()

    coaching_framework = VibeCoachingFramework()
    coaching_recs = coaching_framework.generate_coaching_recommendations(
        vibe_level=vibe_level,
        detected_patterns=[],
        issue_context={"query": query},
        tone=CoachingTone.ENCOURAGING,
    )

    response = {
        "status": "success",
        "immediate_feedback": {
            "summary": _generate_summary(vibe_level, detected_patterns, synthesis),
            "confidence": pattern_confidence,
            "detected_patterns": [p["pattern_type"] for p in detected_patterns],
            "vibe_level": vibe_level,
        },
        "collaborative_insights": {
            "consensus": synthesis["consensus_points"],
            "perspectives": {
                contrib.persona_id: {
                    "message": contrib.content,
                    "type": contrib.type,
                    "confidence": contrib.confidence,
                }
                for contrib in session.contributions
            },
            "key_insights": synthesis["key_insights"],
            "concerns": synthesis["primary_concerns"],
            "recommendations": synthesis["recommendations"],
        },
        "coaching_guidance": {
            "primary_recommendation": (
                coaching_recs[0].title
                if coaching_recs
                else "Proceed with implementation"
            ),
            "action_steps": coaching_recs[0].action_items[:3] if coaching_recs else [],
            "prevention_checklist": (
                coaching_recs[0].prevention_checklist[:3] if coaching_recs else []
            ),
        },
        "session_info": {
            "session_id": session.session_id,
            "stage": session.stage,
            "iteration": session.iteration,
            "can_continue": session.next_contribution_needed,
        },
        "reasoning_depth": reasoning_depth,
        "formatted_output": engine.format_session_output(session) + workspace_warning,
    }

    logger.info(response["formatted_output"])

    return response


def _get_phase_affirmation(phase: str, query: str) -> str:
    """Generate phase-specific affirmation when no interrupt is needed"""
    phase_affirmations = {
        "planning": [
            "Good choice - using standard tools",
            "Solid approach - keep it simple",
            "Great! Following established patterns",
        ],
        "implementation": [
            "Clean implementation - well done",
            "Following best practices - excellent",
            "Standard approach confirmed - proceed",
        ],
        "review": [
            "Implementation looks clean",
            "Matches requirements well",
            "Ready for next steps",
        ],
    }

    if "pandas" in query.lower() or "standard" in query.lower():
        return phase_affirmations[phase][0]
    elif "official" in query.lower() or "sdk" in query.lower():
        return phase_affirmations[phase][1]
    else:
        return phase_affirmations[phase][2]
