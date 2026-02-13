from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class KPIDashboard(BaseAgent):
    """KPI definition, tracking suggestions, dashboard design."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="kpi-dashboard",
                name="KPI Dashboard",
                description="KPI definition, tracking suggestions, dashboard design.",
                supported_stages=[
                    VentureStage.SEED,
                    VentureStage.SERIES_A,
                    VentureStage.SERIES_B,
                    VentureStage.GROWTH,
                ],
                required_context=[
                    KGEntityType.METRIC,
                ],
                can_create_artifacts=["kpi_dashboard"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return (
            "You are the KPI Dashboard advisor. Your role is to help founders "
            "define, track, and report the right metrics.\n\n"
            "Focus areas:\n"
            "- North star metric identification\n"
            "- KPI hierarchy and driver tree design\n"
            "- Dashboard layout and visualization recommendations\n"
            "- Metric benchmarks for the venture's stage and industry\n"
            "- Investor reporting metric selection (MRR, ARR, churn, NRR, etc.)\n\n"
            "Recommend metrics that are actionable, not vanity metrics. "
            "Tailor the dashboard to the venture's stage."
        )


kpi_dashboard = KPIDashboard()
