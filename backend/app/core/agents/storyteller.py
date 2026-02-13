from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class Storyteller(BaseAgent):
    """Pitch narratives, founding stories, mission/vision crafting."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="storyteller",
                name="Storyteller",
                description="Pitch narratives, founding stories, mission/vision crafting.",
                supported_stages=list(VentureStage),
                required_context=[
                    KGEntityType.VENTURE,
                    KGEntityType.ICP,
                    KGEntityType.PRODUCT,
                ],
                can_create_artifacts=["pitch_narrative"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Storyteller. Your role is to craft compelling "
            "narratives that resonate with investors.\n\n"
            "Focus areas:\n"
            "- Pitch narratives that connect emotionally and logically\n"
            "- Founding story development with authenticity\n"
            "- Mission and vision statement crafting\n"
            "- Elevator pitch refinement (30-second and 2-minute versions)\n"
            "- Narrative arc for investor presentations\n\n"
            "Use vivid, concrete language. Show, don't tell. "
            "Every narrative should answer: why this team, why now, why this matters."
        )


storyteller = Storyteller()
