from app.core.router.intent_classifier import IntentClassifier
from app.core.router.types import IntentCategory


def _top_intent(message: str) -> IntentCategory:
    """Helper: return the top-scoring intent for a message."""
    classifier = IntentClassifier()
    results = classifier.classify(message)
    return results[0][0]


def _top_confidence(message: str) -> float:
    """Helper: return the confidence of the top intent."""
    classifier = IntentClassifier()
    results = classifier.classify(message)
    return results[0][1]


def test_market_research_keywords() -> None:
    assert _top_intent("What's the TAM for edtech?") == IntentCategory.MARKET_RESEARCH


def test_competitor_keywords() -> None:
    assert _top_intent("Compare us vs Notion") == IntentCategory.COMPETITOR_ANALYSIS


def test_valuation_keywords() -> None:
    assert _top_intent("What are we worth?") == IntentCategory.VALUATION


def test_deck_keywords() -> None:
    assert _top_intent("Help me build my pitch deck") == IntentCategory.DECK


def test_financial_keywords() -> None:
    assert _top_intent("Calculate our runway") == IntentCategory.FINANCIAL


def test_general_fallback() -> None:
    classifier = IntentClassifier()
    results = classifier.classify("Hello, how are you?")
    top_category, top_confidence = results[0]
    assert top_category == IntentCategory.GENERAL
    assert top_confidence < 0.3


def test_multi_intent_picks_strongest() -> None:
    # "Compare our valuation against competitors" has both VALUATION and COMPETITOR keywords
    classifier = IntentClassifier()
    results = classifier.classify("Compare our valuation against competitors")
    # Should return a list with highest-scored intent first
    assert len(results) >= 2
    top_category = results[0][0]
    assert top_category in (IntentCategory.VALUATION, IntentCategory.COMPETITOR_ANALYSIS)
    # Highest confidence should be >= second
    assert results[0][1] >= results[1][1]


def test_classification_accuracy_benchmark() -> None:
    """Run 50 labeled test cases, assert >= 80% correct."""
    test_cases: list[tuple[str, IntentCategory]] = [
        # MARKET_RESEARCH (5)
        ("What's the TAM for edtech?", IntentCategory.MARKET_RESEARCH),
        ("How big is the addressable market?", IntentCategory.MARKET_RESEARCH),
        ("What are the industry trends?", IntentCategory.MARKET_RESEARCH),
        ("Market size analysis for SaaS", IntentCategory.MARKET_RESEARCH),
        ("Growth rate of the healthtech sector", IntentCategory.MARKET_RESEARCH),
        # COMPETITOR_ANALYSIS (5)
        ("Compare us versus Notion", IntentCategory.COMPETITOR_ANALYSIS),
        ("Who are our competitors?", IntentCategory.COMPETITOR_ANALYSIS),
        ("What's our competitive moat?", IntentCategory.COMPETITOR_ANALYSIS),
        ("How do we differentiate from alternatives?", IntentCategory.COMPETITOR_ANALYSIS),
        ("Competitive landscape analysis", IntentCategory.COMPETITOR_ANALYSIS),
        # NARRATIVE (5)
        ("Help me write our founding story", IntentCategory.NARRATIVE),
        ("Craft a compelling pitch narrative", IntentCategory.NARRATIVE),
        ("What's our mission and vision?", IntentCategory.NARRATIVE),
        ("Create an elevator pitch", IntentCategory.NARRATIVE),
        ("Write our brand story", IntentCategory.NARRATIVE),
        # DECK (5)
        ("Build a pitch deck", IntentCategory.DECK),
        ("Help with my investor deck slides", IntentCategory.DECK),
        ("Create a slide deck for demo day", IntentCategory.DECK),
        ("Improve our presentation", IntentCategory.DECK),
        ("What slides should be in our pitch deck?", IntentCategory.DECK),
        # VALUATION (5)
        ("What's our pre-money valuation?", IntentCategory.VALUATION),
        ("Calculate our post-money valuation", IntentCategory.VALUATION),
        ("What are we worth at this stage?", IntentCategory.VALUATION),
        ("Cap table and dilution analysis", IntentCategory.VALUATION),
        ("How should we value our company?", IntentCategory.VALUATION),
        # FINANCIAL (5)
        ("Calculate our runway and burn rate", IntentCategory.FINANCIAL),
        ("Build a financial model", IntentCategory.FINANCIAL),
        ("What are our unit economics?", IntentCategory.FINANCIAL),
        ("Revenue projection for next year", IntentCategory.FINANCIAL),
        ("What's our CAC to LTV ratio?", IntentCategory.FINANCIAL),
        # METRICS (4)
        ("What KPIs should we track?", IntentCategory.METRICS),
        ("Help me set up a metrics dashboard", IntentCategory.METRICS),
        ("Our MRR and churn metrics", IntentCategory.METRICS),
        ("Define our north star metric", IntentCategory.METRICS),
        # QA_PREP (4)
        ("Prepare for tough investor questions", IntentCategory.QA_PREP),
        ("What will investors ask about our model?", IntentCategory.QA_PREP),
        ("Mock pitch practice session", IntentCategory.QA_PREP),
        ("How to handle objections from VCs?", IntentCategory.QA_PREP),
        # DATAROOM (3)
        ("Set up our data room", IntentCategory.DATAROOM),
        ("What documents do we need for due diligence?", IntentCategory.DATAROOM),
        ("Create a dataroom document checklist", IntentCategory.DATAROOM),
        # ICP (4)
        ("Define our ideal customer profile", IntentCategory.ICP),
        ("Who is our target customer?", IntentCategory.ICP),
        ("Create buyer personas", IntentCategory.ICP),
        ("Customer segmentation analysis", IntentCategory.ICP),
        # RISK (4)
        ("Run a pre-mortem analysis", IntentCategory.RISK),
        ("What could go wrong with our plan?", IntentCategory.RISK),
        ("Risk assessment for our venture", IntentCategory.RISK),
        ("Identify potential weaknesses and threats", IntentCategory.RISK),
        # GENERAL (1)
        ("Hello, can you help me?", IntentCategory.GENERAL),
    ]

    assert len(test_cases) == 50

    correct = 0
    for message, expected in test_cases:
        predicted = _top_intent(message)
        if predicted == expected:
            correct += 1

    accuracy = correct / len(test_cases)
    assert accuracy >= 0.80, f"Accuracy {accuracy:.0%} < 80% ({correct}/50 correct)"
