from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class VentureArchitect(BaseAgent):
    """Foundational venture design, Lean Canvas, JTBD, experiment planning."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="venture-architect",
                name="Venture Architect",
                description="Foundational venture design, Lean Canvas, JTBD, experiment planning.",
                supported_stages=[
                    VentureStage.IDEATION,
                    VentureStage.PRE_SEED,
                    VentureStage.SEED,
                ],
                required_context=[
                    KGEntityType.VENTURE,
                    KGEntityType.MARKET,
                    KGEntityType.ICP,
                    KGEntityType.PRODUCT,
                    KGEntityType.COMPETITOR,
                ],
                can_create_artifacts=["lean_canvas", "research_brief"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Venture Architect. Your role is to help founders design "
            "and validate their venture from first principles.\n\n"
            "Focus areas:\n"
            "- Lean Canvas analysis and recommendations\n"
            "- Jobs-to-be-Done (JTBD) framework application\n"
            "- Experiment design and hypothesis validation\n"
            "- Business model evaluation and iteration\n"
            "- Problem-solution fit assessment\n\n"
            "Always ground your advice in the venture's current stage and available data. "
            "Prioritize clarity and actionability over comprehensiveness."
        )


venture_architect = VentureArchitect()
