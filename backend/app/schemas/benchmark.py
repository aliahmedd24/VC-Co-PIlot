from pydantic import BaseModel, Field


class BenchmarkMetric(BaseModel):
    metric_name: str
    venture_value: float | None = None
    peer_median: float
    peer_p25: float
    peer_p75: float
    percentile: float = Field(ge=0, le=100)
    status: str  # "strong", "average", "weak"


class BenchmarkResult(BaseModel):
    peer_cohort: str
    cohort_size: int
    metrics: list[BenchmarkMetric]
    strengths: list[str] = []
    weaknesses: list[str] = []


class BenchmarkRequest(BaseModel):
    workspace_id: str
    industry: str = "saas"
    stage: str = "seed"
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Metric name → venture's value",
    )


class SuccessStoryMatch(BaseModel):
    name: str
    industry: str
    stage: str
    similarity_score: float = Field(ge=0, le=1.0)
    parallels: list[str] = []
    differences: list[str] = []
    key_traits: list[str] = []


class SuccessStoryResult(BaseModel):
    matches: list[SuccessStoryMatch]
    venture_summary: str = ""


class SuccessStoryRequest(BaseModel):
    workspace_id: str
    industry: str = "saas"
    stage: str = "seed"
    business_model: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)
