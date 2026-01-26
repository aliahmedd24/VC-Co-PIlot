"""Agent router with intent classification."""

from typing import Any

from app.core.agents.base import BaseAgent
from app.core.agents.competitive_intel_agent import CompetitiveIntelAgent
from app.core.agents.dataroom_concierge_agent import DataroomConciergeAgent
from app.core.agents.deck_architect_agent import DeckArchitectAgent
from app.core.agents.general_agent import GeneralAgent
from app.core.agents.icp_profiler_agent import ICPProfilerAgent
from app.core.agents.kpi_dashboard_agent import KPIDashboardAgent
from app.core.agents.lean_modeler_agent import LeanModelerAgent
from app.core.agents.llm_client import LLMClient, get_llm_client
from app.core.agents.market_research_agent import MarketResearchAgent
from app.core.agents.pre_mortem_critic_agent import PreMortemCriticAgent
from app.core.agents.qa_simulator_agent import QASimulatorAgent
from app.core.agents.response import AgentResponse
from app.core.agents.storyteller_agent import StorytellerAgent
from app.core.agents.valuation_strategist_agent import ValuationStrategistAgent
from app.core.agents.venture_analyst_agent import VentureAnalystAgent
from app.core.agents.venture_architect_agent import VentureArchitectAgent
from app.core.brain.startup_brain import StartupBrain

# Intent classification prompt
INTENT_CLASSIFICATION_PROMPT = """Classify the user's message into one of these categories:

1. GENERAL - General questions, advice, or casual conversation
2. VENTURE_ANALYSIS - Deep startup analysis, business model review, due diligence
3. MARKET_RESEARCH - Market size, industry trends, TAM/SAM/SOM
4. VENTURE_ARCHITECT - Lean Canvas, JTBD, experiment design, hypothesis validation
5. NARRATIVE - Pitch story, founding story, mission, vision
6. DECK - Slides, presentation, pitch deck structure
7. VALUATION - Valuation, funding round, cap table, term sheets
8. FINANCIAL - Runway, burn rate, projections, unit economics
9. METRICS - KPIs, MRR, ARR, churn, dashboard
10. QA_PREP - Investor questions, objection handling, Q&A prep
11. DATAROOM - Data room, due diligence documents, document checklists
12. ICP - Customer profiling, personas, segmentation
13. RISK - Risks, failure modes, pre-mortem, threats
14. COMPETITOR - Competitor analysis, competitive landscape, positioning

Respond with ONLY the category name.

User message: {message}

Category:"""


# Agent registry
AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "general_agent": GeneralAgent,
    "venture_analyst": VentureAnalystAgent,
    "market_research": MarketResearchAgent,
    "venture_architect": VentureArchitectAgent,
    "storyteller": StorytellerAgent,
    "deck_architect": DeckArchitectAgent,
    "valuation_strategist": ValuationStrategistAgent,
    "lean_modeler": LeanModelerAgent,
    "kpi_dashboard": KPIDashboardAgent,
    "qa_simulator": QASimulatorAgent,
    "dataroom_concierge": DataroomConciergeAgent,
    "icp_profiler": ICPProfilerAgent,
    "pre_mortem_critic": PreMortemCriticAgent,
    "competitive_intel": CompetitiveIntelAgent,
}

# Intent to agent mapping
INTENT_TO_AGENT: dict[str, str] = {
    "GENERAL": "general_agent",
    "VENTURE_ANALYSIS": "venture_analyst",
    "MARKET_RESEARCH": "market_research",
    "VENTURE_ARCHITECT": "venture_architect",
    "NARRATIVE": "storyteller",
    "DECK": "deck_architect",
    "VALUATION": "valuation_strategist",
    "FINANCIAL": "lean_modeler",
    "METRICS": "kpi_dashboard",
    "QA_PREP": "qa_simulator",
    "DATAROOM": "dataroom_concierge",
    "ICP": "icp_profiler",
    "RISK": "pre_mortem_critic",
    "COMPETITOR": "competitive_intel",
}


class AgentRouter:
    """Routes messages to appropriate agents based on intent classification.

    Uses an LLM to classify user intent and dispatches to the most
    appropriate specialized agent.
    """

    def __init__(self, brain: StartupBrain, llm: LLMClient | None = None):
        """Initialize the agent router.

        Args:
            brain: StartupBrain instance for context retrieval.
            llm: Optional LLM client for intent classification.
        """
        self.brain = brain
        self.llm = llm or get_llm_client("claude")
        self._agent_cache: dict[str, BaseAgent] = {}

    async def classify_intent(self, message: str) -> str:
        """Classify the user's intent.

        Args:
            message: User's message.

        Returns:
            Agent name to handle the message.
        """
        prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)

        response = await self.llm.complete(
            messages=[{"role": "user", "content": prompt}],
            system="You are a message classifier. Respond with only the category name.",
            max_tokens=20,
            temperature=0.0,
        )

        # Parse the response
        intent = response.strip().upper()

        # Map to agent name, default to general
        agent_name = INTENT_TO_AGENT.get(intent, "general_agent")

        return agent_name

    def get_agent(self, name: str) -> BaseAgent:
        """Get an agent by name.

        Args:
            name: Agent name.

        Returns:
            Instantiated agent.

        Raises:
            ValueError: If agent name is not registered.
        """
        if name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {name}. Available: {list(AGENT_REGISTRY.keys())}")

        # Cache agents for reuse
        if name not in self._agent_cache:
            agent_class = AGENT_REGISTRY[name]
            self._agent_cache[name] = agent_class(self.brain, self.llm)

        return self._agent_cache[name]

    async def route(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        agent_override: str | None = None,
    ) -> AgentResponse:
        """Route a message to the appropriate agent and get a response.

        Args:
            message: User's message.
            context: Optional additional context (e.g., chat history).
            agent_override: Optional agent name to force (skip classification).

        Returns:
            AgentResponse from the selected agent.
        """
        # Determine which agent to use
        if agent_override and agent_override in AGENT_REGISTRY:
            agent_name = agent_override
        else:
            agent_name = await self.classify_intent(message)

        # Get the agent and execute
        agent = self.get_agent(agent_name)

        # Add routing info to context
        routing_context = context or {}
        routing_context["routed_to"] = agent_name

        response = await agent.execute(message, routing_context)

        # Add routing plan to response
        response.routing_plan = {
            "classified_intent": agent_name,
            "agent_used": agent.name,
            "agent_description": agent.description,
        }

        return response

    async def route_stream(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        agent_override: str | None = None,
    ):
        """Route a message and stream the response.

        Args:
            message: User's message.
            context: Optional additional context.
            agent_override: Optional agent name to force.

        Yields:
            Response chunks from the agent.
        """
        if agent_override and agent_override in AGENT_REGISTRY:
            agent_name = agent_override
        else:
            agent_name = await self.classify_intent(message)

        agent = self.get_agent(agent_name)

        routing_context = context or {}
        routing_context["routed_to"] = agent_name

        async for chunk in agent.stream(message, routing_context):
            yield chunk


def get_agent_router(brain: StartupBrain) -> AgentRouter:
    """Factory function to create an agent router.

    Args:
        brain: StartupBrain instance.

    Returns:
        Configured AgentRouter.
    """
    return AgentRouter(brain)
