from src.vibe_check.mentor.response_relevance import ResponseRelevanceValidator


def test_rejects_irrelevant_response_for_architecture_query() -> None:
    validator = ResponseRelevanceValidator(minimum_score=0.2, minimum_matches=1)

    query = "Need tier1 vs tier2 architecture guidance for enterprise regions"
    response = "For Stripe MVP: Start with their hosted checkout page. Skip building payment forms initially."
    context = {
        "problem_type": ["architecture"],
        "decision_points": ["tier1 vs tier2 regions"],
    }

    result = validator.score(query=query, response=response, context=context)

    assert not result.passed
    assert result.matched_terms == []
    assert "tier1" in result.considered_terms
    assert "tier2" in result.considered_terms


def test_accepts_response_that_mentions_key_terms() -> None:
    validator = ResponseRelevanceValidator(minimum_score=0.2, minimum_matches=1)

    query = "Need tier1 vs tier2 architecture guidance for enterprise regions"
    response = "Tier1 regions should run on the primary cluster while tier2 can replicate asynchronously."
    context = {
        "problem_type": ["architecture"],
        "decision_points": ["tier1 vs tier2 regions"],
    }

    result = validator.score(query=query, response=response, context=context)

    assert result.passed
    assert "tier1" in result.matched_terms
    assert "tier2" in result.matched_terms


def test_passes_when_no_terms_available() -> None:
    validator = ResponseRelevanceValidator()

    query = "?"
    response = "General debugging tips go here."
    context = {}

    result = validator.score(query=query, response=response, context=context)

    assert result.passed
    assert result.score == 1.0
