# Phase 6: Advanced Features & Production Polish

> **Timeline:** Weeks 17–20  
> **Priority:** Medium-High — differentiating features and production readiness  
> **Depends on:** Phases 1–5 (complete platform)  
> **Claude Code Tag:** `phase-6`

---

## Objective

Add the advanced differentiating features listed in the product spec: Startup Valuation Tool, Investor Readiness Score, Scenario Modeling, Benchmarking Engine, AI Pitch Generator, Success Story Analyzer, Founder Persona Coach, Cross-Border Expansion Advisor, and Real-time Fundraising Playbook. Also implement streaming responses (SSE), observability (metrics, structured logging), rate limiting, and production hardening. This phase transforms the MVP into a market-ready platform.

---

## Tech Stack

| Layer | Tool | Notes |
|-------|------|-------|
| Streaming | Server-Sent Events (SSE) | `fastapi.responses.StreamingResponse` |
| Metrics | `prometheus-fastapi-instrumentator` | Prometheus-compatible `/metrics` |
| Tracing | OpenTelemetry (optional) | Jaeger/Zipkin backend |
| Rate Limiting | `slowapi` | Per-user rate limits on chat endpoint |
| Auth Upgrade | httpOnly cookies + CSRF | Replace localStorage JWT |
| Benchmarking Data | Cached JSON datasets | Startup benchmarks by sector/stage |
| Scoring Engine | Python (weighted rubric) | Investor Readiness Score calculator |

---

## User Flow

### Feature 6A: Startup Valuation Tool
1. User asks a valuation question or navigates to the Valuation Tool in the UI.
2. User inputs: revenue/ARR, growth rate, industry, stage, comparable exits.
3. Backend runs 3 valuation methods: Revenue Multiple, DCF (simplified), and Comparable Analysis.
4. Returns a valuation range (low, mid, high) with methodology breakdown.
5. Creates a `valuation_memo` artifact with the analysis.

### Feature 6B: Investor Readiness Score
1. User clicks "Check Readiness" or asks an agent "Am I ready to raise?".
2. Backend evaluates 5 dimensions against the Knowledge Graph: **Business** (problem, solution, ICP clarity), **Financial** (metrics, runway, unit economics), **Market** (TAM/SAM validation, competitive positioning), **Team** (completeness, relevant experience), **Materials** (deck, dataroom, narrative completeness).
3. Each dimension scored 0–100. Weighted average produces overall score.
4. Returns score card with dimension breakdowns, specific gaps, and recommended next steps.
5. Creates a `research_brief` artifact with the readiness report.

### Feature 6C: Scenario Modeling
1. User requests scenario modeling for a fundraise.
2. Inputs: raise amount, pre-money valuation, employee option pool size.
3. Backend simulates: equity dilution per round, valuation progression over 3 rounds, exit scenarios (1x–20x multiple), time-to-exit estimates.
4. Returns structured scenarios with comparison tables.
5. Creates a `financial_model` artifact with scenarios.

### Feature 6D: Benchmarking Engine
1. User asks "How do we compare to similar funded startups?".
2. Backend matches the venture's industry, stage, and metrics against a curated benchmark dataset.
3. Returns percentile rankings for key metrics (MRR growth, burn rate, CAC, LTV, etc.) compared to peer cohort.
4. Highlights strengths (top quartile) and weaknesses (bottom quartile).

### Feature 6E: AI Pitch Generator
1. User clicks "Generate Pitch" or asks an agent.
2. Backend pulls all available KG data (venture, market, ICP, metrics, team, competitors) and RAG context.
3. Claude generates a polished 2-minute pitch script tailored to the venture's stage and audience.
4. Creates a `pitch_narrative` artifact.

### Feature 6F: Success Story Analyzer
1. User asks "Which successful startups are most like us?".
2. Backend compares venture attributes against a dataset of 100+ unicorn/successful exit profiles.
3. Returns top 5 matches with similarity scores and key parallels/differences.
4. Insights on which traits to amplify and which gaps to close.

### Feature 6G: Founder Persona Coach
1. User submits founder bio or LinkedIn summary.
2. Claude analyzes the bio for investor appeal: narrative strength, credibility signals, unique angles.
3. Returns feedback on the personal brand with specific suggestions for improvement.
4. Creates a `research_brief` artifact with the coaching notes.

### Feature 6H: Cross-Border Expansion Advisor
1. User asks about expanding to a new market (e.g., "Should we enter the EU market?").
2. Agent simulates: regulatory challenges, market size opportunity, localization requirements, competitor landscape in target market, estimated cost/timeline.
3. Returns structured analysis comparing expansion scenarios.

### Feature 6I: Real-Time Fundraising Playbook
1. User enters current fundraising stage and progress.
2. Backend generates a dynamic, step-by-step playbook adapted to the venture's current state.
3. Playbook includes: timeline milestones, investor targeting strategy, materials checklist (linked to existing artifacts), negotiation talking points, and post-term-sheet guidance.
4. Playbook updates dynamically as new information enters the KG.

### Feature 6J: Streaming Responses
1. Chat endpoint upgraded to support SSE streaming.
2. Frontend shows tokens as they arrive, character by character.
3. Routing metadata sent as first SSE event, then content tokens stream.

---

## Technical Constraints

- **Streaming uses SSE** via `StreamingResponse` — NOT WebSockets. Content-Type: `text/event-stream`.
- **SSE event format:** `event: routing\ndata: {routing_plan_json}\n\n` followed by `event: token\ndata: {text}\n\n` followed by `event: done\ndata: {final_metadata}\n\n`.
- **Rate limiting:** 20 messages per minute per user on `/chat/send`. 5 exports per hour per user.
- **Benchmark dataset** stored as a JSON file in the repository (seeded at deploy time). Not a live external API.
- **Success story dataset** similarly a curated static JSON of ~100 startup profiles.
- **Valuation calculations run in Python** — no external financial APIs. Revenue multiples sourced from the benchmark dataset.
- **Investor Readiness Score rubric** is configurable via a YAML file (`scoring_rubric.yaml`).
- **Streaming must be backward-compatible:** If client sends `Accept: application/json`, return the full response as before (non-streaming). If `Accept: text/event-stream`, use streaming.
- **Auth upgrade to httpOnly cookies** must maintain backward compatibility with Bearer tokens during migration.
- **All new features must have OpenAPI documentation** via FastAPI's auto-generated docs.
- **Prometheus metrics** must include: request count, latency histograms (p50, p95, p99), active WebSocket connections, agent invocation counts, router classification distribution.

---

## Data Schema

### Investor Readiness Score

```python
class ReadinessDimension(BaseModel):
    name: str                              # "business", "financial", "market", "team", "materials"
    score: float                           # 0–100
    weight: float                          # 0.0–1.0 (all weights sum to 1.0)
    gaps: list[str]                        # Specific missing items
    recommendations: list[str]             # Actionable next steps

class InvestorReadinessScore(BaseModel):
    overall_score: float                   # Weighted average
    grade: str                             # "A" (90+), "B" (75+), "C" (60+), "D" (40+), "F" (<40)
    dimensions: list[ReadinessDimension]
    summary: str                           # AI-generated narrative summary
    top_priority_actions: list[str]        # Top 3 things to do next
```

### Scenario Model

```python
class FundingScenario(BaseModel):
    raise_amount: float
    pre_money_valuation: float
    post_money_valuation: float
    dilution_pct: float
    option_pool_pct: float
    founder_ownership_after: float

class ScenarioModelResult(BaseModel):
    scenarios: list[FundingScenario]       # Multiple rounds
    exit_scenarios: list[ExitScenario]     # Different multiples
    cap_table_progression: list[dict]      # Ownership over rounds

class ExitScenario(BaseModel):
    exit_multiple: float
    exit_valuation: float
    founder_proceeds: float
    investor_proceeds: float
    time_to_exit_years: float
```

### Benchmark Result

```python
class BenchmarkMetric(BaseModel):
    metric_name: str                       # "mrr_growth", "burn_rate", etc.
    venture_value: Optional[float]
    peer_median: float
    peer_p25: float
    peer_p75: float
    percentile: float                      # Venture's percentile in cohort
    status: str                            # "strong", "average", "weak"

class BenchmarkResult(BaseModel):
    peer_cohort: str                       # "Series A SaaS, 2024"
    cohort_size: int
    metrics: list[BenchmarkMetric]
    strengths: list[str]
    weaknesses: list[str]
```

### SSE Event Schema

```typescript
// Frontend types for SSE
interface SSERoutingEvent {
  event: "routing";
  data: RoutingPlan;
}

interface SSETokenEvent {
  event: "token";
  data: string;                            // Text fragment
}

interface SSEDoneEvent {
  event: "done";
  data: {
    message_id: string;
    citations: Citation[];
    proposed_updates: Record<string, any>[];
    artifact_id: string | null;
  };
}
```

---

## Key Files to Create / Modify

```
backend/app/
├── core/
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── readiness_scorer.py         # InvestorReadinessScorer
│   │   └── scoring_rubric.yaml         # Configurable scoring weights/thresholds
│   │
│   ├── valuation/
│   │   ├── __init__.py
│   │   ├── valuation_engine.py         # 3-method valuation calculator
│   │   └── multiples_data.json         # Industry revenue multiples
│   │
│   ├── scenario/
│   │   ├── __init__.py
│   │   └── scenario_modeler.py         # Dilution + exit calculator
│   │
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── benchmark_engine.py         # Percentile ranking engine
│   │   └── benchmark_data.json         # Curated startup benchmarks
│   │
│   └── success_stories/
│       ├── __init__.py
│       ├── matcher.py                   # Attribute-based similarity matching
│       └── stories_data.json            # 100+ unicorn profiles
│
├── api/routes/
│   ├── chat.py                         # Add SSE streaming support
│   ├── scoring.py                      # /readiness-score endpoint
│   ├── valuation.py                    # /valuation endpoint
│   ├── scenarios.py                    # /scenarios endpoint
│   └── benchmarks.py                   # /benchmarks, /success-stories endpoints
│
├── middleware/
│   ├── rate_limiter.py                 # slowapi configuration
│   └── metrics.py                      # Prometheus instrumentator
│
└── schemas/
    ├── scoring.py
    ├── valuation.py
    ├── scenario.py
    └── benchmark.py

frontend/
├── components/
│   ├── chat/
│   │   └── StreamingMessage.tsx         # Token-by-token rendering
│   ├── tools/
│   │   ├── ValuationTool.tsx            # Valuation input form + results
│   │   ├── ReadinessScoreCard.tsx       # Radar chart + dimension cards
│   │   ├── ScenarioModeler.tsx          # Interactive scenario builder
│   │   ├── BenchmarkComparison.tsx      # Percentile bar charts
│   │   ├── SuccessStoryMatcher.tsx      # Similarity cards
│   │   ├── PitchGenerator.tsx           # One-click pitch generation
│   │   ├── FounderCoach.tsx             # Bio input + feedback
│   │   ├── ExpansionAdvisor.tsx         # Market expansion analysis
│   │   └── FundraisingPlaybook.tsx      # Dynamic checklist/timeline
│   └── charts/
│       ├── RadarChart.tsx               # For readiness score
│       ├── WaterfallChart.tsx           # For dilution/cap table
│       └── PercentileBar.tsx            # For benchmarks
│
└── lib/
    ├── api/
    │   ├── scoring.ts
    │   ├── valuation.ts
    │   ├── scenarios.ts
    │   └── benchmarks.ts
    └── hooks/
        ├── useStreaming.ts              # SSE hook for streaming chat
        └── useTools.ts                  # Hooks for advanced tool APIs
```

---

## Definition of Done

### Automated Tests

1. **Valuation Engine Tests**
   - `test_revenue_multiple_method` → Known inputs produce expected valuation range.
   - `test_dcf_method` → Discounted cash flow calculation matches manual calculation.
   - `test_comparable_analysis` → Peer median valuation correctly computed.
   - `test_missing_inputs_handled` → Gracefully returns partial results with warnings.

2. **Investor Readiness Tests**
   - `test_full_readiness_score` → Venture with all KG entities filled scores > 80.
   - `test_empty_venture_low_score` → Venture with no KG data scores < 30.
   - `test_dimension_weights_sum_to_1` → Rubric weights validated on load.
   - `test_gaps_identified` → Missing KG entity types listed in gaps.
   - `test_grade_assignment` → Score 92 → "A", 50 → "D", etc.

3. **Scenario Modeling Tests**
   - `test_dilution_calculation` → $2M raise at $8M pre → 20% dilution.
   - `test_multi_round_cap_table` → 3-round simulation produces correct progressive dilution.
   - `test_exit_scenarios` → 10x exit on $10M post-money → correct founder proceeds.

4. **Benchmarking Tests**
   - `test_percentile_ranking` → Known value ranked correctly against dataset.
   - `test_peer_cohort_filtering` → Only matching industry + stage included.
   - `test_strength_weakness_classification` → Top quartile = "strong", bottom = "weak".

5. **Streaming Tests**
   - `test_sse_routing_event` → First event is `routing` with valid RoutingPlan.
   - `test_sse_token_events` → Multiple `token` events received, concatenation equals full response.
   - `test_sse_done_event` → Final event contains message_id and citations.
   - `test_non_streaming_fallback` → `Accept: application/json` returns full JSON response.

6. **Rate Limiting Tests**
   - `test_rate_limit_exceeded` → 21st message within 1 minute returns 429.
   - `test_rate_limit_per_user` → Different users have independent limits.
   - `test_export_rate_limit` → 6th export within 1 hour returns 429.

7. **Metrics Tests**
   - `test_prometheus_endpoint` → `/metrics` returns Prometheus text format.
   - `test_request_count_incremented` → Counter increases after API call.

8. **Success Story Matcher Tests**
   - `test_top_5_matches_returned` → Returns exactly 5 matches ordered by similarity.
   - `test_similarity_based_on_attributes` → Same industry + stage → higher similarity.

### Manual / CI Checks

- SSE streaming works in browser: tokens appear progressively, not all at once.
- Valuation Tool produces reasonable ranges for sample inputs.
- Investor Readiness Score radar chart renders correctly with all 5 dimensions.
- Scenario Modeler interactive sliders update calculations in real time.
- Benchmark comparison shows bar charts with peer cohort data.
- Rate limiter returns 429 with appropriate `Retry-After` header.
- `/metrics` endpoint scrape-able by Prometheus.
- `ruff check .` and `mypy .` pass.
- Full platform E2E: register → onboard → upload doc → chat → use valuation tool → generate pitch → check readiness → export artifacts.
- Load test: 10 concurrent users chatting simultaneously without errors.
