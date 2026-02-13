from app.core.router.types import IntentCategory

KEYWORD_PATTERNS: dict[IntentCategory, list[tuple[str, float]]] = {
    IntentCategory.MARKET_RESEARCH: [
        ("tam", 2.0),
        ("sam", 2.0),
        ("som", 2.0),
        ("market size", 2.0),
        ("market research", 2.0),
        ("addressable market", 2.0),
        ("total addressable", 2.0),
        ("industry", 1.0),
        ("trend", 1.0),
        ("growth rate", 1.5),
        ("market opportunity", 1.5),
        ("market analysis", 2.0),
        ("market dynamics", 1.5),
        ("market landscape", 1.5),
        ("sector", 1.0),
        ("edtech", 1.0),
        ("fintech", 1.0),
        ("healthtech", 1.0),
        ("saas", 1.0),
    ],
    IntentCategory.COMPETITOR_ANALYSIS: [
        ("competitor", 2.0),
        ("competitors", 2.0),
        ("compare", 1.5),
        ("vs", 1.5),
        ("versus", 1.5),
        ("competitive", 2.0),
        ("competitive landscape", 2.0),
        ("alternative", 1.0),
        ("differentiation", 1.5),
        ("differentiate", 1.5),
        ("moat", 1.5),
        ("compete", 1.5),
        ("competing", 1.5),
        ("rival", 1.5),
        ("benchmark against", 1.5),
    ],
    IntentCategory.NARRATIVE: [
        ("story", 1.5),
        ("narrative", 2.0),
        ("pitch story", 2.0),
        ("founding story", 2.0),
        ("mission", 1.5),
        ("vision", 1.5),
        ("why us", 2.0),
        ("our story", 2.0),
        ("elevator pitch", 2.0),
        ("messaging", 1.0),
        ("brand story", 1.5),
        ("origin story", 2.0),
    ],
    IntentCategory.DECK: [
        ("deck", 2.0),
        ("slide", 2.0),
        ("slides", 2.0),
        ("pitch deck", 3.0),
        ("presentation", 1.5),
        ("pitch", 1.0),
        ("investor deck", 2.5),
        ("slide deck", 2.5),
        ("demo day", 1.5),
    ],
    IntentCategory.VALUATION: [
        ("valuation", 3.0),
        ("worth", 1.5),
        ("pre-money", 3.0),
        ("post-money", 3.0),
        ("cap table", 2.0),
        ("dilution", 2.0),
        ("multiple", 1.0),
        ("enterprise value", 2.0),
        ("dcf", 2.0),
        ("comparables", 1.5),
        ("what are we worth", 3.0),
        ("how much is", 1.0),
        ("equity", 1.0),
    ],
    IntentCategory.FINANCIAL: [
        ("runway", 2.0),
        ("burn rate", 2.0),
        ("revenue", 1.5),
        ("projection", 1.5),
        ("financial model", 3.0),
        ("unit economics", 2.5),
        ("cac", 2.0),
        ("ltv", 2.0),
        ("margin", 1.0),
        ("gross margin", 1.5),
        ("cash flow", 1.5),
        ("p&l", 2.0),
        ("profit", 1.0),
        ("break even", 1.5),
        ("breakeven", 1.5),
        ("cost structure", 1.5),
        ("budget", 1.0),
        ("forecast", 1.5),
        ("financial projection", 2.5),
    ],
    IntentCategory.METRICS: [
        ("kpi", 2.5),
        ("metric", 1.5),
        ("metrics", 1.5),
        ("dashboard", 2.0),
        ("tracking", 1.0),
        ("okr", 2.0),
        ("mrr", 2.0),
        ("arr", 2.0),
        ("churn", 1.5),
        ("retention", 1.0),
        ("conversion", 1.0),
        ("north star metric", 2.5),
        ("key performance", 2.0),
    ],
    IntentCategory.QA_PREP: [
        ("investor question", 3.0),
        ("q&a", 2.0),
        ("objection", 2.0),
        ("mock pitch", 2.5),
        ("tough question", 2.5),
        ("due diligence question", 2.5),
        ("prepare for questions", 2.0),
        ("investor meeting", 1.5),
        ("pitch practice", 2.0),
        ("what will investors ask", 2.5),
        ("how to answer", 1.0),
        ("common questions", 1.5),
    ],
    IntentCategory.DATAROOM: [
        ("data room", 3.0),
        ("dataroom", 3.0),
        ("due diligence", 2.0),
        ("document checklist", 2.5),
        ("diligence", 1.5),
        ("virtual data room", 3.0),
        ("diligence readiness", 2.5),
        ("fundraising documents", 2.0),
    ],
    IntentCategory.ICP: [
        ("icp", 2.5),
        ("customer profile", 2.0),
        ("persona", 2.0),
        ("target customer", 2.0),
        ("segmentation", 1.5),
        ("ideal customer", 2.5),
        ("buyer persona", 2.0),
        ("customer segment", 2.0),
        ("who is our customer", 2.0),
        ("target audience", 1.5),
        ("user persona", 2.0),
    ],
    IntentCategory.RISK: [
        ("risk", 1.5),
        ("pre-mortem", 3.0),
        ("pre mortem", 3.0),
        ("failure", 1.5),
        ("threat", 1.5),
        ("what could go wrong", 3.0),
        ("weakness", 1.5),
        ("risk analysis", 2.5),
        ("risk assessment", 2.5),
        ("downside", 1.5),
        ("worst case", 1.5),
        ("vulnerability", 1.5),
    ],
}

CONFIDENCE_NORMALIZER = 5.0


class IntentClassifier:
    """Keyword-based intent classification. No ML, no LLM — deterministic."""

    def classify(self, message: str) -> list[tuple[IntentCategory, float]]:
        """Classify message intent by keyword scoring.

        Returns sorted list of (IntentCategory, confidence) with highest first.
        Confidence is normalized to 0.0-1.0 using a fixed normalizer so that
        a single strong keyword match gives meaningful confidence.
        """
        lower = message.lower()
        scores: list[tuple[IntentCategory, float]] = []

        for category, patterns in KEYWORD_PATTERNS.items():
            raw_score = sum(
                weight for keyword, weight in patterns if keyword in lower
            )
            if raw_score > 0:
                confidence = min(raw_score / CONFIDENCE_NORMALIZER, 1.0)
                scores.append((category, round(confidence, 4)))

        if not scores:
            return [(IntentCategory.GENERAL, 0.1)]

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
