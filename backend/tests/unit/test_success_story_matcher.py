from app.core.success_stories.matcher import SuccessStoryMatcher


def test_top_5_matches_returned() -> None:
    """Returns exactly 5 matches ordered by similarity score."""
    matcher = SuccessStoryMatcher()
    result = matcher.match(industry="saas", stage="seed", top_n=5)

    assert len(result.matches) == 5
    # Descending order
    scores = [m.similarity_score for m in result.matches]
    assert scores == sorted(scores, reverse=True)
    # All have names
    for m in result.matches:
        assert m.name
        assert m.similarity_score >= 0
        assert m.similarity_score <= 1.0


def test_similarity_based_on_attributes() -> None:
    """Same industry + stage → higher similarity than different industry."""
    matcher = SuccessStoryMatcher()

    saas_result = matcher.match(industry="saas", stage="growth", top_n=5)
    fintech_result = matcher.match(industry="fintech", stage="growth", top_n=5)

    # Top match for saas query should be a saas company
    saas_top = saas_result.matches[0]
    assert saas_top.industry == "saas"

    # Top match for fintech query should be a fintech company
    fintech_top = fintech_result.matches[0]
    assert fintech_top.industry == "fintech"

    # SaaS query top score should be relatively high
    assert saas_top.similarity_score > 0.2
