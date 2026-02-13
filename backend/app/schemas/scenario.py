from pydantic import BaseModel, Field


class RoundInput(BaseModel):
    raise_amount: float = Field(gt=0)
    pre_money_valuation: float = Field(gt=0)
    option_pool_pct: float = Field(default=0.10, ge=0, le=0.5)


class FundingScenario(BaseModel):
    round_label: str
    raise_amount: float
    pre_money_valuation: float
    post_money_valuation: float
    dilution_pct: float
    option_pool_pct: float
    founder_ownership_after: float


class ExitScenario(BaseModel):
    exit_multiple: float
    exit_valuation: float
    founder_proceeds: float
    investor_proceeds: float


class CapTableEntry(BaseModel):
    round_label: str
    founder_pct: float
    investor_pct: float
    option_pool_pct: float


class ScenarioModelResult(BaseModel):
    scenarios: list[FundingScenario]
    exit_scenarios: list[ExitScenario]
    cap_table_progression: list[CapTableEntry]


class ScenarioRequest(BaseModel):
    workspace_id: str
    rounds: list[RoundInput] = Field(min_length=1, max_length=5)
    exit_multiples: list[float] = Field(
        default=[1.0, 3.0, 5.0, 10.0, 20.0],
        description="Multiples to model exit at",
    )
