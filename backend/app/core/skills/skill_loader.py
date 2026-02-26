"""Skill file loader for the agent domain expertise system.

Reads agent-specific SKILL.md files and shared knowledge from the
backend/app/skills/ directory tree.
"""

from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger()

# Root of the skills content directory
_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

# Maps each agent to the shared skill files it should receive in its system
# prompt.  Every agent gets vc_fundamentals and fundraising_stages; others
# are attached based on relevance.
_SHARED_SKILLS_MAP: dict[str, list[str]] = {
    "venture-architect": [
        "vc_fundamentals.md",
        "fundraising_stages.md",
        "market_sizing.md",
    ],
    "valuation-strategist": [
        "vc_fundamentals.md",
        "fundraising_stages.md",
        "saas_metrics.md",
    ],
    "market-oracle": [
        "market_sizing.md",
        "saas_metrics.md",
    ],
    "pre-mortem-critic": [
        "vc_fundamentals.md",
        "red_flags.md",
    ],
    "deck-architect": [
        "vc_fundamentals.md",
        "fundraising_stages.md",
    ],
    "storyteller": [
        "vc_fundamentals.md",
        "fundraising_stages.md",
    ],
    "lean-modeler": [
        "saas_metrics.md",
        "vc_fundamentals.md",
    ],
    "kpi-dashboard": [
        "saas_metrics.md",
        "fundraising_stages.md",
    ],
    "qa-simulator": [
        "vc_fundamentals.md",
        "fundraising_stages.md",
        "red_flags.md",
    ],
    "dataroom-concierge": [
        "fundraising_stages.md",
        "red_flags.md",
    ],
    "icp-profiler": [
        "market_sizing.md",
        "saas_metrics.md",
    ],
}


class SkillLoader:
    """Load agent skill files from the filesystem."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        self._skills_dir = skills_dir or _SKILLS_DIR

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def load_agent_skill(self, agent_id: str) -> str | None:
        """Return the content of an agent's SKILL.md, or *None* if missing."""
        path = self._skills_dir / agent_id / "SKILL.md"
        return self._read_file(path)

    def load_shared_skills(self, agent_id: str) -> str:
        """Return concatenated shared skill content relevant to *agent_id*."""
        filenames = _SHARED_SKILLS_MAP.get(agent_id, [])
        parts: list[str] = []
        for fname in filenames:
            content = self._read_file(self._skills_dir / "shared" / fname)
            if content:
                parts.append(content)
        return "\n\n---\n\n".join(parts)

    def load_reference(self, reference_path: str) -> str | None:
        """Load a reference file by relative path.

        Example: ``venture-architect/references/lean_canvas_guide.md``

        Validates that the resolved path stays within the skills directory to
        prevent path-traversal attacks.
        """
        resolved = (self._skills_dir / reference_path).resolve()
        skills_root = str(self._skills_dir.resolve())
        if not str(resolved).startswith(skills_root):
            logger.warning("skill_path_traversal_blocked", path=reference_path)
            return None
        return self._read_file(resolved)

    def list_references(self, agent_id: str) -> list[str]:
        """List available reference file names for *agent_id*."""
        ref_dir = self._skills_dir / agent_id / "references"
        if not ref_dir.is_dir():
            return []
        return sorted(
            f.name for f in ref_dir.iterdir() if f.suffix == ".md" and f.is_file()
        )

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    @staticmethod
    def _read_file(path: Path) -> str | None:
        """Read a file safely, returning *None* on any error."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None


# Global singleton
skill_loader = SkillLoader()
