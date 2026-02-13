from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class ValuationStrategist(BaseAgent):
    """Valuation methodologies, comparable analysis, round structuring."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="valuation-strategist",
                name="Valuation Strategist",
                description="Valuation methodologies, comparable analysis, round structuring.",
                supported_stages=[
                    VentureStage.SEED,
                    VentureStage.SERIES_A,
                    VentureStage.SERIES_B,
                    VentureStage.GROWTH,
                ],
                required_context=[
                    KGEntityType.METRIC,
                    KGEntityType.FUNDING_ASSUMPTION,
                    KGEntityType.MARKET,
                ],
                can_create_artifacts=["valuation_memo"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Valuation Strategist. Your role is to help founders "
            "understand and negotiate fair valuations.\n\n"
            "Focus areas:\n"
            "- Valuation methodologies (VC method, comparables, DCF, scorecard)\n"
            "- Comparable company analysis with relevant benchmarks\n"
            "- Round structuring and term sheet considerations\n"
            "- Cap table impact analysis\n"
            "- Dilution modeling and scenario planning\n\n"
            "Always present multiple valuation approaches. "
            "Be transparent about assumptions and their sensitivity."
        )


valuation_strategist = ValuationStrategist()
