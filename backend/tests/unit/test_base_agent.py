from typing import Any
from unittest.mock import MagicMock

from app.core.agents.base import AgentConfig, BaseAgent
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage
from app.schemas.brain import ChunkResult, EntityResult


class _StubAgent(BaseAgent):
    """Concrete agent for testing BaseAgent methods."""

    def __init__(self) -> None:
        super().__init__(
            config=AgentConfig(
                id="test-agent",
                name="Test Agent",
                description="A test agent.",
                supported_stages=[VentureStage.SEED],
                required_context=[KGEntityType.VENTURE, KGEntityType.MARKET],
                can_create_artifacts=["test_artifact"],
            )
        )

    def get_agent_specific_instructions(self) -> str:
        return "You are a test agent. Be helpful."


def _make_venture() -> Any:
    v = MagicMock()
    v.name = "TestCo"
    v.stage = VentureStage.SEED
    v.one_liner = "We make cool stuff"
    return v


def test_build_system_prompt() -> None:
    agent = _StubAgent()
    venture = _make_venture()
    entities = [
        EntityResult(
            id="e1",
            type=KGEntityType.VENTURE,
            status="confirmed",
            data={"name": "TestCo Venture"},
            confidence=0.9,
            evidence_count=2,
        ),
    ]
    chunks = [
        ChunkResult(
            chunk_id="c1",
            document_id="doc-123",
            content="This is some document content about the venture.",
            similarity=0.85,
            freshness_weight=0.95,
            final_score=0.8075,
        ),
    ]

    prompt = agent._build_system_prompt(venture, entities, chunks)

    assert "TestCo" in prompt
    assert "seed" in prompt
    assert "We make cool stuff" in prompt
    assert "TestCo Venture" in prompt
    assert "[Source: doc-123]" in prompt
    assert "You are a test agent" in prompt

    # Skill content is only injected if SKILL.md exists for the agent.
    # test-agent has no SKILL.md, so "## Domain Expertise" should NOT appear
    # (this confirms the loader handles missing skills gracefully).
    assert "## Domain Expertise" not in prompt


def test_extract_citations() -> None:
    text = (
        "Based on the analysis [Source: doc-123], "
        "we can see that [Source: doc-456] and [Source: doc-123] "
        "confirm the market size."
    )
    citations = BaseAgent._extract_citations(text)
    assert len(citations) == 2  # doc-123 deduplicated
    assert {"document_id": "doc-123"} in citations
    assert {"document_id": "doc-456"} in citations


def test_extract_proposed_updates() -> None:
    text = (
        "Here is my analysis.\n"
        '<!-- PROPOSED_UPDATE: {"entity_type": "market", "data": {"name": "EdTech"}} -->\n'
        "More content here.\n"
        '<!-- PROPOSED_UPDATE: {"entity_type": "competitor", "data": {"name": "Rival Inc"}} -->'
    )
    updates = BaseAgent._extract_proposed_updates(text)
    assert len(updates) == 2
    assert updates[0]["entity_type"] == "market"
    assert updates[0]["data"]["name"] == "EdTech"
    assert updates[1]["entity_type"] == "competitor"


def test_extract_proposed_updates_malformed() -> None:
    text = (
        "Some content.\n"
        "<!-- PROPOSED_UPDATE: {invalid json here} -->\n"
        '<!-- PROPOSED_UPDATE: {"entity_type": "market", "data": {"name": "Valid"}} -->'
    )
    updates = BaseAgent._extract_proposed_updates(text)
    assert len(updates) == 1
    assert updates[0]["entity_type"] == "market"
