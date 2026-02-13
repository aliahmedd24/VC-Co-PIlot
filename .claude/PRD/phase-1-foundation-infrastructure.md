# Phase 1: Foundation & Infrastructure

> **Timeline:** Weeks 1–3  
> **Priority:** Critical — all subsequent phases depend on this  
> **Claude Code Tag:** `phase-1`

---

## Objective

Stand up the core project scaffolding, database schema, authentication system, workspace management, and document upload pipeline. By the end of this phase a developer can register, log in, create a workspace with a venture, upload a document to S3/MinIO, and have that document chunked, embedded, and indexed into pgvector for later RAG retrieval.

---

## Tech Stack

| Layer | Tool | Version / Notes |
|-------|------|-----------------|
| Runtime | Python | 3.12+ |
| Framework | FastAPI | 0.111+ |
| ORM | SQLAlchemy 2.0 | Async via `asyncpg` |
| Migrations | Alembic | — |
| Validation | Pydantic 2.x | — |
| Auth | python-jose (JWT) + passlib (bcrypt) | — |
| Database | PostgreSQL 16 + pgvector | HNSW index on embeddings |
| Cache / Queue | Redis 7.x | Broker for Celery |
| Object Storage | MinIO (dev) / S3 (prod) | boto3 client |
| Task Queue | Celery 5.4 | For async doc processing |
| Embeddings | OpenAI `text-embedding-3-small` | 1536 dims |
| Logging | structlog | JSON output |
| Package Manager | Poetry | — |
| Containers | Docker Compose | pgvector image, Redis, MinIO |

---

## User Flow

### 1. Registration & Login
1. User sends `POST /api/v1/auth/register` with `{ email, password, name }`.
2. Backend hashes password with bcrypt, creates `User` row, returns JWT access token.
3. User sends `POST /api/v1/auth/login` with email/password, receives JWT.
4. All subsequent requests include `Authorization: Bearer <token>`.

### 2. Workspace & Venture Setup
1. Authenticated user sends `POST /api/v1/workspaces` with `{ name }`.
2. Backend creates `Workspace` (auto-generates slug), creates `WorkspaceMembership` with role `OWNER`, and creates a stub `Venture` linked to that workspace.
3. User can `PATCH /api/v1/workspaces/{id}/venture` to fill in venture details (name, stage, one-liner, problem, solution).

### 3. Document Upload & Indexing
1. User sends `POST /api/v1/documents/upload` as multipart form with `workspace_id` and file.
2. Backend validates file type (PDF, PPTX, DOCX, XLSX, TXT), streams to S3/MinIO, creates `Document` row with status `PENDING`.
3. Backend enqueues a Celery task `process_document(document_id)`.
4. Worker picks up task → sets status to `PROCESSING` → extracts text (via `pypdf`/`python-pptx`/`python-docx`/`openpyxl`) → chunks text (500-token paragraphs with 50-token overlap) → calls OpenAI embedding API in batches → inserts `DocumentChunk` rows with vectors → sets status to `INDEXED`.
5. User can poll `GET /api/v1/documents?workspace_id=...` to see document status.

---

## Technical Constraints

- **All database operations must be async** (`asyncpg` driver, `async_sessionmaker`).
- **JWT tokens** must expire in 24 hours; algorithm `HS256`.
- **File upload limit:** 50 MB per file.
- **Accepted MIME types:** `application/pdf`, `application/vnd.openxmlformats-officedocument.*`, `text/plain`, `text/csv`.
- **Embedding batch size:** Max 100 texts per OpenAI API call.
- **Chunk strategy:** 500 tokens per chunk, 50-token overlap, paragraph-boundary aware.
- **pgvector HNSW index:** `m=16`, `ef_construction=64`, `vector_cosine_ops`.
- **Docker Compose** must include health checks for Postgres and Redis; backend waits on both.
- **Environment variables** loaded via `pydantic-settings` from `.env` file.
- **CORS** must allow `http://localhost:3000` in development.

---

## Data Schema

### Users

```python
class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str]          # String(255), unique, indexed
    hashed_password: Mapped[str] # String(255)
    name: Mapped[Optional[str]] # String(255), nullable
    is_active: Mapped[bool]     # default True
    is_superuser: Mapped[bool]  # default False
    workspace_memberships: relationship → WorkspaceMembership[]
```

### Workspaces

```python
class WorkspaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    ADVISOR = "advisor"

class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"
    name: Mapped[str]           # String(255)
    slug: Mapped[str]           # String(255), unique, indexed
    memberships: relationship → WorkspaceMembership[]
    venture: relationship → Venture (one-to-one)
    documents: relationship → Document[]
    artifacts: relationship → Artifact[]
    chat_sessions: relationship → ChatSession[]

class WorkspaceMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspace_memberships"
    user_id: FK → users.id (CASCADE)
    workspace_id: FK → workspaces.id (CASCADE)
    role: Enum(WorkspaceRole), default MEMBER
```

### Ventures

```python
class VentureStage(str, Enum):
    IDEATION = "ideation"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    GROWTH = "growth"
    EXIT = "exit"

class Venture(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ventures"
    workspace_id: FK → workspaces.id (CASCADE), unique
    name: Mapped[str]             # String(255)
    stage: Enum(VentureStage)     # default IDEATION
    one_liner: Mapped[Optional[str]]  # String(500)
    problem: Mapped[Optional[str]]    # Text
    solution: Mapped[Optional[str]]   # Text
    entities: relationship → KGEntity[]
```

### Documents & Chunks

```python
class DocumentType(str, Enum):
    PITCH_DECK / FINANCIAL_MODEL / BUSINESS_PLAN / PRODUCT_DOC / OTHER

class DocumentStatus(str, Enum):
    PENDING / PROCESSING / INDEXED / FAILED

class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"
    workspace_id: FK → workspaces.id (CASCADE), indexed
    name: String(255)
    type: Enum(DocumentType), default OTHER
    mime_type: String(100)
    size: Integer (bytes)
    storage_key: String(500)       # S3 object key
    status: Enum(DocumentStatus), default PENDING
    metadata: JSONB, nullable
    error_message: Text, nullable
    chunks: relationship → DocumentChunk[]

class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_chunks"
    document_id: FK → documents.id (CASCADE), indexed
    venture_id: FK → ventures.id (CASCADE), indexed
    content: Text
    embedding: Vector(1536), nullable
    chunk_index: Integer
    metadata: JSONB, nullable
    # HNSW index on embedding column
```

### Pydantic Request/Response Schemas

```python
# Auth
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str  # min_length=8
    name: Optional[str]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Workspace
class WorkspaceCreate(BaseModel):
    name: str  # min_length=1, max_length=255

class VentureUpdate(BaseModel):
    name: Optional[str]
    stage: Optional[VentureStage]
    one_liner: Optional[str]
    problem: Optional[str]
    solution: Optional[str]

# Document
class DocumentResponse(BaseModel):
    id: str
    name: str
    type: DocumentType
    status: DocumentStatus
    size: int
    created_at: datetime
```

---

## Key Files to Create

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app, CORS, lifespan, health check
│   ├── config.py                       # Pydantic Settings class
│   ├── dependencies.py                 # Engine, async session maker, get_db()
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py                   # Include sub-routers
│   │   ├── deps.py                     # get_current_user, get_workspace
│   │   └── routes/
│   │       ├── auth.py                 # /register, /login
│   │       ├── workspaces.py           # CRUD + venture update
│   │       └── documents.py            # Upload + list
│   │
│   ├── models/
│   │   ├── base.py                     # Base, UUIDMixin, TimestampMixin
│   │   ├── user.py
│   │   ├── workspace.py                # Workspace + WorkspaceMembership
│   │   ├── venture.py
│   │   └── document.py                 # Document + DocumentChunk
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── workspace.py
│   │   └── document.py
│   │
│   ├── services/
│   │   ├── embedding_service.py        # OpenAI embed / embed_batch
│   │   └── storage_service.py          # S3/MinIO upload/download
│   │
│   └── workers/
│       ├── celery_app.py               # Celery configuration
│       └── document_tasks.py           # process_document task
│
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
│
├── tests/
│   ├── conftest.py                     # Test DB, fixtures, TestClient
│   └── unit/
│       ├── test_auth.py
│       ├── test_workspaces.py
│       └── test_documents.py
│
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Definition of Done

### Automated Tests (must all pass)

1. **Auth Tests**
   - `test_register_new_user` → 201, returns valid JWT.
   - `test_register_duplicate_email` → 409.
   - `test_login_valid_credentials` → 200, returns JWT.
   - `test_login_invalid_password` → 401.
   - `test_protected_route_no_token` → 401.
   - `test_protected_route_expired_token` → 401.

2. **Workspace Tests**
   - `test_create_workspace` → 201, creates workspace + membership with OWNER role + stub venture.
   - `test_list_workspaces` → returns only workspaces user is a member of.
   - `test_update_venture` → PATCH returns updated venture fields.
   - `test_workspace_access_denied` → user not in workspace gets 404.

3. **Document Tests**
   - `test_upload_document` → 201, document saved to S3, DB row with status PENDING.
   - `test_upload_invalid_type` → 415 (Unsupported Media Type).
   - `test_upload_exceeds_size_limit` → 413.
   - `test_list_documents` → returns documents for workspace.

4. **Worker Tests** (integration)
   - `test_process_document_happy_path` → Document status transitions PENDING → PROCESSING → INDEXED; `DocumentChunk` rows created with non-null embeddings.
   - `test_process_document_failure` → On parse error, status → FAILED, error_message populated.

### Manual / CI Checks

- `docker-compose up` starts all services without errors.
- `alembic upgrade head` applies cleanly on fresh DB.
- `ruff check .` passes with zero violations.
- `mypy .` passes (strict mode).
- `/health` endpoint returns `{ "status": "healthy" }`.
- pgvector extension is enabled (`SELECT * FROM pg_extension WHERE extname = 'vector'` returns a row).
- HNSW index exists on `document_chunks.embedding`.
