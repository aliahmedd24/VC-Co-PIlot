from typing import Any

from pydantic import BaseModel

from app.models.artifact import ArtifactType


class LeanCanvasContent(BaseModel):
    problem: list[str] = []
    solution: list[str] = []
    key_metrics: list[str] = []
    unique_value_prop: str = ""
    unfair_advantage: str = ""
    channels: list[str] = []
    customer_segments: list[str] = []
    cost_structure: list[str] = []
    revenue_streams: list[str] = []


class PitchNarrativeContent(BaseModel):
    hook: str = ""
    problem_story: str = ""
    solution_reveal: str = ""
    traction_proof: str = ""
    market_opportunity: str = ""
    business_model: str = ""
    team_story: str = ""
    ask: str = ""
    vision: str = ""


class SlideOutline(BaseModel):
    title: str
    key_points: list[str]
    visual_suggestion: str = ""
    speaker_notes: str = ""


class DeckOutlineContent(BaseModel):
    slides: list[SlideOutline] = []


class ValuationMemoContent(BaseModel):
    methodology: str = ""
    comparables: list[dict[str, Any]] = []
    assumptions: list[dict[str, Any]] = []
    range_low: float | None = None
    range_high: float | None = None
    recommended: float | None = None
    narrative: str = ""


class FinancialModelContent(BaseModel):
    revenue_projections: list[dict[str, Any]] = []
    cost_projections: list[dict[str, Any]] = []
    runway_months: int | None = None
    burn_rate: float | None = None
    unit_economics: dict[str, Any] = {}
    funding_scenarios: list[dict[str, Any]] = []


class KPIMetric(BaseModel):
    name: str
    current_value: float | None = None
    target_value: float | None = None
    unit: str = ""
    trend: str = ""
    category: str = ""


class KPIDashboardContent(BaseModel):
    metrics: list[KPIMetric] = []


class DataroomCategory(BaseModel):
    name: str
    required_docs: list[str]
    uploaded_docs: list[str] = []
    completion_pct: float = 0.0


class DataroomStructureContent(BaseModel):
    categories: list[DataroomCategory] = []


class ResearchBriefContent(BaseModel):
    title: str = ""
    summary: str = ""
    key_findings: list[str] = []
    methodology: str = ""
    sources: list[str] = []
    recommendations: list[str] = []


class BoardMemoContent(BaseModel):
    subject: str = ""
    executive_summary: str = ""
    key_updates: list[str] = []
    financials_summary: str = ""
    decisions_needed: list[str] = []
    appendix: list[str] = []


class CustomContent(BaseModel):
    title: str = ""
    body: str = ""
    sections: list[dict[str, Any]] = []


CONTENT_SCHEMA_MAP: dict[ArtifactType, type[BaseModel]] = {
    ArtifactType.LEAN_CANVAS: LeanCanvasContent,
    ArtifactType.RESEARCH_BRIEF: ResearchBriefContent,
    ArtifactType.PITCH_NARRATIVE: PitchNarrativeContent,
    ArtifactType.DECK_OUTLINE: DeckOutlineContent,
    ArtifactType.FINANCIAL_MODEL: FinancialModelContent,
    ArtifactType.VALUATION_MEMO: ValuationMemoContent,
    ArtifactType.DATAROOM_STRUCTURE: DataroomStructureContent,
    ArtifactType.KPI_DASHBOARD: KPIDashboardContent,
    ArtifactType.BOARD_MEMO: BoardMemoContent,
    ArtifactType.CUSTOM: CustomContent,
}
