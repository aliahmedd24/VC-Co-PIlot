
import pytest

from app.core.skills.skill_loader import SkillLoader


@pytest.fixture()
def loader() -> SkillLoader:
    """Return a SkillLoader pointing at the real skills directory."""
    return SkillLoader()


# ------------------------------------------------------------------ #
# load_agent_skill
# ------------------------------------------------------------------ #


def test_load_agent_skill_exists(loader: SkillLoader) -> None:
    """SKILL.md for a known agent should return non-empty content."""
    content = loader.load_agent_skill("venture-architect")
    assert content is not None
    assert len(content) > 100
    assert "Venture Architect" in content


def test_load_agent_skill_missing(loader: SkillLoader) -> None:
    """Non-existent agent should return None."""
    assert loader.load_agent_skill("nonexistent-agent-xyz") is None


# ------------------------------------------------------------------ #
# load_shared_skills
# ------------------------------------------------------------------ #


def test_load_shared_skills_returns_content(loader: SkillLoader) -> None:
    """Shared skills for a known agent should be non-empty."""
    content = loader.load_shared_skills("valuation-strategist")
    assert len(content) > 100


def test_load_shared_skills_maps_correctly(loader: SkillLoader) -> None:
    """pre-mortem-critic gets red_flags but not saas_metrics."""
    content = loader.load_shared_skills("pre-mortem-critic")
    assert "Red Flag" in content or "red flag" in content.lower()
    # saas_metrics should NOT be included for this agent
    assert "Net Revenue Retention" not in content


# ------------------------------------------------------------------ #
# load_reference
# ------------------------------------------------------------------ #


def test_load_reference_valid(loader: SkillLoader) -> None:
    """A known reference file should return its content."""
    content = loader.load_reference("venture-architect/references/lean_canvas_guide.md")
    assert content is not None
    assert "Lean Canvas" in content


def test_load_reference_missing(loader: SkillLoader) -> None:
    """Non-existent reference returns None."""
    assert loader.load_reference("venture-architect/references/does_not_exist.md") is None


def test_load_reference_path_traversal(loader: SkillLoader) -> None:
    """Path traversal attempts should be rejected."""
    assert loader.load_reference("../../etc/passwd") is None
    assert loader.load_reference("venture-architect/../../pyproject.toml") is None


# ------------------------------------------------------------------ #
# list_references
# ------------------------------------------------------------------ #


def test_list_references(loader: SkillLoader) -> None:
    """Reference listing for a known agent should return .md file names."""
    refs = loader.list_references("venture-architect")
    assert len(refs) >= 2
    assert "lean_canvas_guide.md" in refs
    assert "hypothesis_testing.md" in refs


def test_list_references_empty(loader: SkillLoader) -> None:
    """An agent without references should return an empty list."""
    # storyteller has no reference files
    refs = loader.list_references("storyteller")
    assert refs == []


# ------------------------------------------------------------------ #
# Content quality
# ------------------------------------------------------------------ #

_ALL_AGENT_IDS = [
    "venture-architect",
    "valuation-strategist",
    "market-oracle",
    "pre-mortem-critic",
    "deck-architect",
    "storyteller",
    "lean-modeler",
    "kpi-dashboard",
    "qa-simulator",
    "dataroom-concierge",
    "icp-profiler",
]


@pytest.mark.parametrize("agent_id", _ALL_AGENT_IDS)
def test_skill_files_exist(loader: SkillLoader, agent_id: str) -> None:
    """Every agent must have a SKILL.md file."""
    content = loader.load_agent_skill(agent_id)
    assert content is not None, f"Missing SKILL.md for {agent_id}"
    assert len(content) > 200, f"SKILL.md for {agent_id} is suspiciously short"


@pytest.mark.parametrize("agent_id", _ALL_AGENT_IDS)
def test_skill_files_under_token_limit(loader: SkillLoader, agent_id: str) -> None:
    """SKILL.md files should be under ~2000 tokens (~8000 chars) to fit system prompt."""
    content = loader.load_agent_skill(agent_id)
    assert content is not None
    assert len(content) < 8000, (
        f"SKILL.md for {agent_id} is {len(content)} chars — too large for system prompt"
    )
