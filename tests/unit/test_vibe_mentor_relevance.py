import pytest
from unittest.mock import AsyncMock, MagicMock

from vibe_check.tools.vibe_mentor_enhanced import EnhancedVibeMentorEngine
from vibe_check.mentor.models.persona import PersonaData
from vibe_check.strategies.response_strategies import TechnicalContext
from vibe_check.mentor.response_relevance import ResponseRelevanceValidator


def _build_persona(persona_id: str) -> PersonaData:
    return PersonaData(
        id=persona_id,
        name="Test Persona",
        expertise=["Testing"],
        background="Testing background",
        perspective="Pragmatic",
        biases=[],
        communication={"style": "Direct", "tone": "Blunt"},
    )


def _tech_context(decision_point: str) -> TechnicalContext:
    return TechnicalContext(
        technologies=[],
        frameworks=[],
        patterns=[],
        problem_type="architecture",
        specific_features=[],
        decision_points=[decision_point],
    )


@pytest.mark.asyncio
async def test_irrelevant_static_response_triggers_dynamic_fallback() -> None:
    base_engine = MagicMock()
    engine = EnhancedVibeMentorEngine(base_engine, enable_mcp_sampling=False)
    engine.enable_mcp_sampling = True
    engine.hybrid_router = object()
    engine.relevance_validator = ResponseRelevanceValidator(minimum_score=0.2)

    dynamic_result = ("insight", "Dynamic fallback guidance", 0.9)
    engine._try_dynamic_generation = AsyncMock(side_effect=[None, dynamic_result])

    engine.enhanced_reasoning.generate_senior_engineer_response = MagicMock(
        return_value=(
            "suggestion",
            "For Stripe MVP: start with hosted checkout pages.",
            0.8,
        )
    )

    persona = _build_persona("senior_engineer")
    tech_context = _tech_context("tier1 vs tier2 regions")

    result = await engine._reason_as_persona_enhanced(
        persona=persona,
        topic="Need tier1 vs tier2 architecture guidance",
        tech_context=tech_context,
        patterns=[],
        previous_contributions=[],
        ctx=MagicMock(),
    )

    assert result == dynamic_result
    assert engine._try_dynamic_generation.await_count == 2
    forced_call = engine._try_dynamic_generation.await_args_list[1]
    assert forced_call.kwargs["force_decision"] is True


@pytest.mark.asyncio
async def test_relevant_static_response_is_returned() -> None:
    base_engine = MagicMock()
    engine = EnhancedVibeMentorEngine(base_engine, enable_mcp_sampling=False)
    engine.enable_mcp_sampling = True
    engine.hybrid_router = object()
    engine.relevance_validator = ResponseRelevanceValidator(minimum_score=0.2)

    engine._try_dynamic_generation = AsyncMock(side_effect=[None])

    static_response = (
        "suggestion",
        "Prioritize tier1 regions on primary cluster; tier2 stays async.",
        0.85,
    )
    engine.enhanced_reasoning.generate_senior_engineer_response = MagicMock(
        return_value=static_response
    )

    persona = _build_persona("senior_engineer")
    tech_context = _tech_context("tier1 vs tier2 regions")

    result = await engine._reason_as_persona_enhanced(
        persona=persona,
        topic="Need tier1 vs tier2 architecture guidance",
        tech_context=tech_context,
        patterns=[],
        previous_contributions=[],
        ctx=MagicMock(),
    )

    assert result == static_response
    assert engine._try_dynamic_generation.await_count == 1
