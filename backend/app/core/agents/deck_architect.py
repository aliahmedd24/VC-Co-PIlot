from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class DeckArchitect(BaseAgent):
    """Pitch deck structure, slide content, visual suggestions."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="deck-architect",
                name="Deck Architect",
                description="Pitch deck structure, slide content, visual suggestions.",
                supported_stages=[
                    VentureStage.PRE_SEED,
                    VentureStage.SEED,
                    VentureStage.SERIES_A,
                    VentureStage.SERIES_B,
                ],
                required_context=[
                    KGEntityType.VENTURE,
                    KGEntityType.MARKET,
                    KGEntityType.ICP,
                    KGEntityType.PRODUCT,
                    KGEntityType.METRIC,
                    KGEntityType.FUNDING_ASSUMPTION,
                ],
                can_create_artifacts=["deck_outline"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Deck Architect. Your role is to help founders build "
            "compelling pitch decks that win investment.\n\n"
            "Focus areas:\n"
            "- Optimal slide ordering and flow\n"
            "- Content recommendations per slide (problem, solution, market, etc.)\n"
            "- Data visualization suggestions\n"
            "- Investor-specific deck customization\n"
            "- Key messages and takeaways per slide\n\n"
            "Structure decks for the venture's stage. "
            "Early-stage decks focus on vision and team; "
            "later-stage decks emphasize traction and metrics."
        )


deck_architect = DeckArchitect()
