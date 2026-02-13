import enum

from pydantic import BaseModel, Field


class IntentCategory(str, enum.Enum):
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    NARRATIVE = "narrative"
    DECK = "deck"
    VALUATION = "valuation"
    FINANCIAL = "financial"
    METRICS = "metrics"
    QA_PREP = "qa_prep"
    DATAROOM = "dataroom"
    ICP = "icp"
    RISK = "risk"
    GENERAL = "general"


class ModelProfile(str, enum.Enum):
    REASONING_HEAVY = "reasoning_heavy"
    WRITING_POLISH = "writing_polish"
    TOOL_USING = "tool_using"
    FAST_RESPONSE = "fast_response"
    DEFAULT = "default"


class RoutingPlan(BaseModel):
    selected_agent: str
    model_profile: ModelProfile
    tools: list[str]
    artifact_needed: bool
    fallback_agent: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    latency_ms: float
