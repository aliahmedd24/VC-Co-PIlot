from app.core.agents.base import BaseAgent
from app.core.agents.dataroom_concierge import dataroom_concierge
from app.core.agents.deck_architect import deck_architect
from app.core.agents.icp_profiler import icp_profiler
from app.core.agents.kpi_dashboard import kpi_dashboard
from app.core.agents.lean_modeler import lean_modeler
from app.core.agents.market_oracle import market_oracle
from app.core.agents.pre_mortem_critic import pre_mortem_critic
from app.core.agents.qa_simulator import qa_simulator
from app.core.agents.storyteller import storyteller
from app.core.agents.valuation_strategist import valuation_strategist
from app.core.agents.venture_architect import venture_architect


class AgentRegistry:
    """Singleton registry for all specialized agents."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.config.id] = agent

    def get(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def get_all(self) -> dict[str, BaseAgent]:
        return dict(self._agents)

    def list_ids(self) -> list[str]:
        return list(self._agents.keys())


agent_registry = AgentRegistry()
agent_registry.register(venture_architect)
agent_registry.register(market_oracle)
agent_registry.register(storyteller)
agent_registry.register(deck_architect)
agent_registry.register(valuation_strategist)
agent_registry.register(lean_modeler)
agent_registry.register(kpi_dashboard)
agent_registry.register(qa_simulator)
agent_registry.register(dataroom_concierge)
agent_registry.register(icp_profiler)
agent_registry.register(pre_mortem_critic)
