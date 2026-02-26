import re
import time

from app.core.router.intent_classifier import IntentClassifier
from app.core.router.types import IntentCategory, ModelProfile, RoutingPlan
from app.core.tools.registry import tool_registry
from app.models.venture import VentureStage

MENTION_ALIASES: dict[str, str] = {
    "@venture": "venture-architect",
    "@market": "market-oracle",
    "@story": "storyteller",
    "@deck": "deck-architect",
    "@valuation": "valuation-strategist",
    "@qa": "qa-simulator",
    "@dataroom": "dataroom-concierge",
    "@kpi": "kpi-dashboard",
    "@icp": "icp-profiler",
    "@risk": "pre-mortem-critic",
}

INTENT_AGENT_MAP: dict[IntentCategory, str] = {
    IntentCategory.MARKET_RESEARCH: "market-oracle",
    IntentCategory.COMPETITOR_ANALYSIS: "market-oracle",
    IntentCategory.NARRATIVE: "storyteller",
    IntentCategory.DECK: "deck-architect",
    IntentCategory.VALUATION: "valuation-strategist",
    IntentCategory.FINANCIAL: "lean-modeler",
    IntentCategory.METRICS: "kpi-dashboard",
    IntentCategory.QA_PREP: "qa-simulator",
    IntentCategory.DATAROOM: "dataroom-concierge",
    IntentCategory.ICP: "icp-profiler",
    IntentCategory.RISK: "pre-mortem-critic",
    IntentCategory.GENERAL: "venture-architect",
}

STAGE_OVERRIDES: dict[tuple[IntentCategory, VentureStage], str] = {
    (IntentCategory.VALUATION, VentureStage.IDEATION): "venture-architect",
    (IntentCategory.VALUATION, VentureStage.PRE_SEED): "lean-modeler",
}

AGENT_MODEL_PROFILES: dict[str, ModelProfile] = {
    "venture-architect": ModelProfile.REASONING_HEAVY,
    "market-oracle": ModelProfile.REASONING_HEAVY,
    "storyteller": ModelProfile.WRITING_POLISH,
    "deck-architect": ModelProfile.WRITING_POLISH,
    "valuation-strategist": ModelProfile.REASONING_HEAVY,
    "lean-modeler": ModelProfile.REASONING_HEAVY,
    "kpi-dashboard": ModelProfile.TOOL_USING,
    "qa-simulator": ModelProfile.FAST_RESPONSE,
    "dataroom-concierge": ModelProfile.TOOL_USING,
    "icp-profiler": ModelProfile.REASONING_HEAVY,
    "pre-mortem-critic": ModelProfile.REASONING_HEAVY,
}

ARTIFACT_AGENTS: set[str] = {
    "venture-architect",
    "market-oracle",
    "storyteller",
    "deck-architect",
    "valuation-strategist",
    "lean-modeler",
    "kpi-dashboard",
    "dataroom-concierge",
    "icp-profiler",
    "pre-mortem-critic",
}

MENTION_PATTERN = re.compile(r"@(\w+)")


class MoERouter:
    """Mixture-of-Experts router. Deterministic keyword-based — no LLM calls."""

    def __init__(self, classifier: IntentClassifier | None = None) -> None:
        self.classifier = classifier or IntentClassifier()

    def route(
        self,
        message: str,
        venture_stage: VentureStage,
        active_artifact_agent: str | None = None,
        override_agent: str | None = None,
    ) -> RoutingPlan:
        """Route a user message to the appropriate agent.

        Priority: override_agent > @mention > artifact continuation > classifier > fallback.
        """
        start = time.perf_counter()

        # 1. Explicit override
        if override_agent:
            return self._build_plan(
                agent_id=override_agent,
                confidence=1.0,
                reasoning=f"User override: {override_agent}",
                start_time=start,
            )

        # 2. @mention check
        mentions = MENTION_PATTERN.findall(message.lower())
        for mention in mentions:
            alias = f"@{mention}"
            if alias in MENTION_ALIASES:
                return self._build_plan(
                    agent_id=MENTION_ALIASES[alias],
                    confidence=1.0,
                    reasoning=f"Explicit mention: {alias}",
                    start_time=start,
                )

        # 3. Artifact continuation
        if active_artifact_agent:
            return self._build_plan(
                agent_id=active_artifact_agent,
                confidence=0.95,
                reasoning=f"Artifact continuation: {active_artifact_agent}",
                start_time=start,
            )

        # 4. Intent classification
        intents = self.classifier.classify(message)
        top_intent, top_confidence = intents[0]

        # 5. Stage overrides
        agent_id = INTENT_AGENT_MAP.get(top_intent, "venture-architect")
        override_key = (top_intent, venture_stage)
        if override_key in STAGE_OVERRIDES:
            agent_id = STAGE_OVERRIDES[override_key]

        # 6. Low confidence fallback
        if top_confidence < 0.3:
            agent_id = "venture-architect"

        return self._build_plan(
            agent_id=agent_id,
            confidence=top_confidence,
            reasoning=f"Intent: {top_intent.value} (confidence: {top_confidence})",
            start_time=start,
        )

    def _build_plan(
        self,
        agent_id: str,
        confidence: float,
        reasoning: str,
        start_time: float,
    ) -> RoutingPlan:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return RoutingPlan(
            selected_agent=agent_id,
            model_profile=AGENT_MODEL_PROFILES.get(agent_id, ModelProfile.DEFAULT),
            tools=tool_registry.get_tool_names_for_agent(agent_id),
            artifact_needed=agent_id in ARTIFACT_AGENTS,
            fallback_agent="venture-architect",
            confidence=confidence,
            reasoning=reasoning,
            latency_ms=round(elapsed_ms, 2),
        )


moe_router = MoERouter()
