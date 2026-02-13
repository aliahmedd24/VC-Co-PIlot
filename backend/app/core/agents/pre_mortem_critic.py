from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class PreMortemCritic(BaseAgent):
    """Risk analysis, failure scenario simulation, threat assessment."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="pre-mortem-critic",
                name="Pre-Mortem Critic",
                description="Risk analysis, failure scenario simulation, threat assessment.",
                supported_stages=list(VentureStage),
                required_context=[
                    KGEntityType.RISK,
                    KGEntityType.VENTURE,
                    KGEntityType.MARKET,
                    KGEntityType.COMPETITOR,
                ],
                can_create_artifacts=["research_brief"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Pre-Mortem Critic. Your role is to stress-test "
            "the venture by imagining how it could fail.\n\n"
            "Focus areas:\n"
            "- Pre-mortem analysis: imagine the venture failed, work backwards to identify causes\n"
            "- Risk categorization (market, execution, technical, regulatory, competitive)\n"
            "- Failure scenario simulation with probability assessment\n"
            "- Mitigation strategy recommendations\n"
            "- Blind spot identification\n\n"
            "Be constructively critical. The goal is to strengthen the venture, "
            "not discourage. Present risks with actionable mitigation plans."
        )


pre_mortem_critic = PreMortemCritic()
