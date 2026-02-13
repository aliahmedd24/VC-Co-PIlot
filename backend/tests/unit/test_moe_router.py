from app.core.router.moe_router import MoERouter
from app.models.venture import VentureStage


def test_explicit_mention_routing() -> None:
    router = MoERouter()
    plan = router.route("@deck make slides", VentureStage.SEED)
    assert plan.selected_agent == "deck-architect"
    assert plan.confidence == 1.0


def test_artifact_continuation() -> None:
    router = MoERouter()
    plan = router.route(
        "Continue working on this",
        VentureStage.SEED,
        active_artifact_agent="storyteller",
    )
    assert plan.selected_agent == "storyteller"
    assert plan.confidence == 0.95


def test_stage_override_ideation() -> None:
    router = MoERouter()
    plan = router.route("What's our valuation?", VentureStage.IDEATION)
    assert plan.selected_agent == "venture-architect"


def test_stage_override_pre_seed() -> None:
    router = MoERouter()
    plan = router.route("What's our valuation?", VentureStage.PRE_SEED)
    assert plan.selected_agent == "lean-modeler"


def test_router_latency() -> None:
    """100 sequential calls complete in < 20s total (< 200ms average)."""
    router = MoERouter()
    messages = [
        "What's the TAM?",
        "Compare us vs Notion",
        "Help me with my pitch deck",
        "Calculate our runway",
        "Risk assessment please",
    ]
    total_plans = []
    for _ in range(20):
        for msg in messages:
            plan = router.route(msg, VentureStage.SEED)
            total_plans.append(plan)

    assert len(total_plans) == 100
    total_latency = sum(p.latency_ms for p in total_plans)
    assert total_latency < 20000, f"Total latency {total_latency}ms >= 20s"


def test_override_agent() -> None:
    router = MoERouter()
    plan = router.route(
        "Tell me about the market",
        VentureStage.SEED,
        override_agent="qa-simulator",
    )
    assert plan.selected_agent == "qa-simulator"
    assert plan.confidence == 1.0


def test_unknown_alias_ignored() -> None:
    router = MoERouter()
    plan = router.route("@nonexistent do something", VentureStage.SEED)
    # Falls through to classifier (no valid mention match)
    assert plan.selected_agent != "nonexistent"
