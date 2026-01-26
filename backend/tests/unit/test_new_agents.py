"""Unit tests for new specialized agents."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.agents.competitive_intel_agent import CompetitiveIntelAgent
from app.core.agents.dataroom_concierge_agent import DataroomConciergeAgent
from app.core.agents.deck_architect_agent import DeckArchitectAgent
from app.core.agents.icp_profiler_agent import ICPProfilerAgent
from app.core.agents.kpi_dashboard_agent import KPIDashboardAgent
from app.core.agents.lean_modeler_agent import LeanModelerAgent
from app.core.agents.pre_mortem_critic_agent import PreMortemCriticAgent
from app.core.agents.qa_simulator_agent import QASimulatorAgent
from app.core.agents.storyteller_agent import StorytellerAgent
from app.core.agents.valuation_strategist_agent import ValuationStrategistAgent
from app.core.agents.venture_architect_agent import VentureArchitectAgent


@pytest.fixture
def mock_brain():
    """Create a mock StartupBrain."""
    brain = MagicMock()
    brain.venture_id = "test-venture-id"
    brain.retrieve = AsyncMock(
        return_value={
            "chunks": [],
            "entities": [],
            "citations": [],
        }
    )
    brain.get_snapshot = AsyncMock(
        return_value={
            "venture": {"name": "Test Startup", "stage": "seed"},
            "entities": {},
        }
    )
    brain.kg = MagicMock()
    brain.kg.get_entities_by_type = AsyncMock(return_value=[])
    return brain


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    llm = MagicMock()
    llm.complete = AsyncMock(return_value="Test response from agent.")
    llm.stream = AsyncMock()
    return llm


class TestVentureArchitectAgent:
    """Tests for VentureArchitectAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = VentureArchitectAgent(mock_brain, mock_llm)
        assert agent.name == "venture_architect"
        assert "Lean Canvas" in agent.description

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = VentureArchitectAgent(mock_brain, mock_llm)
        result = await agent.execute("Create a lean canvas", {})
        assert result.agent_id == "venture_architect"
        assert result.content is not None


class TestStorytellerAgent:
    """Tests for StorytellerAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = StorytellerAgent(mock_brain, mock_llm)
        assert agent.name == "storyteller"
        assert "narrative" in agent.description.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = StorytellerAgent(mock_brain, mock_llm)
        result = await agent.execute("Help with our founding story", {})
        assert result.agent_id == "storyteller"


class TestDeckArchitectAgent:
    """Tests for DeckArchitectAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = DeckArchitectAgent(mock_brain, mock_llm)
        assert agent.name == "deck_architect"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = DeckArchitectAgent(mock_brain, mock_llm)
        result = await agent.execute("Create pitch deck outline", {})
        assert result.agent_id == "deck_architect"


class TestValuationStrategistAgent:
    """Tests for ValuationStrategistAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = ValuationStrategistAgent(mock_brain, mock_llm)
        assert agent.name == "valuation_strategist"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = ValuationStrategistAgent(mock_brain, mock_llm)
        result = await agent.execute("What should our valuation be?", {})
        assert result.agent_id == "valuation_strategist"


class TestLeanModelerAgent:
    """Tests for LeanModelerAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = LeanModelerAgent(mock_brain, mock_llm)
        assert agent.name == "lean_modeler"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = LeanModelerAgent(mock_brain, mock_llm)
        result = await agent.execute("Calculate our runway", {})
        assert result.agent_id == "lean_modeler"


class TestKPIDashboardAgent:
    """Tests for KPIDashboardAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = KPIDashboardAgent(mock_brain, mock_llm)
        assert agent.name == "kpi_dashboard"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = KPIDashboardAgent(mock_brain, mock_llm)
        result = await agent.execute("What KPIs should we track?", {})
        assert result.agent_id == "kpi_dashboard"


class TestQASimulatorAgent:
    """Tests for QASimulatorAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = QASimulatorAgent(mock_brain, mock_llm)
        assert agent.name == "qa_simulator"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = QASimulatorAgent(mock_brain, mock_llm)
        result = await agent.execute("Prepare me for investor questions", {})
        assert result.agent_id == "qa_simulator"


class TestDataroomConciergeAgent:
    """Tests for DataroomConciergeAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = DataroomConciergeAgent(mock_brain, mock_llm)
        assert agent.name == "dataroom_concierge"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = DataroomConciergeAgent(mock_brain, mock_llm)
        result = await agent.execute("Set up our data room", {})
        assert result.agent_id == "dataroom_concierge"


class TestICPProfilerAgent:
    """Tests for ICPProfilerAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = ICPProfilerAgent(mock_brain, mock_llm)
        assert agent.name == "icp_profiler"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = ICPProfilerAgent(mock_brain, mock_llm)
        result = await agent.execute("Define our ideal customer", {})
        assert result.agent_id == "icp_profiler"


class TestPreMortemCriticAgent:
    """Tests for PreMortemCriticAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = PreMortemCriticAgent(mock_brain, mock_llm)
        assert agent.name == "pre_mortem_critic"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = PreMortemCriticAgent(mock_brain, mock_llm)
        result = await agent.execute("What could cause us to fail?", {})
        assert result.agent_id == "pre_mortem_critic"


class TestCompetitiveIntelAgent:
    """Tests for CompetitiveIntelAgent."""

    def test_agent_attributes(self, mock_brain, mock_llm):
        agent = CompetitiveIntelAgent(mock_brain, mock_llm)
        assert agent.name == "competitive_intel"

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_brain, mock_llm):
        agent = CompetitiveIntelAgent(mock_brain, mock_llm)
        result = await agent.execute("Analyze our competitors", {})
        assert result.agent_id == "competitive_intel"


class TestAgentRegistryExpanded:
    """Tests for expanded agent registry."""

    def test_all_new_agents_registered(self):
        from app.core.agents.router import AGENT_REGISTRY

        new_agents = [
            "venture_architect",
            "storyteller",
            "deck_architect",
            "valuation_strategist",
            "lean_modeler",
            "kpi_dashboard",
            "qa_simulator",
            "dataroom_concierge",
            "icp_profiler",
            "pre_mortem_critic",
            "competitive_intel",
        ]
        for agent_name in new_agents:
            assert agent_name in AGENT_REGISTRY, f"{agent_name} not in registry"

    def test_all_new_intents_mapped(self):
        from app.core.agents.router import INTENT_TO_AGENT

        new_intents = [
            "VENTURE_ARCHITECT",
            "NARRATIVE",
            "DECK",
            "VALUATION",
            "FINANCIAL",
            "METRICS",
            "QA_PREP",
            "DATAROOM",
            "ICP",
            "RISK",
            "COMPETITOR",
        ]
        for intent in new_intents:
            assert intent in INTENT_TO_AGENT, f"{intent} not in intent mapping"
