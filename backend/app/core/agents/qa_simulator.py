from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class QASimulator(BaseAgent):
    """Tough investor questions, objection handling, mock pitches."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="qa-simulator",
                name="Q&A Simulator",
                description="Tough investor questions, objection handling, mock pitches.",
                supported_stages=list(VentureStage),
                required_context=[
                    KGEntityType.VENTURE,
                    KGEntityType.MARKET,
                    KGEntityType.METRIC,
                    KGEntityType.RISK,
                    KGEntityType.FUNDING_ASSUMPTION,
                ],
                can_create_artifacts=[],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the Q&A Simulator. Your role is to prepare founders "
            "for tough investor conversations.\n\n"
            "Focus areas:\n"
            "- Generate realistic investor questions based on the venture's profile\n"
            "- Provide suggested answers with data backing\n"
            "- Identify weak points that investors will probe\n"
            "- Simulate objection-handling scenarios\n"
            "- Coach on delivery and confidence\n\n"
            "Be tough but fair. Frame questions the way real VCs would ask them. "
            "After each question, suggest a strong response framework."
        )


qa_simulator = QASimulator()
