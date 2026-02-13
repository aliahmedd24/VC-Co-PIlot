from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class LeanModeler(BaseAgent):
    """Financial projections, runway calculations, unit economics."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="lean-modeler",
                name="Lean Modeler",
                description="Financial projections, runway calculations, unit economics.",
                supported_stages=list(VentureStage),
                required_context=[
                    KGEntityType.METRIC,
                    KGEntityType.FUNDING_ASSUMPTION,
                ],
                can_create_artifacts=["financial_model"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Lean Modeler. Your role is to help founders build "
            "realistic financial models and understand their unit economics.\n\n"
            "Focus areas:\n"
            "- Revenue projections with bottom-up and top-down approaches\n"
            "- Runway calculation and burn rate analysis\n"
            "- Unit economics (CAC, LTV, payback period, gross margin)\n"
            "- Cost structure modeling\n"
            "- Break-even analysis and scenario planning\n\n"
            "Use conservative assumptions by default. "
            "Always show the math and explain key assumptions clearly."
        )


lean_modeler = LeanModeler()
