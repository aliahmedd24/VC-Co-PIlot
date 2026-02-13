# CLAUDE.md — AI VC Co-Pilot Project Rules

> This file governs all Claude Code sessions on this project.
> Read it in full before writing any code. Re-read it if the session is long.

---

## 1. Session Logging (MANDATORY)

You **must** maintain a `log.md` file at the project root. Update it at the **end of every session** — no exceptions.

### Log Format

Append a new entry using this exact structure:

```markdown
---

## Session — YYYY-MM-DD HH:MM (UTC)

**Phase:** <1–6>
**Focus:** <one-line summary of what was worked on>
**Branch:** <git branch name, if applicable>

### Completed
- <bullet list of what was finished and is working>

### Changed Files
- `path/to/file.py` — <what changed and why>

### Decisions Made
- <any architectural, design, or tradeoff decisions>

### Blockers / Open Issues
- <anything unfinished, broken, or needing follow-up>

### Next Steps
- <exactly what the next session should pick up>
```

### Log Rules

- **Never delete or overwrite** previous log entries. Always append.
- If `log.md` does not exist, create it with a header: `# AI VC Co-Pilot — Development Log`
- Before starting work, **read the last 3 log entries** to understand current project state.
- If you are resuming a prior session, reference it: "Continuing from session YYYY-MM-DD."
- Keep entries concise — no more than 30 lines per session.

---

## 2. Project Identity

- **Project:** AI VC Co-Pilot Platform
- **Description:** Agentic venture consultancy platform — AI-powered startup advisory with specialized agents, shared knowledge layer (Startup Brain), and intelligent MoE routing.
- **Backend:** Python 3.12 / FastAPI / SQLAlchemy 2.0 (async) / PostgreSQL + pgvector / Redis / Celery
- **Frontend:** Next.js 14 / TypeScript / Tailwind CSS / shadcn/ui / React Query / Zustand
- **LLM:** Anthropic Claude (via `anthropic` SDK) for agents, OpenAI for embeddings only
- **Monorepo structure:** `backend/` and `frontend/` at project root

---

## 3. Phase Awareness

This project is built in 6 phases. Each phase has its own PRD file:

| Phase | File | Scope |
|-------|------|-------|
| 1 | `phase-1-foundation-infrastructure.md` | DB, auth, workspaces, doc upload, RAG indexing |
| 2 | `phase-2-startup-brain.md` | Knowledge Graph, entity extraction, event store, brain search |
| 3 | `phase-3-moe-router-agents.md` | Intent classifier, MoE router, 11 agents, chat API |
| 4 | `phase-4-artifact-system.md` | Versioned artifacts, diff engine, export, artifact chat |
| 5 | `phase-5-frontend-application.md` | Full Next.js frontend |
| 6 | `phase-6-advanced-features.md` | Valuation, scoring, benchmarks, streaming, metrics |

**Rules:**
- **Always check which phase you are working in.** If unsure, ask.
- **Do not build features from a later phase** unless explicitly told to. Phases have dependencies.
- **Read the relevant phase PRD** before writing any code for that phase.
- If a task spans phases (e.g., adding a DB model in Phase 1 that Phase 3 needs), note the forward dependency in the log but implement only what the current phase requires.

---

## 4. Code Standards

### Python (Backend)

- **Python 3.12+** — use modern syntax: `type` statements, `|` unions, f-strings.
- **Async everywhere** — all DB operations use `async/await`. Never use synchronous SQLAlchemy calls.
- **Type hints on every function** — parameters and return types. No `Any` unless truly necessary.
- **Pydantic 2.x** for all request/response schemas. Never return raw dicts from API routes.
- **SQLAlchemy 2.0 style** — use `Mapped[]`, `mapped_column()`, `select()`. No legacy Query API.
- **Imports:** absolute imports only (`from app.models.user import User`), never relative.
- **Linting:** code must pass `ruff check .` and `mypy . --strict` before considering a task done.
- **No print statements.** Use `structlog` for all logging.
- **Error handling:** raise `HTTPException` in routes, never return error dicts. Use specific status codes.
- **Tests:** use `pytest` with `pytest-asyncio`. Every new endpoint gets at least one happy-path and one failure test.

### TypeScript (Frontend)

- **Strict TypeScript** — no `any` types. Define interfaces for all API responses.
- **Functional components only.** No class components.
- **shadcn/ui** for all UI primitives. Don't use raw HTML `<input>`, `<button>`, `<select>`.
- **React Query** for all server state. **Zustand** for client-only state (auth, UI toggles).
- **Tailwind CSS** only — no inline styles, no CSS modules, no styled-components.
- **pnpm** as package manager.
- Code must pass `pnpm lint` and `pnpm build` (no type errors) before done.

### General

- **No console.log / print debugging** left in committed code.
- **No hardcoded secrets, API keys, or credentials.** Use environment variables via `pydantic-settings` (backend) or `.env.local` (frontend).
- **No new dependencies** without justification logged in `log.md` under "Decisions Made."
- **File naming:** snake_case for Python, PascalCase for React components, camelCase for TypeScript utilities.

---

## 5. Architecture Guardrails

### Do

- Keep agents stateless — all state comes from the Startup Brain and DB.
- Use the `BaseAgent` abstract class for all new agents. Do not create ad-hoc agent patterns.
- Route all KG mutations through the `EventStore`. Direct DB writes to `kg_entities` without an event are bugs.
- Use `get_workspace` dependency for workspace-scoped route authorization.
- Use Celery for anything that takes > 2 seconds (doc processing, PDF export, entity extraction).
- Store structured artifact content as JSONB with Pydantic validation — never as raw text blobs.

### Do Not

- **Do not call the LLM from the router.** The MoE router must be deterministic keyword matching (< 200ms).
- **Do not create new database models** without an Alembic migration. Never use `metadata.create_all()` in production code.
- **Do not store files in the local filesystem.** All file storage goes through the S3/MinIO storage service.
- **Do not add frontend routes that bypass auth.** Only `/login`, `/register`, and `/` (landing) are public.
- **Do not put business logic in API route handlers.** Routes are thin — they validate input, call a service/manager, and return the response.
- **Do not use `*` imports.** Always import specific names.
- **Do not create god objects.** If a class exceeds 300 lines, it needs to be decomposed.

---

## 6. Git Practices

- **Branch naming:** `phase-{N}/{short-description}` (e.g., `phase-2/knowledge-graph`)
- **Commit messages:** imperative mood, prefix with phase: `[P2] Add entity extraction pipeline`
- **One logical change per commit.** Don't bundle unrelated changes.
- **Never commit `.env` files, API keys, or `node_modules/`.** Verify `.gitignore` is correct.
- If you create or modify `.gitignore`, log it.

---

## 7. Testing Philosophy

- Tests live in `backend/tests/` (unit and integration) and `frontend/__tests__/`.
- **Every phase's "Definition of Done"** lists required tests. Implement them.
- Mock external services (Claude API, OpenAI API, S3) in unit tests. Use `unittest.mock.AsyncMock`.
- Integration tests can use a real test database (Docker Compose test profile).
- Name tests descriptively: `test_<what>_<condition>_<expected>` (e.g., `test_login_invalid_password_returns_401`).
- Run the full test suite before marking anything as complete.

---

## 8. When You're Stuck

1. **Re-read the relevant phase PRD** — the answer is usually there.
2. **Check `log.md`** — a previous session may have encountered the same issue.
3. **Check the existing codebase** — use `grep` or `find` before creating something that may already exist.
4. **Ask for clarification** rather than guessing. State what you know, what you don't, and what you recommend.
5. **Never silently skip a requirement.** If you can't do something, say so in the log and in your response.

---

## 9. Environment Quick Reference

```bash
# Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
poetry run celery -A app.workers.celery_app worker --loglevel=info
poetry run pytest
poetry run ruff check .
poetry run mypy .

# Frontend
cd frontend
pnpm install
pnpm dev
pnpm lint
pnpm build

# Infrastructure
docker-compose up -d postgres redis minio    # Start data services
docker-compose up -d                         # Start everything
docker-compose logs -f backend               # Tail logs
```

---

## 10. Reminders

- You are building a **professional B2B SaaS platform**, not a prototype. Code quality matters.
- The end users are **startup founders and VCs**. The platform must feel trustworthy and polished.
- When in doubt, **keep it simple.** A working simple solution beats an overengineered broken one.
- **Update `log.md` before ending the session.** This is the single most important rule in this file.
