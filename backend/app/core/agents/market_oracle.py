from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class MarketOracle(BaseAgent):
    """Market sizing (TAM/SAM/SOM), industry trends, growth analysis."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="market-oracle",
                name="Market Oracle",
                description=(
                    "Market sizing, industry trends, "
                    "competitive landscape, growth analysis."
                ),
                supported_stages=list(VentureStage),
                required_context=[
                    KGEntityType.MARKET,
                    KGEntityType.COMPETITOR,
                ],
                can_create_artifacts=["research_brief"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Market Oracle. Your role is to provide deep market "
            "intelligence and competitive analysis.\n\n"
            "Focus areas:\n"
            "- TAM/SAM/SOM sizing with methodology explanation\n"
            "- Industry trend identification and analysis\n"
            "- Growth rate projections with supporting data\n"
            "- Market dynamics and competitive forces\n"
            "- Market entry timing and positioning\n\n"
            "Always cite data sources when referencing market figures. "
            "Distinguish between estimates and verified data points."
        )


market_oracle = MarketOracle()
