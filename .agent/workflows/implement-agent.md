---
description: Project-specific agent creation—spec → file structure → system prompt → context retrieval → execute/stream methods → router registration → comprehensive tests
---

# Workflow: Implement AI Agent

> Project-specific workflow for implementing new AI agents in the AI VC Co-Pilot system.

---

## Trigger

- Adding a new specialized agent
- Modifying existing agent behavior

## Prerequisites

- [ ] BaseAgent exists in `backend/app/core/agents/base.py`
- [ ] MoE Router exists in `backend/app/core/router/moe_router.py`
- [ ] StartupBrain is functional

---

## Steps

### Step 1: Define Agent Specification

Document in log.md:

```markdown
### Agent: [AgentName]
**Responsibility:** [Single sentence]
**Expertise Areas:** [list]
**Input Triggers:** Keywords: [list], Intents: [list], @mention: @[name]
**Output Types:** [list]
**Artifacts Created:** [if any]
**Brain Reads:** [entities/facts needed]
**Brain Writes:** [what it proposes to update]
**Example Queries:** [2-3 examples with expected behavior]
```

CHECKPOINT: Spec is clear and complete

### Step 2: Create Agent File

Create `backend/app/core/agents/[agent_name].py`:

```python
from typing import AsyncGenerator
from app.core.agents.base import BaseAgent, AgentConfig, AgentResponse
from app.core.brain.startup_brain import StartupBrain
from app.services.anthropic_client import AnthropicClient

class [AgentName]Agent(BaseAgent):
    name = "[agent_name]"
    description = "[When to use this agent]"
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_CONTEXT_CHUNKS = 10
    
    SYSTEM_PROMPT = '''You are the [AgentName], specialized in [domain].
    
## Expertise
[List capabilities]

## Response Format
[Formatting guidelines]

## Context
{venture_context}
'''
    
    async def execute(self, message: str, context: dict) -> AgentResponse:
        raise NotImplementedError("TODO: Implement")
    
    async def stream(self, message: str, context: dict) -> AsyncGenerator[str, None]:
        raise NotImplementedError("TODO: Implement")
```

CHECKPOINT: File created, inherits BaseAgent

### Step 3: Implement Context Retrieval

```python
async def _get_relevant_context(self, message: str, workspace_id: str) -> dict:
    search_config = {
        "query": message,
        "entity_types": ["market_data", "competitor", "metric"],  # Agent-specific
        "max_chunks": self.MAX_CONTEXT_CHUNKS,
    }
    rag_results = await self.brain.retrieve(workspace_id=workspace_id, **search_config)
    kg_entities = await self.brain.kg.get_entities(
        workspace_id=workspace_id, types=search_config["entity_types"]
    )
    return {
        "chunks": rag_results.chunks,
        "entities": kg_entities,
        "venture_snapshot": await self.brain.get_snapshot(workspace_id)
    }
```

CHECKPOINT: Entity types appropriate for agent domain

### Step 4: Implement Execute Method

```python
async def execute(self, message: str, context: dict) -> AgentResponse:
    workspace_id = context.get("workspace_id")
    
    # 1. Get context from brain
    brain_context = await self._get_relevant_context(message, workspace_id)
    
    # 2. Build prompt with context
    system_prompt = self._build_system_prompt(brain_context)
    messages = self._build_messages(message, context)
    
    # 3. Call LLM
    response = await self.llm_client.create_message(
        model=self.DEFAULT_MODEL, system=system_prompt,
        messages=messages, max_tokens=4096
    )
    
    # 4. Extract citations and check for updates
    citations = self._extract_citations(response.content, brain_context["chunks"])
    proposed_updates = await self._check_for_updates(message, response.content, workspace_id)
    
    return AgentResponse(
        content=response.content, agent_name=self.name,
        citations=citations, proposed_updates=proposed_updates
    )
```

### Step 5: Implement Stream Method

```python
async def stream(self, message: str, context: dict) -> AsyncGenerator[str, None]:
    workspace_id = context.get("workspace_id")
    brain_context = await self._get_relevant_context(message, workspace_id)
    system_prompt = self._build_system_prompt(brain_context)
    messages = self._build_messages(message, context)
    
    async for chunk in self.llm_client.stream_message(
        model=self.DEFAULT_MODEL, system=system_prompt,
        messages=messages, max_tokens=4096
    ):
        yield chunk.delta.text if chunk.delta else ""
```

CHECKPOINT: Both execute and stream implemented

### Step 6: Register with Router

Update `backend/app/core/router/moe_router.py`:

```python
# Add to INTENT_TO_AGENT
INTENT_TO_AGENT = {
    "new_intent": "[agent_name]",
}

# Add to AGENT_REGISTRY  
AGENT_REGISTRY = {
    "[agent_name]": [AgentName]Agent,
}

# Add stage overrides if needed
STAGE_OVERRIDES = {
    ("new_intent", "seed"): "[agent_name]",
}
```

CHECKPOINT: Agent registered, intent mapping added

### Step 7: Write Tests

Create `tests/unit/test_[agent_name]_agent.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.agents.[agent_name] import [AgentName]Agent

@pytest.fixture
def agent():
    brain = AsyncMock()
    brain.retrieve.return_value = MagicMock(chunks=[])
    brain.get_snapshot.return_value = {"name": "Test Venture"}
    llm = AsyncMock()
    llm.create_message.return_value = MagicMock(
        content="Response", model="claude-sonnet-4-20250514",
        usage=MagicMock(total_tokens=100)
    )
    return [AgentName]Agent(brain=brain, llm_client=llm)

class Test[AgentName]Agent:
    @pytest.mark.asyncio
    async def test_execute_returns_response(self, agent):
        result = await agent.execute("test", {"workspace_id": "ws"})
        assert result.agent_name == "[agent_name]"
        assert result.content is not None
    
    @pytest.mark.asyncio
    async def test_retrieves_context(self, agent):
        await agent.execute("query", {"workspace_id": "ws"})
        agent.brain.retrieve.assert_called_once()
```

Run: `pytest tests/unit/test_[agent_name]_agent.py -v`

CHECKPOINT: Tests passing

### Step 8: Integration Test

Create `tests/integration/test_[agent_name]_routing.py`:

```python
@pytest.mark.asyncio
async def test_routes_on_keyword(router):
    result = await router.route("[trigger query]", {"workspace_id": "test"})
    assert result.selected_agent == "[agent_name]"

@pytest.mark.asyncio  
async def test_routes_on_mention(router):
    result = await router.route("@[agent_name] help", {"workspace_id": "test"})
    assert result.selected_agent == "[agent_name]"
```

CHECKPOINT: Routing works correctly

---

## Output Checklist

- [ ] Agent class implemented with execute() and stream()
- [ ] System prompt defines expertise and format
- [ ] Brain integration working
- [ ] Router registration complete
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] log.md updated

---

## Reference: Existing Agents

| Agent | File | Pattern |
|-------|------|---------|
| VentureArchitect | `venture_architect.py` | Business model |
| MarketOracle | `market_oracle.py` | Market research |
| FinancialArchitect | `financial_architect.py` | Projections |
| PitchPerfectionist | `pitch_perfectionist.py` | Pitch evaluation |
| GrowthStrategist | `growth_strategist.py` | GTM tactics |
| TechAdvisor | `tech_advisor.py` | Architecture |
