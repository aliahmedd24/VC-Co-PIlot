<p align="center">
  <h1 align="center">🚀 AI VC Co-Pilot</h1>
  <p align="center">
    <strong>An agentic venture consultancy platform powered by a Mixture-of-Experts AI architecture.</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#usage">Usage</a> •
    <a href="#testing">Testing</a> •
    <a href="#project-structure">Project Structure</a>
  </p>
</p>

---

## Overview

AI VC Co-Pilot is a full-stack platform that provides founders and venture consultants with an intelligent, multi-agent AI system. It combines a **Mixture-of-Experts (MoE) router** with **11 specialized AI agents**, a **knowledge graph**, **RAG-powered retrieval**, a **versioned artifact system**, and **4 MCP (Model Context Protocol) servers** to deliver expert-level guidance across every stage of a startup's journey — from ideation to fundraising.

---

## Features

### 🤖 Multi-Agent System
- **11 specialized agents**, each an expert in a different domain:

  | Agent | Role |
  |---|---|
  | **Venture Architect** | Business model design & strategy |
  | **Market Oracle** | Market research & competitive analysis |
  | **Storyteller** | Narrative crafting & pitch storytelling |
  | **Deck Architect** | Pitch deck structure & design |
  | **Valuation Strategist** | Valuation methods & financial modeling |
  | **Lean Modeler** | Lean canvas & business planning |
  | **KPI Dashboard** | Metrics tracking & KPI definition |
  | **QA Simulator** | Investor Q&A preparation |
  | **Dataroom Concierge** | Data room setup & due diligence |
  | **ICP Profiler** | Ideal customer profile analysis |
  | **Pre-Mortem Critic** | Risk analysis & failure prediction |

- **Intelligent routing** via keyword-based intent classification across 12 intent categories
- **Cross-agent delegation** with recursion guards

### 📚 Agent Skill System
Each agent is equipped with **domain-specific skill files** (`SKILL.md`) that are injected into its system prompt at runtime, giving it deep expertise in its area:

- **11 agent-specific SKILL.md files** — comprehensive domain knowledge including frameworks, methodologies, templates, decision trees, and response patterns (e.g., Venture Architect has Lean Canvas methodology, JTBD framework, experiment design, and pivot decision trees; ICP Profiler has segmentation methods, persona templates, and validation signals)
- **5 shared knowledge bases** loaded selectively per agent via `SkillLoader`:

  | Shared Skill | Content | Used By |
  |---|---|---|
  | `vc_fundamentals.md` | VC ecosystem, term sheets, cap tables | 7 agents |
  | `fundraising_stages.md` | Pre-seed → Series C stage definitions | 7 agents |
  | `market_sizing.md` | TAM/SAM/SOM, top-down/bottom-up analysis | 3 agents |
  | `saas_metrics.md` | MRR, churn, LTV, CAC, unit economics | 4 agents |
  | `red_flags.md` | Investor red flags & common pitfalls | 3 agents |

- **Reference directories** — additional material (guides, templates, examples) for agents like venture-architect, valuation-strategist, deck-architect, market-oracle, and pre-mortem-critic
- **`SkillLoader`** singleton — loads agent skills, shared knowledge, and reference files at runtime with path-traversal protection

### 🧠 Startup Brain
- **Knowledge Graph** — Entity extraction (via Claude), conflict detection, CRUD operations, confidence scoring, and advanced traversal
- **RAG Retriever** — Freshness-weighted pgvector semantic search
- **Event Store** — Append-only event log for tracking venture history
- **Unified Search** — Combined RAG + KG retrieval via `asyncio.gather`

### 📄 Artifact System
- **10 artifact types**: Lean Canvas, Pitch Narrative, Deck Outline, Valuation Memo, Financial Model, KPI Dashboard, Dataroom Structure, Research Brief, Board Memo, Custom
- **Version control** with optimistic locking, structural diffing (deepdiff), and version pruning
- **Export** to Markdown and PDF (Jinja2 templates + WeasyPrint)
- **Artifact chat** — scoped conversations for iterating on specific artifacts

### 🔧 Tool Calling System (14 Tools)
- **Engine Tools**: Valuation, investor readiness scoring, scenario modeling, benchmarks, success story matching
- **Brain/Knowledge Tools**: Entity queries, brain search, data gap detection, relation traversal
- **Research Tools**: Web search (Tavily API), URL fetching with HTML extraction
- **Artifact Tools**: Create and update artifacts with content schema validation
- **Delegation Tool**: Cross-agent delegation with depth limiting

### 🔌 MCP Servers (Model Context Protocol)
The platform exposes its capabilities as **4 MCP servers** built with [FastMCP](https://github.com/jlowin/fastmcp):

| MCP Server | Mount Path | Tools & Resources |
|---|---|---|
| **Analytics** | `/mcp/analytics` | `run_valuation`, `score_readiness`, `model_scenario`, `rank_benchmarks`, `match_success_stories` |
| **Brain** | `/mcp/brain` | `query_entities`, `search_brain`, `detect_data_gaps`, `traverse_relations` + 2 resource templates (venture snapshot, entities by type) |
| **Research** | `/mcp/research` | `web_search` (Tavily), `fetch_url` with HTML extraction |
| **Memory** | `/mcp/memory` | `store_insight`, `recall_context`, `update_preference` + 2 resource templates (venture insights, user preferences) |

- **MCP Client Facade** (`MCPClient`) — Lightweight HTTP+SSE client for dispatching tool calls to remote MCP servers, enabling the `ToolExecutor` to transparently route to external services
- Each server is mounted as an ASGI sub-application within FastAPI
- Full JSON-RPC 2.0 protocol support (`tools/call`, `tools/list`)

### 📊 Analytics & Engines
- **Valuation Engine** — 3 valuation methods with industry multiples
- **Investor Readiness Scorer** — YAML rubric, 5 scoring dimensions
- **Scenario Modeler** — Dilution, cap table, and exit modeling
- **Benchmark Engine** — Percentile ranking against industry benchmarks
- **Success Story Matcher** — Pattern matching against 40 startup profiles

### 💬 Chat Interface
- Real-time **SSE streaming** with tool activity indicators
- **@mention** agent selection with keyboard navigation
- Routing transparency (agent, model, confidence, latency, tools used)

### 🎨 Frontend Dashboard
- **Chat** — Full-featured chat with session management and streaming
- **Artifacts** — Grid/list view with filtering, type-specific renderers, version diffing
- **Profile** — Venture overview, knowledge graph entities, metrics
- **Documents** — Drag-and-drop upload with processing pipeline
- **Tools** — Interactive tool pages with charts (Radar, Waterfall, Percentile)
- **Settings** — Workspace management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                        │
│  (React 18 · Tailwind CSS · shadcn/ui · Zustand · RQ)      │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  MoE Router  │  │  11 Agents   │  │  Tool Executor    │  │
│  │  + Intent    │──│  (Claude)    │──│  (14 tools)       │  │
│  │  Classifier  │  │              │  │                   │  │
│  └─────────────┘  └──────┬───────┘  └───────┬───────────┘  │
│                          │                   │              │
│  ┌───────────────────────▼───────────────────┼──────────┐  │
│  │              Startup Brain                │           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────┴──────┐   │  │
│  │  │ Knowledge  │  │    RAG     │  │   Event      │   │  │
│  │  │   Graph    │  │ Retriever  │  │   Store      │   │  │
│  │  └────────────┘  └────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Artifact    │  │   Engines    │  │  Celery Workers   │  │
│  │  Manager     │  │ (Val/Score/  │  │  (Doc processing, │  │
│  │  + Exporters │  │  Scenario)   │  │   PDF export)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          MCP Servers (Model Context Protocol)         │  │
│  │  ┌───────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ Analytics │ │ Brain  │ │ Research │ │  Memory  │ │  │
│  │  │ (5 tools) │ │(4+2res)│ │ (2 tools)│ │(3+2res)  │ │  │
│  │  └───────────┘ └────────┘ └──────────┘ └──────────┘ │  │
│  │          ▲  MCP Client Facade (JSON-RPC)            │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
         │               │               │
    PostgreSQL        Redis          MinIO (S3)
    + pgvector      (Cache/Queue)   (Documents)
               

```

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.12+** | Runtime |
| **FastAPI** | Web framework & API |
| **SQLAlchemy 2.0** (async) | ORM with async sessions |
| **PostgreSQL + pgvector** | Database with vector similarity search |
| **Alembic** | Database migrations |
| **Anthropic Claude** | LLM for agents & entity extraction |
| **OpenAI** | Text embeddings (text-embedding-3-small) |
| **Celery + Redis** | Background task processing |
| **MinIO (S3)** | Document storage |
| **WeasyPrint + Jinja2** | PDF/Markdown export |
| **Pydantic v2** | Data validation & settings |
| **FastMCP** | MCP server framework (Model Context Protocol) |
| **Poetry** | Dependency management |

### Frontend
| Technology | Purpose |
|---|---|
| **Next.js 14** | React framework |
| **TypeScript** (strict) | Type-safe development |
| **Tailwind CSS** | Styling |
| **shadcn/ui + Radix** | UI component library |
| **Zustand** | State management |
| **TanStack React Query** | Server state & caching |
| **Recharts** | Data visualization |
| **Zod + React Hook Form** | Form validation |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker Compose** | Local development services |
| **Prometheus** | Metrics collection |
| **slowapi** | Rate limiting |

---

## Getting Started

### Prerequisites

- **Python** ≥ 3.12
- **Node.js** ≥ 18 & **pnpm**
- **Poetry** (Python dependency manager)
- **Docker & Docker Compose**

### 1. Clone the Repository

```bash
git clone https://github.com/aliahmedd24/VC-Co-PIlot.git
cd VC-Co-PIlot
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | Random secret for JWT tokens |
| `S3_ENDPOINT_URL` | MinIO/S3 endpoint |
| `OPENAI_API_KEY` | OpenAI API key (embeddings) |
| `ANTHROPIC_API_KEY` | Anthropic API key (agents) |
| `TAVILY_API_KEY` | Tavily API key (web search) |

### 3. Start Infrastructure

```bash
make infra
```

This starts PostgreSQL (pgvector), Redis, and MinIO via Docker Compose.

### 4. Backend Setup

```bash
cd backend
poetry install
poetry run alembic upgrade head   # Apply database migrations
```

### 5. Frontend Setup

```bash
cd frontend
pnpm install
```

### 6. Run the Application

**Terminal 1** — Backend API server:
```bash
make dev
```

**Terminal 2** — Celery worker (document processing):
```bash
make worker
```

**Terminal 3** — Frontend dev server:
```bash
cd frontend && pnpm dev
```

The app will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

---

## Usage

1. **Register** — Create an account at `/register`
2. **Onboard** — Set up your workspace and venture profile
3. **Chat** — Ask questions and get expert guidance from specialized AI agents
4. **Upload** — Drag-and-drop documents for automatic processing, chunking, and embedding
5. **Artifacts** — Create, iterate, and export pitch decks, financial models, lean canvases, and more
6. **Tools** — Run valuations, readiness scoring, scenario modeling, and benchmarking
7. **Profile** — View your venture's knowledge graph, entities, and metrics

---

## Testing

### Backend

```bash
make test          # Run all backend tests (217 tests)
make lint          # Run ruff + mypy (strict mode)
```

### Frontend

```bash
cd frontend
pnpm test          # Run all frontend tests (33 tests)
pnpm lint          # Run ESLint
pnpm build         # Type-check + production build
```

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   └── routes/       # auth, chat, artifacts, brain, documents, tools
│   │   ├── core/
│   │   │   ├── agents/       # 11 specialized AI agents + registry
│   │   │   ├── artifacts/    # Artifact manager, diff engine, exporters
│   │   │   ├── brain/        # Knowledge graph, RAG retriever, event store
│   │   │   ├── benchmarks/   # Benchmark engine + data
│   │   │   ├── router/       # MoE router + intent classifier
│   │   │   ├── scoring/      # Investor readiness scorer
│   │   │   ├── scenario/     # Scenario modeler
│   │   │   ├── skills/       # SkillLoader class for agent expertise injection
│   │   │   ├── tools/        # Tool registry, executor, 14 tool handlers
│   │   ├── mcp/              # MCP servers (analytics, brain, research, memory) + client
│   │   ├── skills/           # 11 SKILL.md files + shared knowledge + references
│   │   │   ├── {agent-name}/ # Per-agent SKILL.md + optional references/
│   │   │   └── shared/       # vc_fundamentals, fundraising_stages, market_sizing, etc.
│   │   │   ├── success_stories/  # Success story matcher
│   │   │   └── valuation/    # Valuation engine
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Storage & embedding services
│   │   ├── skills/           # Agent skill definitions (YAML+templates)
│   │   ├── templates/        # Jinja2 export templates
│   │   ├── middleware/       # Rate limiting, Prometheus metrics
│   │   ├── workers/          # Celery tasks (document processing, PDF export)
│   │   └── main.py           # FastAPI application entry point
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend test suite
│   └── pyproject.toml        # Python dependencies (Poetry)
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/           # Login & register pages
│   │   └── (dashboard)/      # Chat, artifacts, profile, documents, tools, settings
│   ├── components/
│   │   ├── chat/             # Chat UI (sidebar, messages, input, streaming)
│   │   ├── artifacts/        # Artifact grid, detail view, renderers, version diff
│   │   ├── documents/        # Document list & upload dropzone
│   │   ├── profile/          # Venture header, entity cards, metrics
│   │   ├── charts/           # Radar, Waterfall, Percentile bar charts
│   │   ├── tools/            # 9 interactive tool components
│   │   ├── layout/           # Sidebar, header, mobile nav
│   │   ├── onboarding/       # 3-step onboarding wizard
│   │   └── ui/               # shadcn/ui base components
│   ├── lib/
│   │   ├── api/              # Axios client + domain API modules
│   │   ├── hooks/            # React Query hooks + streaming
│   │   ├── stores/           # Zustand state stores
│   │   ├── types/            # TypeScript type definitions
│   │   └── utils/            # Formatters, agent metadata, helpers
│   └── __tests__/            # Frontend test suite
│
├── docker-compose.yml        # Infrastructure services
├── Makefile                  # Development commands
└── .env.example              # Environment variable template
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login and get JWT token |
| `POST` | `/api/workspaces` | Create workspace |
| `GET` | `/api/workspaces` | List workspaces |
| `POST` | `/api/chat/send` | Send a chat message (supports SSE streaming) |
| `GET` | `/api/chat/sessions` | List chat sessions |
| `POST` | `/api/brain/search` | Search the startup brain (RAG + KG) |
| `GET` | `/api/brain/profile/{id}` | Get venture profile snapshot |
| `POST` | `/api/documents/upload` | Upload a document |
| `POST` | `/api/artifacts` | Create an artifact |
| `GET` | `/api/artifacts` | List artifacts |
| `POST` | `/api/scoring/readiness` | Run investor readiness scoring |
| `POST` | `/api/valuation/calculate` | Run valuation analysis |
| `POST` | `/api/scenarios/model` | Run scenario modeling |
| `GET` | `/health` | Health check |

### MCP Server Endpoints

| Mount Path | Server | Protocol |
|---|---|---|
| `/mcp/analytics` | VC Analytics — 5 engine tools | MCP over HTTP+SSE |
| `/mcp/brain` | Startup Brain — 4 tools + 2 resources | MCP over HTTP+SSE |
| `/mcp/research` | Market Research — 2 tools | MCP over HTTP+SSE |
| `/mcp/memory` | Agent Memory — 3 tools + 2 resources | MCP over HTTP+SSE |

---

## License

This project is proprietary. All rights reserved.
