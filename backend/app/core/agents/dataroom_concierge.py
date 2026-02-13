from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class DataroomConcierge(BaseAgent):
    """Dataroom structure, document checklists, diligence readiness."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="dataroom-concierge",
                name="Dataroom Concierge",
                description="Dataroom structure, document checklists, diligence readiness.",
                supported_stages=[
                    VentureStage.SEED,
                    VentureStage.SERIES_A,
                    VentureStage.SERIES_B,
                ],
                required_context=[
                    KGEntityType.VENTURE,
                    KGEntityType.METRIC,
                    KGEntityType.FUNDING_ASSUMPTION,
                ],
                can_create_artifacts=["dataroom_structure"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Dataroom Concierge. Your role is to help founders "
            "prepare a professional data room for due diligence.\n\n"
            "Focus areas:\n"
            "- Data room folder structure and organization\n"
            "- Document checklist by category (legal, financial, product, team)\n"
            "- Due diligence readiness assessment\n"
            "- Priority documents by fundraising stage\n"
            "- Common gaps that slow down diligence\n\n"
            "Be specific about document types and naming conventions. "
            "Prioritize documents that investors request most frequently."
        )


dataroom_concierge = DataroomConcierge()
