# Phase 4: Artifact System + Advanced Document Processing

> **Timeline:** Weeks 11–13  
> **Priority:** High — core deliverable for user-facing output  
> **Depends on:** Phase 3 (agents that produce artifacts)  
> **Claude Code Tag:** `phase-4`

---

## Objective

Build the Artifact System — a versioned, structured document workspace where agents create and iteratively refine deliverables (Lean Canvases, pitch narratives, valuation memos, deck outlines, etc.). Each artifact has full version history with JSON diff tracking, supports in-context chat for refinement, and can be exported to Markdown or PDF. Additionally, enhance the document processing pipeline with advanced parsers for PPTX, XLSX, and improved PDF extraction.

---

## Tech Stack

| Layer | Tool | Notes |
|-------|------|-------|
| Artifact Storage | PostgreSQL JSONB | Structured content per artifact type |
| Version Diffing | `deepdiff` Python library | JSON-level structural diffs |
| Export — Markdown | Custom Python renderer | Jinja2 templates per artifact type |
| Export — PDF | `weasyprint` or `reportlab` | HTML→PDF via Jinja2 templates |
| Document Parsing | `pypdf`, `python-pptx`, `python-docx`, `openpyxl`, `unstructured` | Enhanced extraction |
| Background Export | Celery task | Heavy exports run async |
| API | FastAPI routes `/api/v1/artifacts/` | — |

---

## User Flow

### 1. Artifact Creation (Agent-Initiated)
1. During a chat, an agent determines an artifact is needed (via `routing_plan.artifact_needed`).
2. Agent calls the artifact manager: `ArtifactManager.create(workspace_id, type, title, content, owner_agent)`.
3. Manager creates the `Artifact` row (status=DRAFT) and an initial `ArtifactVersion` (version=1).
4. Agent returns the `artifact_id` in its response.
5. User sees the artifact rendered in the UI alongside the chat.

### 2. Artifact Refinement (Chat-in-Context)
1. User sends `POST /api/v1/artifacts/{id}/chat` with `{ content }` — a message scoped to this artifact.
2. The artifact's `owner_agent` is invoked with the artifact's current content injected as additional context.
3. Agent produces an updated version of the artifact content.
4. `ArtifactManager.update()` computes the diff, increments the version, saves both the new content and the diff.
5. Updated artifact returned to user.

### 3. Artifact Browsing
1. `GET /api/v1/artifacts?workspace_id=...` → list all artifacts with type, status, title, last updated.
2. `GET /api/v1/artifacts/{id}` → full artifact with current content.
3. `GET /api/v1/artifacts/{id}/versions` → list all versions with diffs.
4. `GET /api/v1/artifacts/{id}/versions/{version}` → specific version content.

### 4. Artifact Export
1. `POST /api/v1/artifacts/{id}/export` with `{ format: "markdown" | "pdf" }`.
2. For Markdown: synchronous response with rendered content.
3. For PDF: enqueue Celery task, return `{ task_id }`. User polls `GET /api/v1/tasks/{task_id}` for status and download URL.

### 5. Artifact Status Management
1. User can `PATCH /api/v1/artifacts/{id}` to change status: DRAFT → IN_PROGRESS → READY → ARCHIVED.
2. ARCHIVED artifacts are excluded from default list queries.

---

## Technical Constraints

- **Artifact content is stored as JSONB** — each artifact type has a defined schema (see below). The content field is NOT free-form text.
- **Version diffs** use `deepdiff` library to compute structural changes between JSONB versions. Diffs are stored as JSONB in `ArtifactVersion.diff`.
- **Max 100 versions per artifact** — after 100, oldest non-initial versions are pruned (initial version always preserved).
- **Artifact chat messages** are regular `ChatMessage` rows with `artifact_id` set, linking them to the artifact.
- **Export templates** use Jinja2. Each artifact type has its own Markdown template and PDF/HTML template.
- **PDF export** must handle unicode, tables, and basic formatting. Use `weasyprint` (HTML→PDF approach).
- **Concurrent edit protection:** Artifact updates use optimistic locking — the PATCH request must include `expected_version`. If the DB version differs, return 409 Conflict.
- **Artifact content size limit:** 500KB per version (JSONB serialized).

---

## Data Schema

### Artifacts (already defined in Phase 1 migration)

```python
class ArtifactType(str, Enum):
    LEAN_CANVAS = "lean_canvas"
    RESEARCH_BRIEF = "research_brief"
    PITCH_NARRATIVE = "pitch_narrative"
    DECK_OUTLINE = "deck_outline"
    FINANCIAL_MODEL = "financial_model"
    VALUATION_MEMO = "valuation_memo"
    DATAROOM_STRUCTURE = "dataroom_structure"
    KPI_DASHBOARD = "kpi_dashboard"
    BOARD_MEMO = "board_memo"
    CUSTOM = "custom"

class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ARCHIVED = "archived"

class Artifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifacts"
    workspace_id: FK → workspaces.id (CASCADE), indexed
    type: Enum(ArtifactType)
    title: String(255)
    status: Enum(ArtifactStatus), default DRAFT
    owner_agent: String(100)
    content: JSONB, default {}
    assumptions: JSONB, nullable        # List of tracked assumptions
    created_by_id: FK → users.id (SET NULL), nullable
    current_version: Integer, default 1
    versions: relationship → ArtifactVersion[]
    messages: relationship → ChatMessage[]

class ArtifactVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifact_versions"
    artifact_id: FK → artifacts.id (CASCADE), indexed
    version: Integer
    content: JSONB
    diff: JSONB, nullable                # deepdiff output from previous version
    created_by: String(100), nullable    # "user:<id>" or "agent:<id>"
```

### Artifact Content Schemas (Pydantic — for validation, not DB)

```python
class LeanCanvasContent(BaseModel):
    problem: list[str] = []
    solution: list[str] = []
    key_metrics: list[str] = []
    unique_value_prop: str = ""
    unfair_advantage: str = ""
    channels: list[str] = []
    customer_segments: list[str] = []
    cost_structure: list[str] = []
    revenue_streams: list[str] = []

class PitchNarrativeContent(BaseModel):
    hook: str = ""
    problem_story: str = ""
    solution_reveal: str = ""
    traction_proof: str = ""
    market_opportunity: str = ""
    business_model: str = ""
    team_story: str = ""
    ask: str = ""
    vision: str = ""

class DeckOutlineContent(BaseModel):
    slides: list[SlideOutline] = []

class SlideOutline(BaseModel):
    title: str
    key_points: list[str]
    visual_suggestion: str = ""
    speaker_notes: str = ""

class ValuationMemoContent(BaseModel):
    methodology: str = ""
    comparables: list[dict] = []
    assumptions: list[dict] = []
    range_low: Optional[float] = None
    range_high: Optional[float] = None
    recommended: Optional[float] = None
    narrative: str = ""

class FinancialModelContent(BaseModel):
    revenue_projections: list[dict] = []   # {period, amount, assumptions}
    cost_projections: list[dict] = []
    runway_months: Optional[int] = None
    burn_rate: Optional[float] = None
    unit_economics: dict = {}
    funding_scenarios: list[dict] = []

class KPIDashboardContent(BaseModel):
    metrics: list[KPIMetric] = []

class KPIMetric(BaseModel):
    name: str
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: str = ""
    trend: str = ""                        # "up", "down", "flat"
    category: str = ""                     # "growth", "retention", "financial"

class DataroomStructureContent(BaseModel):
    categories: list[DataroomCategory] = []

class DataroomCategory(BaseModel):
    name: str
    required_docs: list[str]
    uploaded_docs: list[str] = []
    completion_pct: float = 0.0
```

### API Schemas

```python
class ArtifactCreate(BaseModel):
    workspace_id: str
    type: ArtifactType
    title: str
    content: Optional[dict] = None

class ArtifactUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ArtifactStatus] = None
    content: Optional[dict] = None
    expected_version: int                  # Optimistic locking

class ArtifactChatRequest(BaseModel):
    content: str                           # User's refinement instruction

class ArtifactExportRequest(BaseModel):
    format: Literal["markdown", "pdf"]

class ArtifactResponse(BaseModel):
    id: str
    type: ArtifactType
    title: str
    status: ArtifactStatus
    owner_agent: str
    content: dict
    current_version: int
    assumptions: Optional[list[dict]]
    created_at: datetime
    updated_at: datetime

class ArtifactVersionResponse(BaseModel):
    id: str
    version: int
    content: dict
    diff: Optional[dict]
    created_by: Optional[str]
    created_at: datetime

class ExportTaskResponse(BaseModel):
    task_id: str
    status: str                            # "pending", "complete", "failed"
    download_url: Optional[str] = None
```

---

## Key Files to Create / Modify

```
backend/app/
├── core/
│   └── artifacts/
│       ├── __init__.py
│       ├── manager.py                  # ArtifactManager: create, update, get, list
│       ├── diff_engine.py              # Compute + store deepdiff between versions
│       ├── content_schemas.py          # Pydantic schemas for each artifact type
│       └── exporters/
│           ├── __init__.py
│           ├── markdown_exporter.py    # Jinja2 → Markdown
│           └── pdf_exporter.py         # Jinja2 → HTML → weasyprint → PDF
│
├── api/routes/
│   └── artifacts.py                    # Full CRUD + chat + export + versions
│
├── schemas/
│   └── artifact.py                     # API request/response schemas
│
├── workers/
│   └── export_tasks.py                 # Celery task for PDF export
│
└── templates/                          # Jinja2 templates
    ├── artifacts/
    │   ├── lean_canvas.md.j2
    │   ├── lean_canvas.html.j2
    │   ├── pitch_narrative.md.j2
    │   ├── pitch_narrative.html.j2
    │   ├── deck_outline.md.j2
    │   ├── valuation_memo.md.j2
    │   └── ... (one per artifact type)
    └── base.html.j2                    # PDF base template with styles
```

### Alembic Migration

```
alembic/versions/003_artifact_versions.py
  - Add current_version column to artifacts
  - Create indexes on artifact_versions(artifact_id, version)
  - Add unique constraint: (artifact_id, version)
```

---

## Definition of Done

### Automated Tests

1. **ArtifactManager Tests**
   - `test_create_artifact` → Creates artifact + initial version (v1). Content matches. Status = DRAFT.
   - `test_update_artifact_content` → Increments version, stores diff, updates current content.
   - `test_optimistic_locking` → Update with wrong `expected_version` raises 409.
   - `test_max_versions_pruning` → After 101 versions, oldest non-initial version is deleted.
   - `test_content_size_limit` → Content exceeding 500KB raises 413.

2. **Diff Engine Tests**
   - `test_diff_added_field` → New key in content detected as "added".
   - `test_diff_changed_value` → Changed value detected as "changed" with old/new.
   - `test_diff_removed_field` → Removed key detected.
   - `test_diff_nested_change` → Change inside nested object correctly tracked.
   - `test_diff_identical` → Identical content produces empty diff.

3. **Content Schema Validation Tests**
   - `test_lean_canvas_valid` → Valid LeanCanvasContent parses correctly.
   - `test_lean_canvas_defaults` → Empty dict produces valid defaults.
   - `test_financial_model_valid` → Valid FinancialModelContent parses.
   - One test per artifact type for valid content.

4. **Export Tests**
   - `test_markdown_export_lean_canvas` → Produces valid Markdown string with all sections.
   - `test_markdown_export_deck_outline` → Slides rendered as numbered sections.
   - `test_pdf_export_produces_file` → PDF bytes are valid (starts with `%PDF`).
   - `test_pdf_export_unicode` → Unicode characters render correctly.

5. **Artifact Chat Tests**
   - `test_artifact_chat_creates_message` → Message created with `artifact_id` set.
   - `test_artifact_chat_updates_artifact` → Artifact content updated after agent response.
   - `test_artifact_chat_routes_to_owner_agent` → Request routed to artifact's `owner_agent`.

6. **API Route Tests**
   - `test_create_artifact_api` → POST returns created artifact.
   - `test_list_artifacts` → GET returns artifacts for workspace (excludes ARCHIVED by default).
   - `test_get_artifact` → GET returns full artifact with content.
   - `test_update_artifact_status` → PATCH changes status.
   - `test_list_versions` → GET returns version history.
   - `test_get_specific_version` → GET returns version content.
   - `test_export_markdown` → POST returns Markdown text.
   - `test_export_pdf` → POST returns task_id; task eventually produces download URL.
   - `test_artifact_routes_require_auth` → 401 without token.
   - `test_artifact_workspace_access` → 404 for artifacts in other workspaces.

### Manual / CI Checks

- Create a Lean Canvas artifact through agent chat, refine it twice, verify version history shows 3 versions with correct diffs.
- Export a valuation memo to PDF, open it, verify formatting and content.
- `ruff check .` and `mypy .` pass.
- All Jinja2 templates render without errors for sample data.
