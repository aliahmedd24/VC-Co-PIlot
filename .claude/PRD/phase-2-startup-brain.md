# Phase 2: Startup Brain — RAG + Knowledge Graph

> **Timeline:** Weeks 4–6  
> **Priority:** Critical — provides the shared context layer all agents consume  
> **Depends on:** Phase 1 (database, models, document indexing)  
> **Claude Code Tag:** `phase-2`

---

## Objective

Build the "Startup Brain" — a unified retrieval layer that combines freshness-weighted RAG search over embedded document chunks with a structured Knowledge Graph (KG) of venture entities (market, competitors, ICP, metrics, team, etc.). Agents will call `brain.retrieve()` for a single interface that returns relevant document chunks, KG entities, and citation metadata. An event-sourcing system tracks every KG mutation for audit and conflict detection.

---

## Tech Stack

| Layer | Tool | Notes |
|-------|------|-------|
| RAG Retrieval | pgvector + raw SQL | Freshness-weighted cosine similarity |
| Knowledge Graph | PostgreSQL JSONB + SQLAlchemy | Entity–Relation model stored relationally |
| Entity Extraction | Anthropic Claude API | Structured extraction via system prompts |
| Embeddings | OpenAI `text-embedding-3-small` | Reuses Phase 1 EmbeddingService |
| Event Store | PostgreSQL JSONB table | Append-only log of KG mutations |
| API | FastAPI routes under `/api/v1/brain/` | — |
| Background | Celery task for extraction pipeline | — |

---

## User Flow

### 1. Automatic Entity Extraction (Background)
1. After a document reaches `INDEXED` status (Phase 1), a follow-up Celery task `extract_entities(document_id)` fires.
2. The task loads the document's chunks, sends them in batches to Claude with a structured extraction prompt.
3. Claude returns structured JSON: entities with `type`, `data`, `confidence`.
4. Each entity is upserted into the KG via `KnowledgeGraph.create_entity()`. If an existing entity of the same type+key exists, a conflict is flagged (status `NEEDS_REVIEW`).
5. Evidence links are created tying each entity back to the source chunk/document.
6. An event is appended to the event store for each mutation.

### 2. Manual Entity CRUD (API)
1. User sends `POST /api/v1/brain/entities` with `{ venture_id, type, data }` to manually create an entity.
2. User sends `PATCH /api/v1/brain/entities/{id}` to update entity data or confirm/pin status.
3. User sends `DELETE /api/v1/brain/entities/{id}` to remove an entity.
4. All mutations go through the event store.

### 3. Venture Profile View (API)
1. User sends `GET /api/v1/brain/profile/{workspace_id}`.
2. Backend returns the venture metadata plus all KG entities grouped by type, with evidence counts and confidence scores.

### 4. Brain Search (API)
1. User sends `POST /api/v1/brain/search` with `{ workspace_id, query, entity_types?, max_chunks? }`.
2. Backend calls `StartupBrain.retrieve()` which runs RAG search and KG keyword search in parallel via `asyncio.gather`.
3. Returns combined results: ranked document chunks + matching KG entities + citation metadata.

---

## Technical Constraints

- **RAG search must use freshness-weighted scoring:** `final_score = cosine_similarity × exp(-0.693 × age_days / 70)`. Half-life = 70 days.
- **Entity extraction prompt must enforce JSON output** — use Claude with a structured system prompt and `<!-- JSON_OUTPUT -->` markers. Parse with `json.loads` and validate against Pydantic models.
- **Confidence auto-thresholding:** ≥ 0.85 → `CONFIRMED`, ≥ 0.60 → `NEEDS_REVIEW`, < 0.60 → `SUGGESTED`.
- **Entity search** uses keyword matching against JSONB `data` field (PostgreSQL `@>` or text search). Not vector-based.
- **Event store is append-only** — no UPDATE/DELETE on `kg_events`. Each row is an immutable log entry.
- **All Brain API routes** require workspace membership (reuse `get_workspace` dependency from Phase 1).
- **Conflict detection:** When extracting a new entity of the same `type` where `data` contains a matching key (e.g., same competitor name), mark as `NEEDS_REVIEW` and link both entities via a `KGRelation` of type `CONFLICTS_WITH`.
- **Max 50 entities per venture per type** to prevent runaway extraction.

---

## Data Schema

### KG Entities (from Phase 1 migration, fleshed out here)

```python
class KGEntityType(str, Enum):
    VENTURE = "venture"
    MARKET = "market"
    ICP = "icp"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    TEAM_MEMBER = "team_member"
    METRIC = "metric"
    FUNDING_ASSUMPTION = "funding_assumption"
    RISK = "risk"

class KGEntityStatus(str, Enum):
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    SUGGESTED = "suggested"
    PINNED = "pinned"

class KGEntity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_entities"
    venture_id: FK → ventures.id (CASCADE), indexed
    type: Enum(KGEntityType), indexed
    status: Enum(KGEntityStatus), default NEEDS_REVIEW
    data: JSONB, default {}              # Flexible structured data per type
    confidence: Float, default 0.5
    evidence: relationship → KGEvidence[]
```

### KG Evidence

```python
class KGEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_evidence"
    entity_id: FK → kg_entities.id (CASCADE), indexed
    snippet: Text                         # Source text excerpt
    document_id: FK → documents.id (SET NULL), nullable
    source_type: String(50)               # "document", "chat", "manual"
    agent_id: String(100), nullable       # Which agent extracted this
```

### KG Relations

```python
class KGRelationType(str, Enum):
    COMPETES_WITH = "competes_with"
    TARGETS = "targets"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    BELONGS_TO = "belongs_to"

class KGRelation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_relations"
    from_entity_id: FK → kg_entities.id (CASCADE), indexed
    to_entity_id: FK → kg_entities.id (CASCADE), indexed
    type: Enum(KGRelationType)
    metadata: JSONB, nullable
```

### Event Store

```python
class KGEventType(str, Enum):
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    ENTITY_CONFIRMED = "entity_confirmed"
    RELATION_CREATED = "relation_created"
    CONFLICT_DETECTED = "conflict_detected"

class KGEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_events"
    venture_id: FK → ventures.id (CASCADE), indexed
    event_type: Enum(KGEventType)
    entity_id: String, nullable           # Affected entity UUID
    payload: JSONB                         # Full event data (before/after)
    actor: String(100)                     # "system", "user:<id>", "agent:<id>"
```

### Pydantic Schemas

```python
# Brain Search
class BrainSearchRequest(BaseModel):
    workspace_id: str
    query: str
    entity_types: Optional[list[KGEntityType]] = None
    max_chunks: int = 10  # 1..50

class ChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity: float
    freshness_weight: float
    final_score: float

class EntityResult(BaseModel):
    id: str
    type: KGEntityType
    status: KGEntityStatus
    data: dict
    confidence: float
    evidence_count: int

class BrainSearchResponse(BaseModel):
    chunks: list[ChunkResult]
    entities: list[EntityResult]
    citations: list[dict]

# Entity CRUD
class EntityCreate(BaseModel):
    venture_id: str
    type: KGEntityType
    data: dict
    confidence: float = 0.5

class EntityUpdate(BaseModel):
    data: Optional[dict] = None
    status: Optional[KGEntityStatus] = None
    confidence: Optional[float] = None

# Venture Profile
class VentureProfileResponse(BaseModel):
    venture: VentureResponse
    entities_by_type: dict[str, list[EntityResult]]
    total_documents: int
    total_entities: int
```

---

## Key Files to Create / Modify

```
backend/app/
├── core/
│   └── brain/
│       ├── __init__.py
│       ├── startup_brain.py            # StartupBrain: unified retrieve() + get_snapshot()
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── retriever.py            # RAGRetriever: freshness-weighted pgvector search
│       │   └── chunker.py              # Text chunking utility (500 tokens, 50 overlap)
│       ├── kg/
│       │   ├── __init__.py
│       │   ├── knowledge_graph.py      # KnowledgeGraph: CRUD, search, relations
│       │   └── entity_extractor.py     # Claude-based structured extraction
│       └── events/
│           ├── __init__.py
│           └── event_store.py          # Append-only event log
│
├── api/routes/
│   └── brain.py                        # /profile, /search, /entities CRUD
│
├── models/
│   ├── kg_entity.py                    # Add KGRelation model
│   └── kg_event.py                     # New: KGEvent model
│
├── schemas/
│   └── brain.py                        # Request/Response schemas
│
└── workers/
    └── document_tasks.py               # Add extract_entities task
```

### Alembic Migration

```
alembic/versions/002_knowledge_graph.py
  - kg_relations table
  - kg_events table
  - Index on kg_events(venture_id, created_at)
```

---

## Definition of Done

### Automated Tests

1. **RAG Retriever Tests**
   - `test_search_returns_ranked_chunks` → Insert 10 chunks with known embeddings. Search returns them ordered by `final_score` descending.
   - `test_freshness_weighting` → Two chunks with same similarity but different ages. Newer chunk scores higher.
   - `test_search_scoped_to_venture` → Chunks from other ventures are never returned.
   - `test_empty_query` → Returns empty list, no error.

2. **Knowledge Graph Tests**
   - `test_create_entity` → Creates entity, auto-sets status based on confidence threshold.
   - `test_update_entity` → Merges `data` dict correctly.
   - `test_search_entities_by_keyword` → Keyword in entity `data` matches; unrelated entities excluded.
   - `test_search_entities_by_type_filter` → Only requested types returned.
   - `test_conflict_detection` → Two entities of same type with overlapping key trigger `NEEDS_REVIEW` + `CONFLICTS_WITH` relation.
   - `test_max_entities_per_type` → 51st entity of same type raises ValidationError.

3. **Entity Extraction Tests**
   - `test_extract_entities_from_chunks` → Mock Claude response → correct entities created with evidence links.
   - `test_extraction_invalid_json` → Gracefully handles malformed Claude output; logs warning, skips entity.

4. **Event Store Tests**
   - `test_event_created_on_entity_create` → `ENTITY_CREATED` event logged with correct payload.
   - `test_event_created_on_entity_update` → `ENTITY_UPDATED` event contains before/after snapshot.
   - `test_events_are_immutable` → Attempting to UPDATE a `kg_events` row raises error (DB constraint or application logic).

5. **StartupBrain Integration Tests**
   - `test_retrieve_combines_rag_and_kg` → Returns both chunks and entities for a query.
   - `test_get_snapshot` → Returns venture + entities grouped by type.

6. **API Route Tests**
   - `test_brain_search` → POST `/brain/search` returns `BrainSearchResponse`.
   - `test_create_entity_api` → POST `/brain/entities` returns created entity.
   - `test_update_entity_api` → PATCH `/brain/entities/{id}` returns updated entity.
   - `test_delete_entity_api` → DELETE `/brain/entities/{id}` returns 204; entity gone.
   - `test_venture_profile` → GET `/brain/profile/{workspace_id}` returns full profile.
   - `test_brain_routes_require_auth` → All brain routes return 401 without token.

### Manual / CI Checks

- Entity extraction Celery task completes successfully on a sample PDF upload.
- `kg_events` table has correct entries after a sequence of create/update/delete operations.
- RAG search latency < 500ms for a venture with 100 chunks (measured via `EXPLAIN ANALYZE`).
- `ruff check .` and `mypy .` pass.
