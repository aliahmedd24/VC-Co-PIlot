from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    revenue: float | None = Field(None, ge=0, description="Annual revenue / ARR")
    growth_rate: float | None = Field(None, description="YoY growth rate (e.g. 1.5 = 150%)")
    industry: str = Field(default="saas", description="Industry sector")
    stage: str = Field(default="seed", description="Funding stage")
    discount_rate: float = Field(default=0.30, ge=0.01, le=1.0)
    projection_years: int = Field(default=5, ge=1, le=10)
    comparable_exits: list[float] | None = Field(
        None, description="List of comparable exit valuations"
    )


class ValuationMethodResult(BaseModel):
    method: str
    low: float
    mid: float
    high: float
    details: dict[str, float | str] = {}
    warnings: list[str] = []


class ValuationResult(BaseModel):
    low: float
    mid: float
    high: float
    methods: list[ValuationMethodResult]
    currency: str = "USD"
    warnings: list[str] = []
