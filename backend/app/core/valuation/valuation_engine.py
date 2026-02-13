import json
from pathlib import Path
from typing import Any

from app.schemas.valuation import ValuationMethodResult, ValuationRequest, ValuationResult

_DATA_DIR = Path(__file__).parent


class ValuationEngine:
    """Pure-Python startup valuation calculator with 3 methods."""

    def __init__(self) -> None:
        data_path = _DATA_DIR / "multiples_data.json"
        with open(data_path) as f:
            raw: dict[str, Any] = json.load(f)
        self._multiples: dict[str, dict[str, dict[str, float]]] = raw["industry_multiples"]
        self._growth_premium: list[dict[str, float]] = raw["growth_premium"]["ranges"]

    def valuate(self, request: ValuationRequest) -> ValuationResult:
        """Run all applicable valuation methods and return combined result."""
        methods: list[ValuationMethodResult] = []
        warnings: list[str] = []

        rev_result = self._revenue_multiple(request)
        if rev_result is not None:
            methods.append(rev_result)
        else:
            warnings.append("Revenue multiple skipped: revenue data required.")

        dcf_result = self._dcf_simplified(request)
        if dcf_result is not None:
            methods.append(dcf_result)
        else:
            warnings.append("DCF skipped: revenue and growth rate required.")

        comp_result = self._comparable_analysis(request)
        if comp_result is not None:
            methods.append(comp_result)
        else:
            warnings.append("Comparable analysis skipped: comparable exits required.")

        if not methods:
            return ValuationResult(
                low=0, mid=0, high=0, methods=[], warnings=warnings,
            )

        avg_low = sum(m.low for m in methods) / len(methods)
        avg_mid = sum(m.mid for m in methods) / len(methods)
        avg_high = sum(m.high for m in methods) / len(methods)

        return ValuationResult(
            low=round(avg_low, 2),
            mid=round(avg_mid, 2),
            high=round(avg_high, 2),
            methods=methods,
            warnings=warnings,
        )

    def _get_multiples(
        self, industry: str, stage: str,
    ) -> dict[str, float]:
        """Look up revenue multiples for industry/stage, falling back to defaults."""
        industry_key = industry.lower()
        stage_key = stage.lower()
        ind_data = self._multiples.get(industry_key, self._multiples["default"])
        return ind_data.get(stage_key, ind_data.get("seed", {"low": 6, "mid": 10, "high": 18}))

    def _get_growth_multiplier(self, growth_rate: float) -> float:
        """Return a premium multiplier based on growth rate."""
        for bracket in self._growth_premium:
            if bracket["min_growth"] <= growth_rate < bracket["max_growth"]:
                return bracket["multiplier"]
        return 1.0

    def _revenue_multiple(self, req: ValuationRequest) -> ValuationMethodResult | None:
        """Valuation = Revenue * Multiple (adjusted for growth)."""
        if req.revenue is None or req.revenue <= 0:
            return None

        multiples = self._get_multiples(req.industry, req.stage)
        growth_mult = self._get_growth_multiplier(req.growth_rate or 0.0)

        low = req.revenue * multiples["low"] * growth_mult
        mid = req.revenue * multiples["mid"] * growth_mult
        high = req.revenue * multiples["high"] * growth_mult

        return ValuationMethodResult(
            method="revenue_multiple",
            low=round(low, 2),
            mid=round(mid, 2),
            high=round(high, 2),
            details={
                "base_multiple_low": multiples["low"],
                "base_multiple_mid": multiples["mid"],
                "base_multiple_high": multiples["high"],
                "growth_multiplier": growth_mult,
                "industry": req.industry,
                "stage": req.stage,
            },
        )

    def _dcf_simplified(self, req: ValuationRequest) -> ValuationMethodResult | None:
        """Simplified DCF: project revenue forward, discount back."""
        if req.revenue is None or req.revenue <= 0:
            return None
        if req.growth_rate is None:
            return None

        discount = req.discount_rate
        years = req.projection_years
        growth = req.growth_rate

        # Project cash flows (assume 15% margin low, 25% mid, 35% high)
        margins = {"low": 0.15, "mid": 0.25, "high": 0.35}
        results: dict[str, float] = {}

        for label, margin in margins.items():
            pv_total = 0.0
            projected_rev = req.revenue
            for year in range(1, years + 1):
                projected_rev *= (1 + growth)
                cash_flow = projected_rev * margin
                pv = cash_flow / ((1 + discount) ** year)
                pv_total += pv

            # Terminal value (exit multiple of 5x final year revenue)
            terminal = projected_rev * 5 / ((1 + discount) ** years)
            results[label] = round(pv_total + terminal, 2)

        return ValuationMethodResult(
            method="dcf_simplified",
            low=results["low"],
            mid=results["mid"],
            high=results["high"],
            details={
                "discount_rate": discount,
                "projection_years": years,
                "growth_rate": growth,
                "terminal_multiple": 5.0,
            },
        )

    def _comparable_analysis(self, req: ValuationRequest) -> ValuationMethodResult | None:
        """Use provided comparable exit valuations to derive a range."""
        if not req.comparable_exits or len(req.comparable_exits) == 0:
            return None

        sorted_exits = sorted(req.comparable_exits)
        n = len(sorted_exits)

        median = self._percentile(sorted_exits, 50)
        p25 = self._percentile(sorted_exits, 25)
        p75 = self._percentile(sorted_exits, 75)

        warnings: list[str] = []
        if n < 3:
            warnings.append(f"Only {n} comparable(s) provided; results may be unreliable.")

        return ValuationMethodResult(
            method="comparable_analysis",
            low=round(p25, 2),
            mid=round(median, 2),
            high=round(p75, 2),
            details={"comparable_count": n, "min": sorted_exits[0], "max": sorted_exits[-1]},
            warnings=warnings,
        )

    @staticmethod
    def _percentile(sorted_values: list[float], pct: float) -> float:
        """Linear interpolation percentile on a sorted list."""
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]
        k = (pct / 100) * (n - 1)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f
        return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])


valuation_engine = ValuationEngine()
