import json
from pathlib import Path
from typing import Any

from app.schemas.benchmark import BenchmarkMetric, BenchmarkResult

_DATA_DIR = Path(__file__).parent


class BenchmarkEngine:
    """Percentile-based benchmark ranking against curated startup datasets."""

    def __init__(self) -> None:
        data_path = _DATA_DIR / "benchmark_data.json"
        with open(data_path) as f:
            raw: dict[str, Any] = json.load(f)
        self._cohorts: list[dict[str, Any]] = raw["cohorts"]

    def rank(
        self,
        industry: str,
        stage: str,
        metrics: dict[str, float],
    ) -> BenchmarkResult:
        """Rank venture metrics against the matching peer cohort."""
        cohort = self._find_cohort(industry, stage)
        if cohort is None:
            return BenchmarkResult(
                peer_cohort=f"{stage} {industry} (no data)",
                cohort_size=0,
                metrics=[],
                strengths=[],
                weaknesses=[],
            )

        companies: list[dict[str, float]] = cohort["companies"]
        label: str = cohort["label"]

        benchmark_metrics: list[BenchmarkMetric] = []
        strengths: list[str] = []
        weaknesses: list[str] = []

        # Get all available metric names from the cohort
        all_metric_names: set[str] = set()
        for c in companies:
            all_metric_names.update(c.keys())

        for metric_name in sorted(all_metric_names):
            values = [c[metric_name] for c in companies if metric_name in c]
            if not values:
                continue

            sorted_values = sorted(values)
            p25 = self._percentile(sorted_values, 25)
            median = self._percentile(sorted_values, 50)
            p75 = self._percentile(sorted_values, 75)

            venture_value = metrics.get(metric_name)
            if venture_value is not None:
                pctile = self._compute_percentile(sorted_values, venture_value)
                status = self._classify(pctile)
            else:
                pctile = 50.0  # neutral if not provided
                status = "average"

            bm = BenchmarkMetric(
                metric_name=metric_name,
                venture_value=venture_value,
                peer_median=round(median, 2),
                peer_p25=round(p25, 2),
                peer_p75=round(p75, 2),
                percentile=round(pctile, 1),
                status=status,
            )
            benchmark_metrics.append(bm)

            if venture_value is not None:
                pretty_name = metric_name.replace("_", " ").title()
                if status == "strong":
                    strengths.append(f"{pretty_name} (p{pctile:.0f})")
                elif status == "weak":
                    weaknesses.append(f"{pretty_name} (p{pctile:.0f})")

        return BenchmarkResult(
            peer_cohort=label,
            cohort_size=len(companies),
            metrics=benchmark_metrics,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    def _find_cohort(
        self, industry: str, stage: str,
    ) -> dict[str, Any] | None:
        """Find matching cohort by industry + stage."""
        industry_lower = industry.lower()
        stage_lower = stage.lower()
        for cohort in self._cohorts:
            if cohort["industry"] == industry_lower and cohort["stage"] == stage_lower:
                return cohort
        return None

    @staticmethod
    def _percentile(sorted_values: list[float], pct: float) -> float:
        """Linear interpolation percentile."""
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]
        k = (pct / 100) * (n - 1)
        f = int(k)
        c = min(f + 1, n - 1)
        d = k - f
        return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])

    @staticmethod
    def _compute_percentile(sorted_values: list[float], value: float) -> float:
        """Compute where a value falls in the distribution (0-100)."""
        n = len(sorted_values)
        if n == 0:
            return 50.0
        count_below = sum(1 for v in sorted_values if v < value)
        count_equal = sum(1 for v in sorted_values if v == value)
        return ((count_below + 0.5 * count_equal) / n) * 100

    @staticmethod
    def _classify(percentile: float) -> str:
        """Classify based on percentile: top quartile = strong, bottom = weak."""
        if percentile >= 75:
            return "strong"
        if percentile <= 25:
            return "weak"
        return "average"


benchmark_engine = BenchmarkEngine()
