from pydantic import BaseModel, Field


class ReadinessDimension(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1.0)
    gaps: list[str] = []
    recommendations: list[str] = []


class InvestorReadinessScore(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    grade: str
    dimensions: list[ReadinessDimension]
    summary: str
    top_priority_actions: list[str] = []


class ReadinessRequest(BaseModel):
    workspace_id: str
