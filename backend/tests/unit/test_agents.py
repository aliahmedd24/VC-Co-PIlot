"""Unit tests for the agent framework."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.agents.response import AgentResponse, Citation, SuggestedEntity
from app.core.agents.router import AGENT_REGISTRY, INTENT_TO_AGENT, AgentRouter


class TestAgentResponse:
    """Tests for AgentResponse schema."""

    def test_agent_response_creation(self):
        """Test creating an AgentResponse."""
        response = AgentResponse(
            content="Test response",
            agent_id="test_agent",
            confidence=0.9,
        )
        assert response.content == "Test response"
        assert response.agent_id == "test_agent"
        assert response.confidence == 0.9
        assert response.citations == []
        assert response.suggested_entities == []

    def test_agent_response_with_citations(self):
        """Test AgentResponse with citations."""
        citations = [
            Citation(
                chunk_id="chunk1",
                document_id="doc1",
                snippet="Test snippet",
                score=0.85,
            )
        ]
        response = AgentResponse(
            content="Response with citation",
            agent_id="test_agent",
            citations=citations,
        )
        assert len(response.citations) == 1
        assert response.citations[0].chunk_id == "chunk1"
        assert response.citations[0].score == 0.85

    def test_citation_validation(self):
        """Test Citation score validation."""
        # Valid score
        citation = Citation(
            chunk_id="c1",
            document_id="d1",
            snippet="s1",
            score=0.5,
        )
        assert citation.score == 0.5

        # Score at boundaries
        citation_zero = Citation(chunk_id="c1", document_id="d1", snippet="s1", score=0.0)
        assert citation_zero.score == 0.0

        citation_one = Citation(chunk_id="c1", document_id="d1", snippet="s1", score=1.0)
        assert citation_one.score == 1.0

    def test_suggested_entity(self):
        """Test SuggestedEntity schema."""
        entity = SuggestedEntity(
            type="competitor",
            data={"name": "Competitor Inc", "website": "https://competitor.com"},
            confidence=0.7,
            reasoning="Found in market analysis document",
        )
        assert entity.type == "competitor"
        assert entity.data["name"] == "Competitor Inc"
        assert entity.confidence == 0.7


class TestAgentRegistry:
    """Tests for agent registry and routing."""

    def test_intent_to_agent_mapping(self):
        """Test intent to agent name mapping."""
        assert INTENT_TO_AGENT["GENERAL"] == "general_agent"
        assert INTENT_TO_AGENT["VENTURE_ANALYSIS"] == "venture_analyst"
        assert INTENT_TO_AGENT["MARKET_RESEARCH"] == "market_research"

    def test_agent_registry_has_all_agents(self):
        """Test all agents are registered."""
        assert "general_agent" in AGENT_REGISTRY
        assert "venture_analyst" in AGENT_REGISTRY
        assert "market_research" in AGENT_REGISTRY


class TestAgentRouter:
    """Tests for AgentRouter."""

    @pytest.fixture
    def mock_brain(self):
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
    def mock_llm(self):
        """Create a mock LLM client."""
        llm = MagicMock()
        llm.complete = AsyncMock(return_value="GENERAL")
        llm.stream = AsyncMock()
        return llm

    def test_router_initialization(self, mock_brain, mock_llm):
        """Test AgentRouter initialization."""
        router = AgentRouter(mock_brain, mock_llm)
        assert router.brain == mock_brain
        assert router.llm == mock_llm
        assert router._agent_cache == {}

    def test_get_agent_valid(self, mock_brain, mock_llm):
        """Test getting a valid agent."""
        router = AgentRouter(mock_brain, mock_llm)
        agent = router.get_agent("general_agent")
        assert agent.name == "general_agent"

        # Test caching
        agent2 = router.get_agent("general_agent")
        assert agent is agent2

    def test_get_agent_invalid(self, mock_brain, mock_llm):
        """Test getting an invalid agent raises error."""
        router = AgentRouter(mock_brain, mock_llm)
        with pytest.raises(ValueError, match="Unknown agent"):
            router.get_agent("nonexistent_agent")

    @pytest.mark.asyncio
    async def test_classify_intent_general(self, mock_brain, mock_llm):
        """Test intent classification for general queries."""
        mock_llm.complete = AsyncMock(return_value="GENERAL")
        router = AgentRouter(mock_brain, mock_llm)

        agent_name = await router.classify_intent("What is product-market fit?")
        assert agent_name == "general_agent"

    @pytest.mark.asyncio
    async def test_classify_intent_venture_analysis(self, mock_brain, mock_llm):
        """Test intent classification for venture analysis."""
        mock_llm.complete = AsyncMock(return_value="VENTURE_ANALYSIS")
        router = AgentRouter(mock_brain, mock_llm)

        agent_name = await router.classify_intent("Analyze our business model")
        assert agent_name == "venture_analyst"

    @pytest.mark.asyncio
    async def test_classify_intent_market_research(self, mock_brain, mock_llm):
        """Test intent classification for market research."""
        mock_llm.complete = AsyncMock(return_value="MARKET_RESEARCH")
        router = AgentRouter(mock_brain, mock_llm)

        agent_name = await router.classify_intent("Who are our competitors?")
        assert agent_name == "market_research"

    @pytest.mark.asyncio
    async def test_classify_intent_defaults_to_general(self, mock_brain, mock_llm):
        """Test unknown intent defaults to general agent."""
        mock_llm.complete = AsyncMock(return_value="UNKNOWN_INTENT")
        router = AgentRouter(mock_brain, mock_llm)

        agent_name = await router.classify_intent("Random query")
        assert agent_name == "general_agent"

    @pytest.mark.asyncio
    async def test_route_uses_classification(self, mock_brain, mock_llm):
        """Test route method uses intent classification."""
        mock_llm.complete = AsyncMock(
            side_effect=[
                "GENERAL",  # Classification call
                "This is a response about product-market fit.",  # Agent response
            ]
        )
        router = AgentRouter(mock_brain, mock_llm)

        response = await router.route("What is PMF?")

        assert response.agent_id == "general_agent"
        assert "product-market fit" in response.content

    @pytest.mark.asyncio
    async def test_route_with_override(self, mock_brain, mock_llm):
        """Test route with agent override skips classification."""
        mock_llm.complete = AsyncMock(return_value="Market research response.")
        router = AgentRouter(mock_brain, mock_llm)

        response = await router.route(
            "Tell me about competitors",
            agent_override="market_research",
        )

        # Should be market_research even though we didn't classify
        assert response.agent_id == "market_research"

        # Classification should not have been called
        # (only the agent's execute call)
        assert mock_llm.complete.call_count == 1
