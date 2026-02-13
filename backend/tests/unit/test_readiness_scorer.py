import pytest

from app.core.scoring.readiness_scorer import InvestorReadinessScorer
from app.models.kg_entity import KGEntityStatus, KGEntityType
from app.schemas.brain import EntityResult


def _make_entity(
    entity_type: KGEntityType,
    name: str = "test",
    confidence: float = 0.8,
) -> EntityResult:
    return EntityResult(
        id="fake-id",
        type=entity_type,
        status=KGEntityStatus.CONFIRMED,
        data={"name": name},
        confidence=confidence,
        evidence_count=1,
    )


@pytest.fixture
def scorer() -> InvestorReadinessScorer:
    return InvestorReadinessScorer()


def test_full_readiness_score_above_80(scorer: InvestorReadinessScorer) -> None:
    """Venture with all KG entities and venture fields scores > 80."""
    entities = [
        _make_entity(KGEntityType.VENTURE, "MyStartup"),
        _make_entity(KGEntityType.PRODUCT, "SaaS Product"),
        _make_entity(KGEntityType.ICP, "SMB Owners"),
        _make_entity(KGEntityType.METRIC, "revenue"),
        _make_entity(KGEntityType.METRIC, "mrr"),
        _make_entity(KGEntityType.FUNDING_ASSUMPTION, "Series A Plan"),
        _make_entity(KGEntityType.MARKET, "B2B SaaS"),
        _make_entity(KGEntityType.COMPETITOR, "Competitor A"),
        _make_entity(KGEntityType.COMPETITOR, "Competitor B"),
        _make_entity(KGEntityType.TEAM_MEMBER, "Alice (CEO)"),
        _make_entity(KGEntityType.TEAM_MEMBER, "Bob (CTO)"),
        _make_entity(KGEntityType.RISK, "Market Risk"),
    ]
    result = scorer.score(
        entities=entities,
        venture_name="MyStartup",
        venture_stage="seed",
        venture_one_liner="AI-powered platform",
        venture_problem="Manual processes waste time",
        venture_solution="Automated AI workflows",
    )
    assert result.overall_score > 80
    assert result.grade in ("A", "B")


def test_empty_venture_scores_below_30(scorer: InvestorReadinessScorer) -> None:
    """Venture with no KG data scores < 30."""
    result = scorer.score(entities=[])
    assert result.overall_score < 30
    assert result.grade in ("D", "F")


def test_dimension_weights_sum_to_1(scorer: InvestorReadinessScorer) -> None:
    """Rubric dimension weights must sum to 1.0."""
    result = scorer.score(entities=[])
    total_weight = sum(d.weight for d in result.dimensions)
    assert abs(total_weight - 1.0) < 0.01


def test_gaps_identified_for_missing_entities(scorer: InvestorReadinessScorer) -> None:
    """Missing entity types are listed in gaps."""
    result = scorer.score(entities=[])
    all_gaps = []
    for dim in result.dimensions:
        all_gaps.extend(dim.gaps)

    gap_text = " ".join(all_gaps).lower()
    assert "icp" in gap_text or "customer" in gap_text
    assert "team" in gap_text or "member" in gap_text
    assert "competitor" in gap_text or "competitive" in gap_text


def test_grade_assignment_thresholds(scorer: InvestorReadinessScorer) -> None:
    """Grade assignments map correctly to score ranges."""
    # Test via private method
    assert scorer._assign_grade(92) == "A"
    assert scorer._assign_grade(80) == "B"
    assert scorer._assign_grade(65) == "C"
    assert scorer._assign_grade(50) == "D"
    assert scorer._assign_grade(20) == "F"
