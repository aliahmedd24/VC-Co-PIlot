# Phase 3: MoE Router + Core Agents

> **Timeline:** Weeks 7–10  
> **Priority:** Critical — the core intelligence layer  
> **Depends on:** Phase 2 (Startup Brain)  
> **Claude Code Tag:** `phase-3`

---

## Objective

Implement the Mixture-of-Experts (MoE) router that classifies user intent and dispatches requests to specialized AI agents, plus build all core agent implementations. The router must achieve < 200ms P95 latency and > 80% classification accuracy. Each agent consumes the Startup Brain context, calls Claude with a domain-specific system prompt, and returns structured responses with citations and proposed KG updates.

---

## Tech Stack

| Layer | Tool | Notes |
|-------|------|-------|
| Router | Python (keyword classifier) | No ML model — deterministic pattern matching for V1 |
| Intent Classification | Regex + weighted keyword scoring | Async, < 200ms target |
| Agent Framework | Abstract base class + Anthropic SDK | `anthropic.AsyncAnthropic` |
| LLM | Claude Sonnet (`claude-sonnet-4-20250514`) | Default model; configurable |
| Brain Integration | StartupBrain (Phase 2) | `retrieve()` and `get_snapshot()` |
| Chat Persistence | SQLAlchemy (Phase 1 models) | ChatSession + ChatMessage |
| API | FastAPI routes `/api/v1/chat/` | — |

---

## User Flow

### 1. Send a Message
1. User sends `POST /api/v1/chat/send` with `{ workspace_id, content, session_id?, override_agent? }`.
2. Backend loads venture context and validates workspace membership.
3. If `session_id` is null, a new `ChatSession` is created.
4. User message is saved as a `ChatMessage` (role=USER).

### 2. Router Decides
5. **Explicit @mention check:** If message contains `@deck`, `@market`, `@valuation`, etc., router maps to the corresponding agent directly (confidence=1.0).
6. **Artifact continuation:** If there's an active artifact in context, route to that artifact's `owner_agent` (confidence=0.95).
7. **Intent classification:** Keywords in the message are scored against pattern dictionaries. Highest-scoring intent is selected. If below 0.3 confidence, falls back to `venture-architect`.
8. **Stage overrides:** Certain intent→agent mappings change based on venture stage (e.g., `VALUATION` at `IDEATION` stage routes to `venture-architect` instead of `valuation-strategist`).
9. A `RoutingPlan` is produced containing: `selected_agent`, `model_profile`, `tools`, `artifact_needed`, `fallback_agent`, `confidence`, `reasoning`, `latency_ms`.

### 3. Agent Executes
10. The selected agent's `execute()` method is called.
11. Agent calls `brain.get_snapshot()` for venture state and `brain.retrieve(prompt)` for relevant context.
12. Agent builds a domain-specific system prompt combining venture context, KG entities, RAG chunks, and its own instructions.
13. Agent calls Claude via `_call_claude(system, prompt)`.
14. Agent extracts citations (`[Source: doc_id]` markers) and proposed KG updates (`<!-- PROPOSED_UPDATE: {...} -->` markers) from the response.
15. Returns `AgentResponse(content, citations, proposed_updates, artifact_id?)`.

### 4. Response Saved
16. Assistant message saved as `ChatMessage` (role=ASSISTANT) with `routing_plan`, `agent_id`, `citations`.
17. Full `SendMessageResponse` returned to user.

### 5. Agent Override
- User can force a specific agent via `override_agent` parameter.
- User can also use `@agent-name` syntax in the message body.

---

## Technical Constraints

- **Router P95 latency < 200ms** — no LLM calls in the router; keyword matching only.
- **First token latency < 2s** for simple queries, < 5s for complex queries.
- **All agents share a common base class** (`BaseAgent`) with template method pattern.
- **System prompts must include:** venture name, stage, one-liner, relevant KG entities, top-5 RAG chunks (capped at 300 chars each), and agent-specific instructions.
- **Max context window management:** Total system prompt + user prompt must not exceed 180K tokens. Truncate RAG chunks if necessary.
- **Proposed updates use HTML comments** so they don't render in the user-facing response: `<!-- PROPOSED_UPDATE: {"entity_type": "...", "data": {...}} -->`.
- **Citations use bracket notation:** `[Source: <document_id>]`.
- **Agent registry is a singleton** initialized at application startup.
- **Each agent must define:** `id`, `name`, `description`, `supported_stages`, `required_context` (list of KGEntityTypes), `can_create_artifacts` (list of artifact type strings).

---

## Data Schema

### Router Types

```python
class IntentCategory(str, Enum):
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    NARRATIVE = "narrative"
    DECK = "deck"
    VALUATION = "valuation"
    FINANCIAL = "financial"
    METRICS = "metrics"
    QA_PREP = "qa_prep"
    DATAROOM = "dataroom"
    ICP = "icp"
    RISK = "risk"
    GENERAL = "general"

class ModelProfile(str, Enum):
    REASONING_HEAVY = "reasoning_heavy"
    WRITING_POLISH = "writing_polish"
    TOOL_USING = "tool_using"
    FAST_RESPONSE = "fast_response"
    DEFAULT = "default"

class RoutingPlan(BaseModel):
    selected_agent: str
    model_profile: ModelProfile
    tools: list[str]
    artifact_needed: bool
    fallback_agent: str
    confidence: float        # 0.0 – 1.0
    reasoning: str
    latency_ms: float
```

### Agent Types

```python
class AgentConfig(BaseModel):
    id: str                              # e.g., "venture-architect"
    name: str                            # e.g., "Venture Architect"
    description: str
    supported_stages: list[VentureStage]
    required_context: list[KGEntityType]
    can_create_artifacts: list[str]

class AgentResponse(BaseModel):
    content: str
    artifact_id: Optional[str] = None
    citations: list[dict] = []
    proposed_updates: list[dict] = []
```

### Chat Schemas

```python
class SendMessageRequest(BaseModel):
    workspace_id: str
    content: str                          # min_length=1, max_length=10000
    session_id: Optional[str] = None
    override_agent: Optional[str] = None

class SendMessageResponse(BaseModel):
    session_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    routing_plan: RoutingPlan
    proposed_updates: list[dict]

class ChatSessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

class ChatMessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    agent_id: Optional[str]
    citations: Optional[list[dict]]
    created_at: datetime
```

### Intent-to-Agent Mapping

| Intent | Default Agent | Stage Override |
|--------|--------------|---------------|
| MARKET_RESEARCH | `market-oracle` | — |
| COMPETITOR_ANALYSIS | `competitive-intelligence` | — |
| NARRATIVE | `storyteller` | — |
| DECK | `deck-architect` | — |
| VALUATION | `valuation-strategist` | IDEATION → `venture-architect`, PRE_SEED → `lean-modeler` |
| FINANCIAL | `lean-modeler` | — |
| METRICS | `kpi-dashboard` | — |
| QA_PREP | `qa-simulator` | — |
| DATAROOM | `dataroom-concierge` | — |
| ICP | `icp-profiler` | — |
| RISK | `pre-mortem-critic` | — |
| GENERAL | `venture-architect` | — |

### Agent @-Mention Aliases

| Alias | Agent ID |
|-------|----------|
| `@venture` | `venture-architect` |
| `@market` | `market-oracle` |
| `@story` | `storyteller` |
| `@deck` | `deck-architect` |
| `@valuation` | `valuation-strategist` |
| `@qa` | `qa-simulator` |
| `@dataroom` | `dataroom-concierge` |
| `@kpi` | `kpi-dashboard` |
| `@icp` | `icp-profiler` |
| `@risk` | `pre-mortem-critic` |

---

## Agents to Implement

Each agent extends `BaseAgent` and implements `execute()` and `get_agent_specific_instructions()`.

### 1. Venture Architect (`venture-architect`)
- **Role:** Foundational venture design, Lean Canvas, JTBD, experiment planning.
- **Stages:** IDEATION, PRE_SEED, SEED.
- **Context:** VENTURE, MARKET, ICP, PRODUCT, COMPETITOR.
- **Artifacts:** `lean_canvas`, `research_brief`.

### 2. Market Oracle (`market-oracle`)
- **Role:** Market sizing (TAM/SAM/SOM), industry trends, growth analysis.
- **Stages:** All.
- **Context:** MARKET, COMPETITOR.
- **Artifacts:** `research_brief`.

### 3. Storyteller (`storyteller`)
- **Role:** Pitch narratives, founding stories, mission/vision crafting.
- **Stages:** All.
- **Context:** VENTURE, ICP, PRODUCT.
- **Artifacts:** `pitch_narrative`.

### 4. Deck Architect (`deck-architect`)
- **Role:** Pitch deck structure, slide content, visual suggestions.
- **Stages:** PRE_SEED, SEED, SERIES_A, SERIES_B.
- **Context:** VENTURE, MARKET, ICP, PRODUCT, METRIC, FUNDING_ASSUMPTION.
- **Artifacts:** `deck_outline`.

### 5. Valuation Strategist (`valuation-strategist`)
- **Role:** Valuation methodologies, comparable analysis, round structuring.
- **Stages:** SEED, SERIES_A, SERIES_B, GROWTH.
- **Context:** METRIC, FUNDING_ASSUMPTION, MARKET.
- **Artifacts:** `valuation_memo`.

### 6. Lean Modeler (`lean-modeler`)
- **Role:** Financial projections, runway calculations, unit economics.
- **Stages:** All.
- **Context:** METRIC, FUNDING_ASSUMPTION.
- **Artifacts:** `financial_model`.

### 7. KPI Dashboard (`kpi-dashboard`)
- **Role:** KPI definition, tracking suggestions, dashboard design.
- **Stages:** SEED, SERIES_A, SERIES_B, GROWTH.
- **Context:** METRIC.
- **Artifacts:** `kpi_dashboard`.

### 8. Q&A Simulator (`qa-simulator`)
- **Role:** Tough investor questions, objection handling, mock pitches.
- **Stages:** All.
- **Context:** VENTURE, MARKET, METRIC, RISK, FUNDING_ASSUMPTION.
- **Artifacts:** None (conversational).

### 9. Dataroom Concierge (`dataroom-concierge`)
- **Role:** Dataroom structure, document checklists, diligence readiness.
- **Stages:** SEED, SERIES_A, SERIES_B.
- **Context:** VENTURE, METRIC, FUNDING_ASSUMPTION.
- **Artifacts:** `dataroom_structure`.

### 10. ICP Profiler (`icp-profiler`)
- **Role:** Customer persona definition, market segmentation.
- **Stages:** All.
- **Context:** ICP, MARKET, PRODUCT.
- **Artifacts:** `research_brief`.

### 11. Pre-Mortem Critic (`pre-mortem-critic`)
- **Role:** Risk analysis, failure scenario simulation, threat assessment.
- **Stages:** All.
- **Context:** RISK, VENTURE, MARKET, COMPETITOR.
- **Artifacts:** `research_brief`.

---

## Key Files to Create / Modify

```
backend/app/
├── core/
│   ├── router/
│   │   ├── __init__.py
│   │   ├── moe_router.py              # MoERouter class
│   │   ├── intent_classifier.py       # Keyword-based IntentClassifier
│   │   └── types.py                   # IntentCategory, ModelProfile, RoutingPlan
│   │
│   └── agents/
│       ├── __init__.py
│       ├── base.py                     # BaseAgent, AgentConfig, AgentResponse
│       ├── registry.py                 # AgentRegistry singleton
│       ├── venture_architect.py
│       ├── market_oracle.py
│       ├── storyteller.py
│       ├── deck_architect.py
│       ├── valuation_strategist.py
│       ├── lean_modeler.py
│       ├── kpi_dashboard.py
│       ├── qa_simulator.py
│       ├── dataroom_concierge.py
│       ├── icp_profiler.py
│       └── pre_mortem_critic.py
│
├── api/routes/
│   └── chat.py                         # /send, /sessions, /sessions/{id}
│
├── schemas/
│   └── chat.py                         # SendMessageRequest/Response, etc.
│
└── models/
    └── chat.py                         # ChatSession, ChatMessage (from Phase 1)
```

---

## Definition of Done

### Automated Tests

1. **Intent Classifier Tests**
   - `test_market_research_keywords` → "What's the TAM for edtech?" → `MARKET_RESEARCH`.
   - `test_competitor_keywords` → "Compare us vs Notion" → `COMPETITOR_ANALYSIS`.
   - `test_valuation_keywords` → "What are we worth?" → `VALUATION`.
   - `test_deck_keywords` → "Help me build my pitch deck" → `DECK`.
   - `test_financial_keywords` → "Calculate our runway" → `FINANCIAL`.
   - `test_general_fallback` → "Hello, how are you?" → `GENERAL` with confidence < 0.3.
   - `test_multi_intent_picks_strongest` → "Compare our valuation against competitors" → highest-scored intent wins.
   - `test_classification_accuracy_benchmark` → Run 50 labeled test cases, assert ≥ 80% correct.

2. **MoE Router Tests**
   - `test_explicit_mention_routing` → "@deck make slides" routes to `deck-architect` with confidence 1.0.
   - `test_artifact_continuation` → Active artifact with owner `storyteller` routes to `storyteller`.
   - `test_stage_override_ideation` → VALUATION intent at IDEATION stage routes to `venture-architect`.
   - `test_stage_override_pre_seed` → VALUATION intent at PRE_SEED routes to `lean-modeler`.
   - `test_router_latency` → 100 sequential calls complete in < 20s total (< 200ms average).
   - `test_override_agent` → `override_agent="qa-simulator"` bypasses all routing logic.
   - `test_unknown_alias_ignored` → "@nonexistent do something" falls through to classifier.

3. **BaseAgent Tests**
   - `test_build_system_prompt` → System prompt contains venture name, stage, entities, chunks.
   - `test_extract_citations` → Parses `[Source: doc-123]` from response text.
   - `test_extract_proposed_updates` → Parses `<!-- PROPOSED_UPDATE: {...} -->` correctly.
   - `test_extract_proposed_updates_malformed` → Invalid JSON in update marker is skipped gracefully.

4. **Agent Execution Tests** (with mocked Claude API)
   - `test_venture_architect_execute` → Returns `AgentResponse` with non-empty content.
   - `test_market_oracle_execute` → Returns response with market-specific context.
   - `test_qa_simulator_execute` → Returns response with investor question format.
   - For each of the 11 agents: at least one basic execution test.

5. **Agent Registry Tests**
   - `test_all_agents_registered` → Registry contains all 11 agents.
   - `test_get_agent_by_id` → Each agent retrievable by its ID.
   - `test_get_nonexistent_agent` → Returns None.

6. **Chat API Tests**
   - `test_send_message_creates_session` → POST with no `session_id` creates new session.
   - `test_send_message_existing_session` → POST with valid `session_id` appends to session.
   - `test_send_message_returns_routing_plan` → Response includes `routing_plan` with all fields.
   - `test_list_sessions` → Returns sessions ordered by `updated_at` desc.
   - `test_get_session_with_messages` → Returns session with message history.
   - `test_chat_requires_venture` → Workspace without venture returns 400.

### Manual / CI Checks

- Send a message through the API and verify the full flow: routing → agent → Claude call → response with citations.
- Verify that routing metadata is correctly stored in `ChatMessage.routing_plan`.
- `ruff check .` and `mypy .` pass.
- All 11 agents produce coherent responses when tested against a sample venture profile.
