from pathlib import Path
from typing import Any

import yaml

from app.models.kg_entity import KGEntityType
from app.schemas.brain import EntityResult
from app.schemas.scoring import InvestorReadinessScore, ReadinessDimension

_RUBRIC_PATH = Path(__file__).parent / "scoring_rubric.yaml"


class InvestorReadinessScorer:
    """Score venture investor-readiness across 5 dimensions using KG data."""

    def __init__(self, rubric_path: Path | None = None) -> None:
        path = rubric_path or _RUBRIC_PATH
        with open(path) as f:
            raw: dict[str, Any] = yaml.safe_load(f)
        self._dimensions: dict[str, dict[str, Any]] = raw["dimensions"]
        self._grades: list[dict[str, Any]] = raw["grades"]

        # Validate weights sum to 1.0
        total = sum(float(d["weight"]) for d in self._dimensions.values())
        if abs(total - 1.0) > 0.01:
            msg = f"Scoring rubric weights sum to {total}, expected 1.0"
            raise ValueError(msg)

    def score(
        self,
        entities: list[EntityResult],
        venture_name: str | None = None,
        venture_stage: str | None = None,
        venture_one_liner: str | None = None,
        venture_problem: str | None = None,
        venture_solution: str | None = None,
    ) -> InvestorReadinessScore:
        """Evaluate readiness across all dimensions."""
        # Build lookup structures
        entity_types_present: set[str] = set()
        entity_counts: dict[str, int] = {}
        entity_names: set[str] = set()

        for entity in entities:
            t = entity.type.value if isinstance(entity.type, KGEntityType) else str(entity.type)
            entity_types_present.add(t)
            entity_counts[t] = entity_counts.get(t, 0) + 1
            name = entity.data.get("name", "")
            if name:
                entity_names.add(name.lower())

        venture_fields: dict[str, bool] = {
            "problem": bool(venture_problem),
            "solution": bool(venture_solution),
            "one_liner": bool(venture_one_liner),
            "venture_name": bool(venture_name),
            "stage": bool(venture_stage),
        }

        dimensions: list[ReadinessDimension] = []
        for dim_key, dim_config in self._dimensions.items():
            dim = self._score_dimension(
                dim_key,
                dim_config,
                entity_types_present,
                entity_counts,
                entity_names,
                venture_fields,
                len(entities),
            )
            dimensions.append(dim)

        overall = sum(d.score * d.weight for d in dimensions)
        grade = self._assign_grade(overall)

        # Top priority actions = gaps from lowest-scoring dimensions
        sorted_dims = sorted(dimensions, key=lambda d: d.score)
        top_actions: list[str] = []
        for dim in sorted_dims[:3]:
            for gap in dim.gaps[:2]:
                top_actions.append(gap)
            if not dim.gaps:
                for rec in dim.recommendations[:1]:
                    top_actions.append(rec)

        summary = self._generate_summary(overall, grade, dimensions)

        return InvestorReadinessScore(
            overall_score=round(overall, 1),
            grade=grade,
            dimensions=dimensions,
            summary=summary,
            top_priority_actions=top_actions[:5],
        )

    def _score_dimension(
        self,
        dim_key: str,
        config: dict[str, Any],
        entity_types: set[str],
        entity_counts: dict[str, int],
        entity_names: set[str],
        venture_fields: dict[str, bool],
        total_entities: int,
    ) -> ReadinessDimension:
        """Score a single dimension based on its checks."""
        weight = float(config["weight"])
        checks: list[dict[str, Any]] = config["checks"]
        total_points = sum(int(c["points"]) for c in checks)
        earned_points = 0
        gaps: list[str] = []
        recommendations: list[str] = []

        for check in checks:
            source = check["source"]
            points = int(check["points"])
            label = str(check["label"])
            passed = False

            if source == "venture_fields":
                field = check["field"]
                passed = venture_fields.get(field, False)

            elif source == "entity_type":
                field = check["field"]
                passed = field in entity_types

            elif source == "entity_count_min":
                et = check["entity_type"]
                min_count = int(check["min_count"])
                passed = entity_counts.get(et, 0) >= min_count

            elif source == "metric_has_name":
                match_name = check.get("match_name", "").lower()
                passed = match_name in entity_names

            elif source == "total_entity_min":
                min_count = int(check["min_count"])
                passed = total_entities >= min_count

            if passed:
                earned_points += points
            else:
                gaps.append(f"Missing: {label}")
                recommendations.append(f"Add {label.lower()} to improve {config['label']} score.")

        score = (earned_points / total_points * 100) if total_points > 0 else 0

        return ReadinessDimension(
            name=config["label"],
            score=round(score, 1),
            weight=weight,
            gaps=gaps,
            recommendations=recommendations,
        )

    def _assign_grade(self, score: float) -> str:
        """Map overall score to letter grade."""
        for grade_def in self._grades:
            if score >= grade_def["min_score"]:
                return str(grade_def["grade"])
        return "F"

    @staticmethod
    def _generate_summary(
        score: float, grade: str, dimensions: list[ReadinessDimension],
    ) -> str:
        """Generate a narrative summary of the readiness assessment."""
        strong = [d.name for d in dimensions if d.score >= 75]
        weak = [d.name for d in dimensions if d.score < 50]

        parts = [f"Overall investor readiness: {score:.0f}/100 (Grade: {grade})."]
        if strong:
            parts.append(f"Strong areas: {', '.join(strong)}.")
        if weak:
            parts.append(f"Needs improvement: {', '.join(weak)}.")
        if not weak:
            parts.append("All dimensions are in good shape.")

        return " ".join(parts)


readiness_scorer = InvestorReadinessScorer()
