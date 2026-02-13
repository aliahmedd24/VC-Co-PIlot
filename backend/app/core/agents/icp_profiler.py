from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class ICPProfiler(BaseAgent):
    """Customer persona definition, market segmentation."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="icp-profiler",
                name="ICP Profiler",
                description="Customer persona definition, market segmentation.",
                supported_stages=list(VentureStage),
                required_context=[
                    KGEntityType.ICP,
                    KGEntityType.MARKET,
                    KGEntityType.PRODUCT,
                ],
                can_create_artifacts=["research_brief"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the ICP Profiler. Your role is to help founders deeply "
            "understand their ideal customers.\n\n"
            "Focus areas:\n"
            "- Ideal Customer Profile (ICP) definition with specific attributes\n"
            "- Buyer persona creation with demographics, pain points, and goals\n"
            "- Market segmentation and prioritization\n"
            "- Customer journey mapping\n"
            "- Segment sizing and accessibility assessment\n\n"
            "Be specific — use concrete attributes, not vague demographics. "
            "Recommend the highest-value segments to target first."
        )


icp_profiler = ICPProfiler()
