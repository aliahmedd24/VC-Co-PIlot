# AI VC Co-Pilot Platform — Engineering Specification (Python/FastAPI)

> **Document Type:** Claude Code Implementation Guide  
> **Version:** 2.0  
> **Status:** Ready for Implementation  
> **Stack:** Python 3.12 / FastAPI / Next.js Frontend

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Database Schema](#4-database-schema)
5. [Core Configuration](#5-core-configuration)
6. [API Layer](#6-api-layer)
7. [Startup Brain Implementation](#7-startup-brain-implementation)
8. [MoE Router Implementation](#8-moe-router-implementation)
9. [Agent System](#9-agent-system)
10. [Artifact System](#10-artifact-system)
11. [Document Processing](#11-document-processing)
12. [Background Workers](#12-background-workers)
13. [Frontend Integration](#13-frontend-integration)
14. [Testing Strategy](#14-testing-strategy)
15. [Deployment Configuration](#15-deployment-configuration)
16. [Implementation Phases](#16-implementation-phases)

---

## 1. Project Overview

### 1.1 Product Summary

An agentic venture consultancy platform providing AI-powered guidance for startups across all maturity stages. Uses a shared knowledge layer (Startup Brain) and intelligent routing (MoE) to deliver specialized advisory through multiple AI agents.

### 1.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                    │
│                    Next.js 14 (TypeScript)                         │
│              React, TailwindCSS, React Query                       │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTP/WebSocket
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PYTHON BACKEND                                 │
│                    FastAPI + SQLAlchemy                            │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  API Layer  │  │  MoE Router │  │   Agents    │  │  Workers  │ │
│  │  (FastAPI)  │  │             │  │             │  │  (Celery) │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         └────────────────┴────────────────┴────────────────┘       │
│                                  │                                  │
│                    ┌─────────────┴─────────────┐                   │
│                    │      STARTUP BRAIN        │                   │
│                    │   (RAG + Knowledge Graph)  │                   │
│                    └─────────────┬─────────────┘                   │
└──────────────────────────────────┼──────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
│         PostgreSQL + pgvector  │  Redis  │  S3/MinIO              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Technical Requirements

| Requirement | Specification |
|-------------|---------------|
| Router latency (P95) | < 200ms |
| First token latency | < 2s (simple), < 5s (complex) |
| Artifact generation | < 120s |
| Concurrent users/workspace | 10 |
| Uptime SLA | 99.5% |
| Python version | 3.12+ |

---

## 2. Technology Stack

### 2.1 Backend Stack

```yaml
runtime: Python 3.12
framework: FastAPI 0.111+
package_manager: Poetry

core:
  api: FastAPI
  orm: SQLAlchemy 2.0 (async)
  migrations: Alembic
  validation: Pydantic 2.x
  
ai_ml:
  llm: anthropic (Claude API)
  embeddings: openai / sentence-transformers
  rag: langchain / llama-index
  document_processing: unstructured, pypdf, python-pptx, python-docx
  
data:
  database: PostgreSQL 16 + pgvector
  cache: Redis 7.x
  queue: Celery + Redis
  storage: S3 / MinIO
  
observability:
  logging: structlog
  metrics: prometheus-fastapi-instrumentator
  tracing: opentelemetry (optional)
```

### 2.2 Frontend Stack

```yaml
runtime: Node.js 20 LTS
framework: Next.js 14 (App Router)
language: TypeScript 5.x

ui:
  styling: Tailwind CSS 3.x
  components: shadcn/ui
  state: Zustand + React Query
  editor: TipTap (prose), Monaco (code)
  charts: Recharts
```

### 2.3 Python Dependencies (pyproject.toml)

```toml
[tool.poetry]
name = "ai-vc-copilot"
version = "1.0.0"
description = "AI VC Co-Pilot Platform Backend"
python = "^3.12"

[tool.poetry.dependencies]
python = "^3.12"

# FastAPI & Web
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
python-multipart = "^0.0.9"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
httpx = "^0.27.0"

# Database
sqlalchemy = {extras = ["asyncio"], version = "^2.0.30"}
asyncpg = "^0.29.0"
alembic = "^1.13.1"
pgvector = "^0.2.5"
redis = "^5.0.4"

# AI/ML
anthropic = "^0.28.0"
openai = "^1.30.0"
langchain = "^0.2.0"
langchain-anthropic = "^0.1.15"
langchain-openai = "^0.1.8"
langchain-community = "^0.2.0"
sentence-transformers = "^3.0.0"

# Document Processing
unstructured = {extras = ["all-docs"], version = "^0.14.0"}
pypdf = "^4.2.0"
python-pptx = "^0.6.23"
python-docx = "^1.1.0"
openpyxl = "^3.1.2"
pandas = "^2.2.2"

# Task Queue
celery = {extras = ["redis"], version = "^5.4.0"}

# Utilities
pydantic = "^2.7.0"
pydantic-settings = "^2.2.1"
structlog = "^24.2.0"
tenacity = "^8.3.0"
python-slugify = "^8.0.4"
boto3 = "^1.34.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-asyncio = "^0.23.6"
pytest-cov = "^5.0.0"
httpx = "^0.27.0"
factory-boy = "^3.3.0"
faker = "^25.0.0"
ruff = "^0.4.4"
mypy = "^1.10.0"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 3. Project Structure

```
ai-vc-copilot/
│
├── backend/                              # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI application entry
│   │   ├── config.py                     # Configuration management
│   │   ├── dependencies.py               # Dependency injection
│   │   │
│   │   ├── api/                          # API layer
│   │   │   ├── __init__.py
│   │   │   ├── router.py                 # Main API router
│   │   │   ├── deps.py                   # Route dependencies
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── workspaces.py
│   │   │       ├── chat.py
│   │   │       ├── agents.py
│   │   │       ├── brain.py
│   │   │       ├── artifacts.py
│   │   │       └── documents.py
│   │   │
│   │   ├── core/                         # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── agents/                   # Agent implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── registry.py
│   │   │   │   ├── venture_architect.py
│   │   │   │   ├── market_oracle.py
│   │   │   │   ├── storyteller.py
│   │   │   │   ├── deck_architect.py
│   │   │   │   ├── valuation_strategist.py
│   │   │   │   ├── qa_simulator.py
│   │   │   │   ├── dataroom_concierge.py
│   │   │   │   └── kpi_dashboard.py
│   │   │   │
│   │   │   ├── router/                   # MoE Router
│   │   │   │   ├── __init__.py
│   │   │   │   ├── moe_router.py
│   │   │   │   ├── intent_classifier.py
│   │   │   │   └── types.py
│   │   │   │
│   │   │   ├── brain/                    # Startup Brain
│   │   │   │   ├── __init__.py
│   │   │   │   ├── startup_brain.py
│   │   │   │   ├── rag/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── retriever.py
│   │   │   │   │   └── chunker.py
│   │   │   │   ├── kg/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── knowledge_graph.py
│   │   │   │   │   └── entity_extractor.py
│   │   │   │   └── events/
│   │   │   │       ├── __init__.py
│   │   │   │       └── event_store.py
│   │   │   │
│   │   │   ├── artifacts/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py
│   │   │   │   └── diff_engine.py
│   │   │   │
│   │   │   └── documents/
│   │   │       ├── __init__.py
│   │   │       ├── processor.py
│   │   │       └── parsers/
│   │   │
│   │   ├── models/                       # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── workspace.py
│   │   │   ├── venture.py
│   │   │   ├── document.py
│   │   │   ├── kg_entity.py
│   │   │   ├── chat.py
│   │   │   └── artifact.py
│   │   │
│   │   ├── schemas/                      # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── brain.py
│   │   │   └── artifact.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── anthropic_client.py
│   │   │   ├── embedding_service.py
│   │   │   └── storage_service.py
│   │   │
│   │   └── workers/                      # Celery tasks
│   │       ├── __init__.py
│   │       ├── celery_app.py
│   │       └── document_tasks.py
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   │
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/                             # Next.js frontend
│   ├── app/
│   │   ├── (auth)/
│   │   ├── (dashboard)/
│   │   │   ├── chat/
│   │   │   ├── artifacts/
│   │   │   └── profile/
│   │   └── layout.tsx
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 4. Database Schema

### 4.1 Base Model (app/models/base.py)

```python
from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UUIDMixin:
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
```

### 4.2 User Model (app/models/user.py)

```python
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.workspace import WorkspaceMembership


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    workspace_memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

### 4.3 Workspace & Venture Models (app/models/workspace.py, app/models/venture.py)

```python
# app/models/workspace.py
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class WorkspaceRole(str, PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    ADVISOR = "advisor"


class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"
    
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    venture: Mapped[Optional["Venture"]] = relationship(
        back_populates="workspace", uselist=False, cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspace_memberships"
    
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    role: Mapped[WorkspaceRole] = mapped_column(Enum(WorkspaceRole), default=WorkspaceRole.MEMBER)
    
    user: Mapped["User"] = relationship(back_populates="workspace_memberships")
    workspace: Mapped["Workspace"] = relationship(back_populates="memberships")
```

```python
# app/models/venture.py
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class VentureStage(str, PyEnum):
    IDEATION = "ideation"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    GROWTH = "growth"
    EXIT = "exit"


class Venture(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ventures"
    
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(255))
    stage: Mapped[VentureStage] = mapped_column(Enum(VentureStage), default=VentureStage.IDEATION)
    one_liner: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    problem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    workspace: Mapped["Workspace"] = relationship(back_populates="venture")
    entities: Mapped[list["KGEntity"]] = relationship(
        back_populates="venture", cascade="all, delete-orphan"
    )
```

### 4.4 Knowledge Graph Entity (app/models/kg_entity.py)

```python
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Float, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class KGEntityType(str, PyEnum):
    VENTURE = "venture"
    MARKET = "market"
    ICP = "icp"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    TEAM_MEMBER = "team_member"
    METRIC = "metric"
    FUNDING_ASSUMPTION = "funding_assumption"
    RISK = "risk"


class KGEntityStatus(str, PyEnum):
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    SUGGESTED = "suggested"
    PINNED = "pinned"


class KGEntity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_entities"
    
    venture_id: Mapped[str] = mapped_column(
        ForeignKey("ventures.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[KGEntityType] = mapped_column(Enum(KGEntityType), index=True)
    status: Mapped[KGEntityStatus] = mapped_column(
        Enum(KGEntityStatus), default=KGEntityStatus.NEEDS_REVIEW
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    
    venture: Mapped["Venture"] = relationship(back_populates="entities")
    evidence: Mapped[list["KGEvidence"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )


class KGEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kg_evidence"
    
    entity_id: Mapped[str] = mapped_column(
        ForeignKey("kg_entities.id", ondelete="CASCADE"), index=True
    )
    snippet: Mapped[str] = mapped_column(Text)
    document_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(50))
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    entity: Mapped["KGEntity"] = relationship(back_populates="evidence")
```

### 4.5 Document & Chunks (app/models/document.py)

```python
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Integer, ForeignKey, Enum, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin, UUIDMixin


class DocumentType(str, PyEnum):
    PITCH_DECK = "pitch_deck"
    FINANCIAL_MODEL = "financial_model"
    BUSINESS_PLAN = "business_plan"
    PRODUCT_DOC = "product_doc"
    OTHER = "other"


class DocumentStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"
    
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.OTHER)
    mime_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    workspace: Mapped["Workspace"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_chunks"
    
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    venture_id: Mapped[str] = mapped_column(
        ForeignKey("ventures.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(1536), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    document: Mapped["Document"] = relationship(back_populates="chunks")
    
    __table_args__ = (
        Index(
            "ix_chunks_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
```

### 4.6 Chat Models (app/models/chat.py)

```python
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class MessageRole(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_sessions"
    
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    workspace: Mapped["Workspace"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"
    
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    routing_plan: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    artifact_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True
    )
    citations: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
    artifact: Mapped[Optional["Artifact"]] = relationship(back_populates="messages")
```

### 4.7 Artifact Models (app/models/artifact.py)

```python
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class ArtifactType(str, PyEnum):
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


class ArtifactStatus(str, PyEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ARCHIVED = "archived"


class Artifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifacts"
    
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[ArtifactStatus] = mapped_column(
        Enum(ArtifactStatus), default=ArtifactStatus.DRAFT
    )
    owner_agent: Mapped[str] = mapped_column(String(100))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    assumptions: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    created_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    workspace: Mapped["Workspace"] = relationship(back_populates="artifacts")
    versions: Mapped[list["ArtifactVersion"]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan", order_by="ArtifactVersion.version.desc()"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="artifact")


class ArtifactVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifact_versions"
    
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    diff: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    artifact: Mapped["Artifact"] = relationship(back_populates="versions")
```

---

## 5. Core Configuration

### 5.1 Settings (app/config.py)

```python
from functools import lru_cache
from typing import Optional
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "AI VC Co-Pilot"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    
    # Database
    database_url: PostgresDsn
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Redis
    redis_url: RedisDsn
    
    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    
    # AI APIs
    anthropic_api_key: str
    openai_api_key: str
    default_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Storage
    s3_endpoint: Optional[str] = None
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "uploads"
    s3_region: str = "us-east-1"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### 5.2 Database Session (app/dependencies.py)

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import settings

engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 5.3 Main Application (app/main.py)

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api.router import api_router
from app.config import settings
from app.dependencies import engine

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting AI VC Co-Pilot API", version=settings.app_version)
    yield
    logger.info("Shutting down AI VC Co-Pilot API")
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}
```

---

## 6. API Layer

### 6.1 Route Dependencies (app/api/deps.py)

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user


async def get_workspace(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Workspace:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMembership)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    
    return workspace


# Type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
```

### 6.2 Chat Routes (app/api/routes/chat.py)

```python
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, get_workspace
from app.core.agents.registry import agent_registry
from app.core.brain.startup_brain import StartupBrain
from app.core.router.moe_router import MoERouter
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.venture import Venture
from app.schemas.chat import SendMessageRequest, SendMessageResponse, ChatSessionResponse
from app.services.embedding_service import get_embedding_service

router = APIRouter()


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Send a message and get AI response."""
    # Get workspace and venture
    workspace = await get_workspace(request.workspace_id, db, current_user)
    
    result = await db.execute(select(Venture).where(Venture.workspace_id == workspace.id))
    venture = result.scalar_one_or_none()
    
    if not venture:
        raise HTTPException(400, "No venture configured")
    
    # Get or create session
    if request.session_id:
        sess_result = await db.execute(
            select(ChatSession).where(ChatSession.id == request.session_id)
        )
        session = sess_result.scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Session not found")
    else:
        session = ChatSession(
            id=str(uuid4()),
            workspace_id=workspace.id,
            title=request.content[:50],
        )
        db.add(session)
        await db.flush()
    
    # Save user message
    user_msg = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.USER,
        content=request.content,
        user_id=current_user.id,
    )
    db.add(user_msg)
    
    # Initialize brain and router
    brain = StartupBrain(venture.id, db, get_embedding_service())
    moe = MoERouter(venture.stage)
    
    # Route request
    if request.override_agent:
        plan = moe.create_override_plan(request.override_agent)
    else:
        plan = await moe.route(request.content, {"active_artifact": None})
    
    # Get agent and execute
    agent = agent_registry.get(plan.selected_agent)
    if not agent:
        raise HTTPException(500, f"Agent not found: {plan.selected_agent}")
    
    response = await agent.execute(
        prompt=request.content,
        brain=brain,
        routing_plan=plan,
        session_id=session.id,
        user_id=current_user.id,
    )
    
    # Save assistant message
    assistant_msg = ChatMessage(
        id=str(uuid4()),
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=response.content,
        routing_plan=plan.model_dump(),
        agent_id=plan.selected_agent,
        citations=response.citations,
    )
    db.add(assistant_msg)
    await db.commit()
    
    return SendMessageResponse(
        session_id=session.id,
        user_message=user_msg,
        assistant_message=assistant_msg,
        routing_plan=plan,
        proposed_updates=response.proposed_updates,
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(workspace_id: str, db: DbSession, current_user: CurrentUser, limit: int = 20):
    workspace = await get_workspace(workspace_id, db, current_user)
    
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.workspace_id == workspace.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str, db: DbSession, current_user: CurrentUser):
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Verify access
    await get_workspace(session.workspace_id, db, current_user)
    return session
```

---

## 7. Startup Brain Implementation

### 7.1 Main Interface (app/core/brain/startup_brain.py)

```python
from typing import Optional, Any
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain.rag.retriever import RAGRetriever
from app.core.brain.kg.knowledge_graph import KnowledgeGraph
from app.core.brain.events.event_store import EventStore
from app.models.venture import Venture
from app.models.kg_entity import KGEntity, KGEntityType


class StartupBrain:
    """Unified interface to RAG + Knowledge Graph with event sourcing."""
    
    def __init__(self, venture_id: str, session: AsyncSession, embedder):
        self.venture_id = venture_id
        self.session = session
        self.rag = RAGRetriever(venture_id, session, embedder)
        self.kg = KnowledgeGraph(venture_id, session)
        self.events = EventStore(venture_id, session)
    
    async def retrieve(
        self,
        query: str,
        max_chunks: int = 10,
        entity_types: Optional[list[KGEntityType]] = None,
        include_relations: bool = True,
    ) -> dict:
        """Unified retrieval combining RAG and KG."""
        chunks_task = self.rag.search(query, limit=max_chunks)
        entities_task = self.kg.search_entities(query, types=entity_types)
        
        chunks, entities = await asyncio.gather(chunks_task, entities_task)
        
        citations = [
            {
                "chunk_id": c.id,
                "document_id": c.document_id,
                "snippet": c.content[:200],
                "score": c.final_score,
            }
            for c in chunks
        ]
        
        if include_relations and entities:
            entity_ids = [e.id for e in entities]
            relations = await self.kg.get_relations(entity_ids)
            for entity in entities:
                entity.relations = [
                    r for r in relations
                    if r.from_entity_id == entity.id or r.to_entity_id == entity.id
                ]
        
        return {"chunks": chunks, "entities": entities, "citations": citations}
    
    async def get_snapshot(self, entity_types: Optional[list[KGEntityType]] = None) -> dict:
        """Get current venture state for agent context."""
        result = await self.session.execute(
            select(Venture).where(Venture.id == self.venture_id)
        )
        venture = result.scalar_one()
        
        entities = await self.kg.get_entities_by_type(entity_types)
        
        entities_by_type = {}
        for entity in entities:
            key = entity.type.value
            if key not in entities_by_type:
                entities_by_type[key] = []
            entities_by_type[key].append(entity)
        
        return {"venture": venture, "entities": entities_by_type, "metrics": None}
```

### 7.2 RAG Retriever (app/core/brain/rag/retriever.py)

```python
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ChunkWithScore:
    id: str
    content: str
    document_id: str
    similarity: float
    freshness_weight: float
    final_score: float
    metadata: Optional[dict] = None


class RAGRetriever:
    """RAG retrieval with freshness-weighted scoring."""
    
    FRESHNESS_HALF_LIFE_DAYS = 70
    
    def __init__(self, venture_id: str, session: AsyncSession, embedder):
        self.venture_id = venture_id
        self.session = session
        self.embedder = embedder
    
    async def search(self, query: str, limit: int = 10) -> list[ChunkWithScore]:
        """Search with combined relevance and freshness scoring."""
        query_embedding = await self.embedder.embed(query)
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        sql = text("""
            SELECT 
                dc.id,
                dc.content,
                dc.document_id,
                dc.metadata,
                1 - (dc.embedding <=> :embedding::vector) AS similarity,
                EXP(-0.693 * EXTRACT(EPOCH FROM (NOW() - d.created_at)) / 86400 / :half_life) AS freshness_weight,
                (1 - (dc.embedding <=> :embedding::vector)) * 
                EXP(-0.693 * EXTRACT(EPOCH FROM (NOW() - d.created_at)) / 86400 / :half_life) AS final_score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.venture_id = :venture_id AND dc.embedding IS NOT NULL
            ORDER BY final_score DESC
            LIMIT :limit
        """)
        
        result = await self.session.execute(sql, {
            "embedding": embedding_str,
            "venture_id": self.venture_id,
            "half_life": self.FRESHNESS_HALF_LIFE_DAYS,
            "limit": limit,
        })
        
        return [
            ChunkWithScore(
                id=row.id,
                content=row.content,
                document_id=row.document_id,
                similarity=row.similarity,
                freshness_weight=row.freshness_weight,
                final_score=row.final_score,
                metadata=row.metadata,
            )
            for row in result.fetchall()
        ]
    
    async def index_document(self, document_id: str, content: str) -> int:
        """Index a document by chunking and embedding."""
        chunks = self._chunk_text(content)
        texts = [c["text"] for c in chunks]
        embeddings = await self.embedder.embed_batch(texts)
        
        from app.models.document import Document, DocumentChunk
        from app.models.venture import Venture
        from uuid import uuid4
        
        doc_result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one()
        
        venture_result = await self.session.execute(
            select(Venture).where(Venture.workspace_id == document.workspace_id)
        )
        venture = venture_result.scalar_one()
        
        chunk_objects = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_obj = DocumentChunk(
                id=str(uuid4()),
                document_id=document_id,
                venture_id=venture.id,
                content=chunk["text"],
                embedding=embedding,
                chunk_index=idx,
                metadata=chunk.get("metadata"),
            )
            chunk_objects.append(chunk_obj)
        
        self.session.add_all(chunk_objects)
        return len(chunk_objects)
    
    def _chunk_text(self, text: str, target_size: int = 512, overlap: int = 64) -> list[dict]:
        """Semantic chunking with overlap."""
        char_target = target_size * 4
        char_overlap = overlap * 4
        
        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) > char_target and current_chunk:
                chunks.append({"text": current_chunk.strip(), "metadata": {"start_char": chunk_start}})
                overlap_start = max(0, len(current_chunk) - char_overlap)
                current_chunk = current_chunk[overlap_start:] + "\n\n" + para
                chunk_start += overlap_start
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
        
        if current_chunk.strip():
            chunks.append({"text": current_chunk.strip(), "metadata": {"start_char": chunk_start}})
        
        return chunks
```

### 7.3 Knowledge Graph (app/core/brain/kg/knowledge_graph.py)

```python
from typing import Optional, Any
from uuid import uuid4
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.kg_entity import KGEntity, KGEntityType, KGEntityStatus, KGRelation, KGEvidence


class KnowledgeGraph:
    """Knowledge Graph operations."""
    
    def __init__(self, venture_id: str, session: AsyncSession):
        self.venture_id = venture_id
        self.session = session
    
    async def create_entity(
        self,
        type: KGEntityType,
        data: dict[str, Any],
        confidence: float = 0.5,
        status: Optional[KGEntityStatus] = None,
    ) -> KGEntity:
        if status is None:
            if confidence >= 0.85:
                status = KGEntityStatus.CONFIRMED
            elif confidence >= 0.6:
                status = KGEntityStatus.NEEDS_REVIEW
            else:
                status = KGEntityStatus.SUGGESTED
        
        entity = KGEntity(
            id=str(uuid4()),
            venture_id=self.venture_id,
            type=type,
            data=data,
            confidence=confidence,
            status=status,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def get_entity(self, entity_id: str) -> Optional[KGEntity]:
        result = await self.session.execute(
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.id == entity_id)
        )
        return result.scalar_one_or_none()
    
    async def update_entity(self, entity_id: str, updates: dict[str, Any]) -> KGEntity:
        entity = await self.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")
        entity.data = {**entity.data, **updates}
        return entity
    
    async def search_entities(
        self, query: str, types: Optional[list[KGEntityType]] = None
    ) -> list[KGEntity]:
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(
                KGEntity.venture_id == self.venture_id,
                KGEntity.status != KGEntityStatus.SUGGESTED,
            )
        )
        if types:
            stmt = stmt.where(KGEntity.type.in_(types))
        
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        
        keywords = query.lower().split()
        return [e for e in entities if any(kw in str(e.data).lower() for kw in keywords)]
    
    async def get_entities_by_type(
        self, types: Optional[list[KGEntityType]] = None
    ) -> list[KGEntity]:
        stmt = (
            select(KGEntity)
            .options(selectinload(KGEntity.evidence))
            .where(KGEntity.venture_id == self.venture_id)
        )
        if types:
            stmt = stmt.where(KGEntity.type.in_(types))
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_relations(self, entity_ids: list[str]) -> list[KGRelation]:
        result = await self.session.execute(
            select(KGRelation).where(
                or_(
                    KGRelation.from_entity_id.in_(entity_ids),
                    KGRelation.to_entity_id.in_(entity_ids),
                )
            )
        )
        return list(result.scalars().all())
```

---

## 8. MoE Router Implementation

### 8.1 Router (app/core/router/moe_router.py)

```python
import re
import time
from typing import Optional
from app.core.router.intent_classifier import IntentClassifier
from app.core.router.types import IntentCategory, ModelProfile, RoutingPlan
from app.models.venture import VentureStage


class MoERouter:
    """Mixture-of-Experts router for directing requests to agents."""
    
    INTENT_TO_AGENT = {
        IntentCategory.MARKET_RESEARCH: "market-oracle",
        IntentCategory.COMPETITOR_ANALYSIS: "competitive-intelligence",
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
    
    STAGE_OVERRIDES = {
        VentureStage.IDEATION: {IntentCategory.VALUATION: "venture-architect"},
        VentureStage.PRE_SEED: {IntentCategory.VALUATION: "lean-modeler"},
    }
    
    AGENT_ALIASES = {
        "venture": "venture-architect",
        "market": "market-oracle",
        "story": "storyteller",
        "deck": "deck-architect",
        "valuation": "valuation-strategist",
        "qa": "qa-simulator",
        "dataroom": "dataroom-concierge",
        "kpi": "kpi-dashboard",
        "icp": "icp-profiler",
        "risk": "pre-mortem-critic",
    }
    
    def __init__(self, venture_stage: VentureStage):
        self.stage = venture_stage
        self.classifier = IntentClassifier()
    
    async def route(self, prompt: str, context: dict) -> RoutingPlan:
        start = time.perf_counter()
        
        # Check explicit @mention
        explicit = self._extract_explicit_agent(prompt)
        if explicit:
            return self._build_plan(explicit, "explicit", 1.0, start)
        
        # Check artifact continuation
        if context.get("active_artifact"):
            return self._build_plan(
                context["active_artifact"].owner_agent, "artifact", 0.95, start
            )
        
        # Classify intent
        intent = await self.classifier.classify(prompt)
        agent = self._select_agent(intent.category)
        
        return RoutingPlan(
            selected_agent=agent,
            model_profile=ModelProfile.DEFAULT,
            tools=self._get_tools(intent.category),
            artifact_needed=self._needs_artifact(intent.category, prompt),
            fallback_agent="venture-architect",
            confidence=intent.confidence,
            reasoning=intent.reasoning,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
    
    def create_override_plan(self, agent_id: str) -> RoutingPlan:
        return RoutingPlan(
            selected_agent=agent_id,
            model_profile=ModelProfile.DEFAULT,
            tools=["rag", "kg_query"],
            artifact_needed=False,
            fallback_agent="venture-architect",
            confidence=1.0,
            reasoning="User override",
            latency_ms=0,
        )
    
    def _extract_explicit_agent(self, prompt: str) -> Optional[str]:
        match = re.search(r"@([\w-]+)", prompt, re.I)
        if match:
            alias = match.group(1).lower()
            return self.AGENT_ALIASES.get(alias)
        return None
    
    def _select_agent(self, intent: IntentCategory) -> str:
        overrides = self.STAGE_OVERRIDES.get(self.stage, {})
        if intent in overrides:
            return overrides[intent]
        return self.INTENT_TO_AGENT.get(intent, "venture-architect")
    
    def _get_tools(self, intent: IntentCategory) -> list[str]:
        base = ["rag", "kg_query"]
        if intent in {IntentCategory.VALUATION, IntentCategory.FINANCIAL}:
            base.extend(["calculator", "artifact_create"])
        return base
    
    def _needs_artifact(self, intent: IntentCategory, prompt: str) -> bool:
        if intent in {IntentCategory.DECK, IntentCategory.VALUATION}:
            return True
        keywords = ["create", "generate", "build", "make", "draft"]
        return any(kw in prompt.lower() for kw in keywords)
    
    def _build_plan(self, agent: str, source: str, conf: float, start: float) -> RoutingPlan:
        return RoutingPlan(
            selected_agent=agent,
            model_profile=ModelProfile.DEFAULT,
            tools=["rag", "kg_query"],
            artifact_needed=False,
            fallback_agent="venture-architect",
            confidence=conf,
            reasoning=f"Routed via {source}",
            latency_ms=(time.perf_counter() - start) * 1000,
        )
```

### 8.2 Intent Classifier (app/core/router/intent_classifier.py)

```python
from dataclasses import dataclass
from app.core.router.types import IntentCategory


@dataclass
class ClassificationResult:
    category: IntentCategory
    confidence: float
    reasoning: str


class IntentClassifier:
    """Keyword-based intent classifier."""
    
    PATTERNS = {
        IntentCategory.MARKET_RESEARCH: [
            (["market", "size", "tam", "sam", "som"], 1.0),
            (["industry", "trends", "growth"], 0.8),
        ],
        IntentCategory.COMPETITOR_ANALYSIS: [
            (["competitor", "competition", "competitive"], 1.0),
            (["vs", "compare", "alternative"], 0.9),
        ],
        IntentCategory.NARRATIVE: [
            (["story", "narrative", "pitch", "founding"], 1.0),
            (["mission", "vision"], 0.7),
        ],
        IntentCategory.DECK: [(["deck", "slides", "presentation"], 1.0)],
        IntentCategory.VALUATION: [
            (["valuation", "worth", "value"], 1.0),
            (["raise", "funding", "round"], 0.8),
        ],
        IntentCategory.FINANCIAL: [
            (["runway", "burn", "cash"], 1.0),
            (["model", "forecast", "projection"], 0.8),
        ],
        IntentCategory.METRICS: [
            (["kpi", "metric", "dashboard"], 1.0),
            (["mrr", "arr", "churn"], 0.9),
        ],
        IntentCategory.QA_PREP: [(["question", "q&a", "objection"], 1.0)],
        IntentCategory.DATAROOM: [(["dataroom", "diligence", "documents"], 1.0)],
        IntentCategory.ICP: [(["customer", "icp", "persona"], 1.0)],
        IntentCategory.RISK: [(["risk", "fail", "threat"], 1.0)],
    }
    
    async def classify(self, prompt: str) -> ClassificationResult:
        lower = prompt.lower()
        scores = {}
        
        for cat, patterns in self.PATTERNS.items():
            score = 0.0
            for keywords, weight in patterns:
                matches = sum(1 for kw in keywords if kw in lower)
                if matches:
                    score += (matches / len(keywords)) * weight
            scores[cat] = score
        
        if not scores or max(scores.values()) == 0:
            return ClassificationResult(IntentCategory.GENERAL, 0.3, "No matches")
        
        best = max(scores, key=scores.get)
        conf = min(scores[best] / 1.5, 1.0)
        
        if conf < 0.3:
            return ClassificationResult(IntentCategory.GENERAL, conf, f"Low: {best.value}")
        
        return ClassificationResult(best, conf, f"Matched {best.value}")
```

### 8.3 Types (app/core/router/types.py)

```python
from enum import Enum
from pydantic import BaseModel


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
    confidence: float
    reasoning: str
    latency_ms: float
```

---

## 9. Agent System

### 9.1 Base Agent (app/core/agents/base.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, Any
import re
import anthropic
from pydantic import BaseModel
from app.config import settings
from app.core.brain.startup_brain import StartupBrain
from app.core.router.types import RoutingPlan
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str
    supported_stages: list[VentureStage]
    required_context: list[KGEntityType]
    can_create_artifacts: list[str]


class AgentResponse(BaseModel):
    content: str
    artifact_id: Optional[str] = None
    citations: list[dict[str, Any]] = []
    proposed_updates: list[dict[str, Any]] = []


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    @property
    def id(self) -> str:
        return self.config.id
    
    @abstractmethod
    async def execute(
        self,
        prompt: str,
        brain: StartupBrain,
        routing_plan: RoutingPlan,
        session_id: str,
        user_id: str,
    ) -> AgentResponse:
        pass
    
    @abstractmethod
    def get_agent_specific_instructions(self) -> str:
        pass
    
    async def _get_context(self, brain: StartupBrain, prompt: str) -> dict:
        result = await brain.retrieve(
            query=prompt,
            max_chunks=10,
            entity_types=self.config.required_context,
        )
        return result
    
    def _build_system_prompt(self, snapshot: dict, context: dict) -> str:
        venture = snapshot["venture"]
        
        entities_text = ""
        for entity in context.get("entities", []):
            entities_text += f"\n### {entity.type.value}\n{entity.data}\n"
        
        chunks_text = ""
        for chunk in context.get("chunks", [])[:5]:
            chunks_text += f"\n[Score: {chunk.final_score:.2f}]\n{chunk.content[:300]}...\n"
        
        return f"""You are {self.config.name}, specialized in {self.config.description}.

## Venture Context
- Name: {venture.name}
- Stage: {venture.stage.value}
- One-liner: {venture.one_liner or 'Not defined'}

## Knowledge Graph Entities
{entities_text}

## Relevant Documents
{chunks_text}

## Your Role
{self.get_agent_specific_instructions()}

## Guidelines
1. Ground responses in venture context
2. Cite sources with [Source: doc_id]
3. State clearly when information is missing
4. For new facts, use: <!-- PROPOSED_UPDATE: {{"entity_type": "...", "new_value": ...}} -->
5. Be professional and consultant-grade
"""
    
    async def _call_claude(self, system: str, prompt: str, max_tokens: int = 4096) -> str:
        response = await self.client.messages.create(
            model=settings.default_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    
    def _extract_citations(self, response: str, context: dict) -> list[dict]:
        citations = []
        for match in re.finditer(r'\[Source: ([^\]]+)\]', response):
            ref = match.group(1)
            for chunk in context.get("chunks", []):
                if ref in chunk.document_id:
                    citations.append({
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "snippet": chunk.content[:200],
                    })
                    break
        return citations
    
    def _extract_proposed_updates(self, response: str) -> list[dict]:
        updates = []
        import json
        for match in re.finditer(r'<!-- PROPOSED_UPDATE: ({.*?}) -->', response, re.S):
            try:
                updates.append(json.loads(match.group(1)))
            except:
                pass
        return updates
```

### 9.2 Venture Architect Agent (app/core/agents/venture_architect.py)

```python
from app.core.agents.base import BaseAgent, AgentConfig, AgentResponse
from app.core.brain.startup_brain import StartupBrain
from app.core.router.types import RoutingPlan
from app.models.kg_entity import KGEntityType
from app.models.venture import VentureStage


class VentureArchitectAgent(BaseAgent):
    """Agent for foundational venture design and Lean Canvas creation."""
    
    def __init__(self):
        super().__init__(AgentConfig(
            id="venture-architect",
            name="Venture Architect",
            description="foundational venture design, Lean Canvas, JTBD, experiment planning",
            supported_stages=[VentureStage.IDEATION, VentureStage.PRE_SEED, VentureStage.SEED],
            required_context=[
                KGEntityType.VENTURE, KGEntityType.MARKET, KGEntityType.ICP,
                KGEntityType.PRODUCT, KGEntityType.COMPETITOR,
            ],
            can_create_artifacts=["lean_canvas", "research_brief"],
        ))
    
    def get_agent_specific_instructions(self) -> str:
        return """You help founders build strong venture foundations:

1. **Lean Canvas**: Identify and validate 9 key building blocks
2. **Jobs-to-be-Done**: Uncover customer progress needs
3. **Experiment Design**: Create testable hypotheses

Your approach:
- Ask probing questions to uncover assumptions
- Challenge weak hypotheses constructively
- Prioritize highest-risk assumptions
- Ground recommendations in specific context

Mark assumptions with [ASSUMPTION] and gaps with [NEEDS VALIDATION]."""
    
    async def execute(
        self,
        prompt: str,
        brain: StartupBrain,
        routing_plan: RoutingPlan,
        session_id: str,
        user_id: str,
    ) -> AgentResponse:
        snapshot = await brain.get_snapshot(self.config.required_context)
        context = await self._get_context(brain, prompt)
        
        system = self._build_system_prompt(snapshot, context)
        response = await self._call_claude(system, prompt)
        
        return AgentResponse(
            content=response,
            citations=self._extract_citations(response, context),
            proposed_updates=self._extract_proposed_updates(response),
        )
```

### 9.3 Agent Registry (app/core/agents/registry.py)

```python
from typing import Optional
from app.core.agents.base import BaseAgent
from app.core.agents.venture_architect import VentureArchitectAgent


class AgentRegistry:
    """Registry for all available agents."""
    
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        agents = [
            VentureArchitectAgent(),
            # Add other agents here as implemented
        ]
        for agent in agents:
            self.register(agent)
    
    def register(self, agent: BaseAgent):
        self._agents[agent.id] = agent
    
    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)
    
    def all(self) -> list[BaseAgent]:
        return list(self._agents.values())


agent_registry = AgentRegistry()
```

---

## 10. Services

### 10.1 Embedding Service (app/services/embedding_service.py)

```python
from functools import lru_cache
import openai
from app.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
    
    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.model, input=text, dimensions=self.dimensions
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=self.model, input=texts, dimensions=self.dimensions
        )
        return [item.embedding for item in response.data]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
```

---

## 11. Background Workers

### 11.1 Celery App (app/workers/celery_app.py)

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_vc_copilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=300,
)

celery_app.autodiscover_tasks(["app.workers.document_tasks"])
```

### 11.2 Document Tasks (app/workers/document_tasks.py)

```python
import asyncio
from app.workers.celery_app import celery_app
from app.dependencies import get_db_context
from app.models.document import Document, DocumentStatus
from app.services.embedding_service import get_embedding_service
from sqlalchemy import select


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    return asyncio.get_event_loop().run_until_complete(
        _process_document_async(document_id)
    )


async def _process_document_async(document_id: str):
    async with get_db_context() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            return {"status": "error", "message": "Document not found"}
        
        try:
            document.status = DocumentStatus.PROCESSING
            await db.commit()
            
            # Process document (parse, chunk, embed)
            # ... implementation details ...
            
            document.status = DocumentStatus.INDEXED
            await db.commit()
            
            return {"status": "success"}
            
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await db.commit()
            raise
```

---

## 12. Deployment Configuration

### 12.1 Docker Compose (docker-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_vc_copilot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 5

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/ai_vc_copilot
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: minio
      S3_SECRET_KEY: minio123
      ANTHROPIC_API_KEY: \${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: \${OPENAI_API_KEY}
      SECRET_KEY: \${SECRET_KEY:-supersecret}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/ai_vc_copilot
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      ANTHROPIC_API_KEY: \${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: \${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    command: celery -A app.workers.celery_app worker --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 12.2 Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:\$PATH"

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .
RUN poetry install --no-interaction --no-ansi

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 12.3 Environment Template (.env.example)

```bash
# Application
DEBUG=false
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_vc_copilot

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI APIs
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_BUCKET=uploads
S3_REGION=us-east-1

# CORS
CORS_ORIGINS=http://localhost:3000
```

---

## 13. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)

**Deliverables:**
- [ ] Database schema deployed with Alembic migrations
- [ ] Basic FastAPI application structure
- [ ] User auth (JWT-based)
- [ ] Workspace CRUD operations
- [ ] Document upload to S3/MinIO
- [ ] Basic RAG indexing (chunking + embedding)

**Key Files:**
```
backend/app/models/*.py
backend/alembic/versions/001_initial_schema.py
backend/app/api/routes/auth.py
backend/app/api/routes/workspaces.py
backend/app/api/routes/documents.py
backend/app/core/brain/rag/retriever.py
```

### Phase 2: Startup Brain (Weeks 4-6)

**Deliverables:**
- [ ] Knowledge Graph CRUD operations
- [ ] Entity extraction pipeline (using Claude)
- [ ] Event sourcing for KG changes
- [ ] Conflict detection
- [ ] Venture Profile API endpoint

**Key Files:**
```
backend/app/core/brain/kg/knowledge_graph.py
backend/app/core/brain/kg/entity_extractor.py
backend/app/core/brain/events/event_store.py
backend/app/api/routes/brain.py
```

### Phase 3: MoE Router + Core Agents (Weeks 7-10)

**Deliverables:**
- [ ] Intent classifier with >80% accuracy
- [ ] Router latency <200ms P95
- [ ] 6 core agents implemented
- [ ] Chat API with routing
- [ ] Agent override mechanism

**Key Files:**
```
backend/app/core/router/moe_router.py
backend/app/core/router/intent_classifier.py
backend/app/core/agents/base.py
backend/app/core/agents/venture_architect.py
backend/app/api/routes/chat.py
```

### Phase 4: Artifact System (Weeks 11-13)

**Deliverables:**
- [ ] Artifact CRUD with versioning
- [ ] Diff engine for version comparison
- [ ] Artifact workspace API
- [ ] Agent chat in artifact context
- [ ] Export (Markdown, PDF)

**Key Files:**
```
backend/app/core/artifacts/manager.py
backend/app/core/artifacts/diff_engine.py
backend/app/api/routes/artifacts.py
backend/app/workers/export_tasks.py
```

### Phase 5: Frontend + Polish (Weeks 14-16)

**Deliverables:**
- [ ] Next.js app with auth
- [ ] Chat interface
- [ ] Venture profile view
- [ ] Artifact workspace UI
- [ ] Onboarding flow
- [ ] Full integration tests passing

---

## 14. Quick Reference

### Common Commands

```bash
# Backend
cd backend
poetry install                    # Install dependencies
poetry run alembic upgrade head   # Run migrations
poetry run uvicorn app.main:app --reload  # Start dev server
poetry run celery -A app.workers.celery_app worker --loglevel=info
poetry run pytest                 # Run tests
poetry run ruff check .           # Lint
poetry run mypy .                 # Type check

# Docker
docker-compose up -d              # Start all services
docker-compose logs -f backend    # View logs
docker-compose exec backend bash  # Shell access
```

### API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Login, get JWT token |
| `/api/v1/chat/send` | POST | Send message, get AI response |
| `/api/v1/chat/sessions` | GET | List chat sessions |
| `/api/v1/chat/sessions/{id}` | GET | Get session with messages |
| `/api/v1/brain/profile/{workspace_id}` | GET | Get venture profile |
| `/api/v1/brain/entities` | POST | Create KG entity |
| `/api/v1/brain/entities/{id}` | PATCH | Update KG entity |
| `/api/v1/brain/search` | POST | Search brain |
| `/api/v1/artifacts` | GET/POST | List/create artifacts |
| `/api/v1/artifacts/{id}` | GET/PATCH | Get/update artifact |
| `/api/v1/artifacts/{id}/chat` | POST | Artifact chat |
| `/api/v1/documents/upload` | POST | Upload document |
| `/api/v1/documents` | GET | List documents |

### Makefile

```makefile
.PHONY: install dev test lint migrate

install:
	cd backend && poetry install

dev:
	docker-compose up -d postgres redis minio
	cd backend && poetry run uvicorn app.main:app --reload

test:
	cd backend && poetry run pytest

lint:
	cd backend && poetry run ruff check .
	cd backend && poetry run mypy .

migrate:
	cd backend && poetry run alembic upgrade head

worker:
	cd backend && poetry run celery -A app.workers.celery_app worker --loglevel=info
```

---

*End of Engineering Specification*
