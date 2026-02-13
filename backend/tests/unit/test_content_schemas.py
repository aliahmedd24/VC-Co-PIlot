from app.core.artifacts.content_schemas import (
    CONTENT_SCHEMA_MAP,
    BoardMemoContent,
    CustomContent,
    DataroomCategory,
    DataroomStructureContent,
    DeckOutlineContent,
    FinancialModelContent,
    KPIDashboardContent,
    KPIMetric,
    LeanCanvasContent,
    PitchNarrativeContent,
    ResearchBriefContent,
    SlideOutline,
    ValuationMemoContent,
)
from app.models.artifact import ArtifactType


def test_lean_canvas_valid() -> None:
    content = LeanCanvasContent(
        problem=["High CAC"],
        solution=["AI-powered outreach"],
        key_metrics=["MRR", "Churn"],
        unique_value_prop="10x faster prospecting",
        customer_segments=["B2B SaaS"],
    )
    assert content.problem == ["High CAC"]
    assert content.unique_value_prop == "10x faster prospecting"


def test_lean_canvas_defaults() -> None:
    content = LeanCanvasContent()
    assert content.problem == []
    assert content.unique_value_prop == ""
    assert content.revenue_streams == []


def test_pitch_narrative_valid() -> None:
    content = PitchNarrativeContent(
        hook="What if fundraising took 5 minutes?",
        problem_story="Founders spend months...",
        ask="$2M seed round",
    )
    assert content.hook == "What if fundraising took 5 minutes?"
    assert content.ask == "$2M seed round"


def test_deck_outline_with_slides() -> None:
    content = DeckOutlineContent(
        slides=[
            SlideOutline(
                title="Problem",
                key_points=["Market pain", "User quotes"],
                visual_suggestion="Photo of frustrated user",
            ),
            SlideOutline(
                title="Solution",
                key_points=["Product demo"],
            ),
        ]
    )
    assert len(content.slides) == 2
    assert content.slides[0].title == "Problem"
    assert content.slides[1].visual_suggestion == ""


def test_valuation_memo_valid() -> None:
    content = ValuationMemoContent(
        methodology="DCF + Comparables",
        range_low=5_000_000,
        range_high=8_000_000,
        recommended=6_500_000,
        comparables=[{"company": "Acme", "multiple": 12.5}],
    )
    assert content.range_low == 5_000_000
    assert content.recommended == 6_500_000
    assert len(content.comparables) == 1


def test_financial_model_valid() -> None:
    content = FinancialModelContent(
        runway_months=18,
        burn_rate=50000.0,
        unit_economics={"cac": 120, "ltv": 1500},
        revenue_projections=[{"period": "Q1", "amount": 100000}],
    )
    assert content.runway_months == 18
    assert content.unit_economics["ltv"] == 1500


def test_kpi_dashboard_valid() -> None:
    content = KPIDashboardContent(
        metrics=[
            KPIMetric(
                name="MRR",
                current_value=50000,
                target_value=100000,
                unit="USD",
                trend="up",
                category="financial",
            )
        ]
    )
    assert len(content.metrics) == 1
    assert content.metrics[0].name == "MRR"
    assert content.metrics[0].trend == "up"


def test_dataroom_structure_valid() -> None:
    content = DataroomStructureContent(
        categories=[
            DataroomCategory(
                name="Legal",
                required_docs=["Articles of Incorporation", "Cap Table"],
                uploaded_docs=["Articles of Incorporation"],
                completion_pct=50.0,
            )
        ]
    )
    assert len(content.categories) == 1
    assert content.categories[0].completion_pct == 50.0


def test_research_brief_defaults() -> None:
    content = ResearchBriefContent()
    assert content.title == ""
    assert content.key_findings == []


def test_board_memo_defaults() -> None:
    content = BoardMemoContent()
    assert content.subject == ""
    assert content.decisions_needed == []


def test_custom_content_valid() -> None:
    content = CustomContent(
        title="Custom Analysis",
        body="Detailed analysis here...",
        sections=[{"heading": "Section 1", "text": "Content"}],
    )
    assert content.title == "Custom Analysis"
    assert len(content.sections) == 1


def test_content_schema_map_covers_all_types() -> None:
    for artifact_type in ArtifactType:
        assert artifact_type in CONTENT_SCHEMA_MAP, (
            f"Missing content schema for {artifact_type}"
        )
