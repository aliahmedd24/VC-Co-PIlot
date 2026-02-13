from app.core.agents.registry import agent_registry

EXPECTED_AGENT_IDS = [
    "venture-architect",
    "market-oracle",
    "storyteller",
    "deck-architect",
    "valuation-strategist",
    "lean-modeler",
    "kpi-dashboard",
    "qa-simulator",
    "dataroom-concierge",
    "icp-profiler",
    "pre-mortem-critic",
]


def test_all_agents_registered() -> None:
    registered = agent_registry.list_ids()
    assert len(registered) == 11
    for agent_id in EXPECTED_AGENT_IDS:
        assert agent_id in registered, f"Missing agent: {agent_id}"


def test_get_agent_by_id() -> None:
    for agent_id in EXPECTED_AGENT_IDS:
        agent = agent_registry.get(agent_id)
        assert agent is not None, f"Could not retrieve agent: {agent_id}"
        assert agent.config.id == agent_id


def test_get_nonexistent_agent() -> None:
    agent = agent_registry.get("nonexistent-agent")
    assert agent is None
