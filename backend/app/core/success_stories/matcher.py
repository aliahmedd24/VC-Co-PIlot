import json
from pathlib import Path
from typing import Any

from app.schemas.benchmark import SuccessStoryMatch, SuccessStoryResult

_DATA_DIR = Path(__file__).parent

# Weights for similarity calculation
_WEIGHTS = {
    "industry": 0.30,
    "stage": 0.15,
    "business_model": 0.25,
    "traits": 0.30,
}


class SuccessStoryMatcher:
    """Attribute-based similarity matching against curated startup success stories."""

    def __init__(self) -> None:
        data_path = _DATA_DIR / "stories_data.json"
        with open(data_path) as f:
            raw: dict[str, Any] = json.load(f)
        self._stories: list[dict[str, Any]] = raw["stories"]

    def match(
        self,
        industry: str,
        stage: str = "",
        business_model: str = "",
        attributes: dict[str, str] | None = None,
        top_n: int = 5,
    ) -> SuccessStoryResult:
        """Find top N most similar success stories."""
        scored: list[tuple[float, dict[str, Any]]] = []
        venture_traits = set((attributes or {}).get("traits", "").lower().split(","))
        venture_traits = {t.strip() for t in venture_traits if t.strip()}

        for story in self._stories:
            sim = self._compute_similarity(
                industry, stage, business_model, venture_traits, story,
            )
            scored.append((sim, story))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_n]

        matches: list[SuccessStoryMatch] = []
        for sim_score, story in top:
            parallels = self._find_parallels(industry, stage, business_model, story)
            differences = self._find_differences(industry, stage, business_model, story)
            matches.append(SuccessStoryMatch(
                name=story["name"],
                industry=story["industry"],
                stage=story["stage"],
                similarity_score=round(sim_score, 3),
                parallels=parallels,
                differences=differences,
                key_traits=story.get("key_traits", []),
            ))

        return SuccessStoryResult(
            matches=matches,
            venture_summary=f"{industry} venture at {stage} stage",
        )

    def _compute_similarity(
        self,
        industry: str,
        stage: str,
        business_model: str,
        venture_traits: set[str],
        story: dict[str, Any],
    ) -> float:
        """Weighted similarity score between venture and story."""
        score = 0.0

        # Industry match
        if industry.lower() == story["industry"].lower():
            score += _WEIGHTS["industry"]
        elif self._industries_related(industry.lower(), story["industry"].lower()):
            score += _WEIGHTS["industry"] * 0.5

        # Stage proximity
        stage_dist = self._stage_distance(stage, story.get("stage", ""))
        stage_sim = max(0, 1.0 - stage_dist * 0.25)
        score += _WEIGHTS["stage"] * stage_sim

        # Business model
        if business_model and business_model.lower() == story.get("business_model", "").lower():
            score += _WEIGHTS["business_model"]
        elif business_model and self._model_partial_match(
            business_model.lower(), story.get("business_model", "").lower()
        ):
            score += _WEIGHTS["business_model"] * 0.4

        # Trait overlap
        story_traits = set(story.get("key_traits", []))
        if venture_traits and story_traits:
            overlap = len(venture_traits & story_traits)
            total = len(venture_traits | story_traits)
            score += _WEIGHTS["traits"] * (overlap / total) if total > 0 else 0

        return min(score, 1.0)

    @staticmethod
    def _industries_related(a: str, b: str) -> bool:
        """Check if two industries are adjacent/related."""
        related_groups = [
            {"saas", "deeptech"},
            {"fintech", "saas"},
            {"healthtech", "saas"},
            {"ecommerce", "marketplace"},
            {"edtech", "saas"},
        ]
        return any(a in group and b in group for group in related_groups)

    @staticmethod
    def _stage_distance(a: str, b: str) -> int:
        """Ordinal distance between stages."""
        stages = ["pre_seed", "seed", "series_a", "series_b", "growth", "exit"]
        try:
            ia = stages.index(a.lower())
        except ValueError:
            ia = 1
        try:
            ib = stages.index(b.lower())
        except ValueError:
            ib = 1
        return abs(ia - ib)

    @staticmethod
    def _model_partial_match(a: str, b: str) -> bool:
        """Check for partial business model match."""
        keywords_a = set(a.replace("_", " ").split())
        keywords_b = set(b.replace("_", " ").split())
        return len(keywords_a & keywords_b) > 0

    @staticmethod
    def _find_parallels(
        industry: str, stage: str, business_model: str, story: dict[str, Any],
    ) -> list[str]:
        """Identify parallels between venture and story."""
        parallels: list[str] = []
        if industry.lower() == story["industry"].lower():
            parallels.append(f"Same industry: {industry}")
        if business_model and business_model.lower() in story.get("business_model", "").lower():
            parallels.append(f"Similar business model: {story.get('business_model', '')}")
        if not parallels:
            parallels.append(f"Related market opportunity ({story.get('market', 'tech')})")
        return parallels

    @staticmethod
    def _find_differences(
        industry: str, stage: str, business_model: str, story: dict[str, Any],
    ) -> list[str]:
        """Identify key differences."""
        diffs: list[str] = []
        if industry.lower() != story["industry"].lower():
            diffs.append(f"Different industry ({story['industry']})")
        if story.get("peak_valuation", 0) > 10_000_000_000:
            diffs.append(f"Much larger scale (${story['peak_valuation'] / 1e9:.0f}B peak)")
        return diffs


success_story_matcher = SuccessStoryMatcher()
