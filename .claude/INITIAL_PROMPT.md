---
description: 
---

# Initial Prompt for Claude Code — AI VC Co-Pilot Project

## Session Initialization Protocol

Before beginning any work on this project, you MUST:

1. **Read /.claude/CLAUDE.md** — This file contains all project rules, architecture guardrails, scope boundaries, and mandatory workflows
2. **Read log.md** — Review the latest session entries to understand current project state and recent decisions
3. **Identify Current Phase** — Determine which phase (1–6) you're working on from the last log.md entry
4. **Read Current Phase PRD** — Open the relevant `phase-{N}-*.md` file for detailed specifications

## Session Start Checklist

Execute this checklist at the START of EVERY session:

```markdown
## Session Start: [YYYY-MM-DD HH:MM]

- [ ] Read /.claude/CLAUDE.md completely
- [ ] Reviewed log.md — last 3 sessions
- [ ] Identified current phase: Phase [N]
- [ ] Opened phase-{N}-*.md for reference
- [ ] Reviewed "Definition of Done" for current phase
- [ ] Checked for any blockers from previous session
- [ ] Confirmed working in correct git branch (phase-{N}/*)
```

## Core Directives

### 1. MANDATORY: Reference CLAUDE.md First

**EVERY session starts with:**
```
I have read CLAUDE.md and understand:
- Mandatory log.md update requirements
- Phase containment rules (no building ahead)
- Architecture guardrails (stateless agents, EventStore for KG, deterministic router)
- Code standards (async, typed, linted)
- Testing requirements per phase PRD
- Git conventions (phase-{N}/feature-name branches)

Current Phase: [Phase N — Feature Name]
Current Objective: [Brief description from PRD]
```

### 2. MANDATORY: Update log.md at Session End

Before ending ANY session, you MUST update log.md with the exact format from CLAUDE.md:
- Session timestamp and phase
- Focus (one-line summary)
- Branch name
- Work completed (checklist format)
- Changed files (path + what/why)
- Decisions made
- Blockers / open issues
- Next steps for next session

**Failure to update log.md is a critical violation of project rules.**

### 3. MANDATORY: Phase Containment

Before implementing ANY feature, verify it belongs to the current phase:

| Phase | File | Scope |
|-------|------|-------|
| 1 | `phase-1-foundation-infrastructure.md` | DB, auth, workspaces, doc upload, RAG indexing |
| 2 | `phase-2-startup-brain.md` | Knowledge Graph, entity extraction, event store, brain search |
| 3 | `phase-3-moe-router-agents.md` | Intent classifier, MoE router, 11 agents, chat API |
| 4 | `phase-4-artifact-system.md` | Versioned artifacts, diff engine, export, artifact chat |
| 5 | `phase-5-frontend-application.md` | Full Next.js frontend |
| 6 | `phase-6-advanced-features.md` | Valuation, scoring, benchmarks, streaming, metrics |

```
✅ CORRECT: Building feature listed in current phase PRD
❌ WRONG: Building Phase 4 artifact export while working in Phase 2
```

If a task crosses phase boundaries, implement ONLY what the current phase requires and note the forward dependency in log.md.

### 4. MANDATORY: Architecture Compliance

Before committing ANY code, verify these guardrails:

```python
# Agents are stateless — all state from Brain + DB
✅ CORRECT:
async def execute(self, prompt, brain, routing_plan, session_id, user_id):
    snapshot = await brain.get_snapshot(self.config.required_context)
    context = await self._get_context(brain, prompt)

❌ WRONG:
class MyAgent:
    def __init__(self):
        self.conversation_history = []  # NO — agents don't hold state

# KG mutations go through EventStore
✅ CORRECT:
await self.events.append(KGEventType.ENTITY_CREATED, entity_id, payload)

❌ WRONG:
db.add(kg_entity)  # Direct write without event — this is a bug

# MoE Router is deterministic — no LLM calls
✅ CORRECT:
scores[cat] = sum(1 for kw in keywords if kw in lower) * weight

❌ WRONG:
result = await claude.messages.create(...)  # NEVER in the router

# Business logic in services, not routes
✅ CORRECT:
@router.post("/send")
async def send_message(request, db, current_user):
    response = await agent.execute(prompt, brain, plan, session_id, user_id)

❌ WRONG:
@router.post("/send")
async def send_message(request, db, current_user):
    # 200 lines of business logic directly in the route handler
```

### 5. MANDATORY: Scope Adherence

**IN SCOPE** (proceed with implementation):
- Features explicitly listed in the current phase PRD
- Tests specified in the phase's "Definition of Done"
- Bug fixes for existing code
- Security improvements
- Performance optimizations within the current phase

**OUT OF SCOPE** (require explicit approval before proceeding):
- Features from a later phase
- Architecture changes not in CLAUDE.md
- New third-party dependencies (log justification first)
- Refactoring code outside the current task
- "Nice-to-have" additions not in any PRD

If unsure, **ASK** before implementing.

---

## Workflow by Session Type

### Session Type A: Feature Implementation

```
1. Read feature specification in current phase PRD
2. Check "Definition of Done" criteria for this feature
3. Plan implementation (outline files to create/modify if > 2 files)
4. Get confirmation on plan before writing code
5. Implement in small, testable increments
6. Write tests alongside implementation (not after)
7. Run linters: ruff check . && mypy . (backend) or pnpm lint (frontend)
8. Verify all phase PRD tests pass
9. Update log.md
10. Mark feature as complete in log.md
```

### Session Type B: Bug Fix

```
1. Document the bug in log.md (observed vs expected behavior)
2. Write a failing test that reproduces the bug
3. Implement the fix
4. Verify fix doesn't break architecture guardrails
5. Run full test suite: poetry run pytest (backend) or pnpm test (frontend)
6. Update log.md with root cause and solution
```

### Session Type C: Phase Transition

```
1. Review "Definition of Done" for the completing phase
2. Verify ALL checklist items are complete — no partial phases
3. Run full test suite with coverage report
4. Check linting: ruff check . && mypy . && pnpm lint
5. Create phase summary entry in log.md
6. Document any technical debt carried forward
7. Request explicit phase review/approval before proceeding
8. ONLY proceed to next phase after confirmation
9. Read the new phase's PRD in full before starting work
```

### Session Type D: Setup / Configuration

```
1. Follow Phase 1 PRD specifications exactly
2. Verify docker-compose up starts all services (Postgres, Redis, MinIO)
3. Verify alembic upgrade head applies cleanly
4. Verify /health endpoint returns { "status": "healthy" }
5. Test with seed data if applicable
6. Document any deviations or environment issues in log.md
7. Create troubleshooting notes for future sessions
```

### Session Type E: Continuation ("Continue" command)

```
1. Read last log.md entry's "Next Steps" section
2. Confirm the next task aloud before starting
3. Pick up exactly where the previous session left off
4. Follow Session Type A workflow from step 2 onward
```

---

## Quick Reference Commands

### Before Starting Work
```bash
# Check current project state
git status
git branch --show-current
cat log.md | tail -n 60

# Verify infrastructure running
docker-compose ps
docker-compose logs --tail=20 backend
```

### During Development (Backend)
```bash
# Run tests frequently
cd backend && poetry run pytest -v

# Run specific test file
poetry run pytest tests/unit/test_auth.py -v

# Check test coverage
poetry run pytest --cov=app --cov-report=term-missing

# Linting
poetry run ruff check .
poetry run mypy .

# Database migrations
poetry run alembic current
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "description"
```

### During Development (Frontend)
```bash
# Dev server
cd frontend && pnpm dev

# Linting and type checking
pnpm lint
pnpm build  # catches type errors

# Tests
pnpm test
```

### Before Declaring Work Complete
```bash
# Backend validation
cd backend
poetry run ruff check .
poetry run mypy .
poetry run pytest -v

# Frontend validation
cd frontend
pnpm lint
pnpm build
pnpm test
```

---

## Communication Templates

### Starting a Session
```
Starting session for AI VC Co-Pilot.

✅ Read CLAUDE.md
✅ Reviewed log.md (last session: [date] — [one-line summary])
✅ Current Phase: Phase [N] — [Phase Name]
✅ Objective: [Brief description from PRD or log next steps]

Ready to begin. Next task: [specific task from PRD or log.md]
```

### Ending a Session
```
Session complete. Updating log.md now.

Summary:
- Completed: [list of tasks]
- Tests: [N tests added, passing/failing]
- Linting: [clean / issues]
- Next session: [specific next task]

log.md updated ✅
```

### Requesting Clarification
```
⚠️ Clarification needed:

**Context**: [What I'm working on and which phase]
**Question**: [Specific question]
**Impact**: [Why this blocks progress]
**Options I see**: [If applicable, list alternatives]

Pausing work on this item until clarification received.
```

### Flagging a Scope Issue
```
🚫 Scope check — potential violation:

**Requested**: [What was asked]
**Current Phase**: Phase [N]
**Belongs to**: Phase [M] per PRD
**Recommendation**: [Defer / implement partially / proceed with approval]

Awaiting decision before proceeding.
```

---

## Critical Reminders

### Architecture (Non-Negotiable)
- ✅ Agents are stateless — Brain + DB provide all context
- ✅ All KG mutations go through the EventStore — no direct writes
- ✅ MoE Router is keyword-based — zero LLM calls, < 200ms P95
- ✅ Business logic in services/managers — route handlers stay thin
- ✅ All file storage through S3/MinIO — never local filesystem
- ✅ New DB models require Alembic migrations — no `create_all()`
- ✅ Async everywhere — no synchronous SQLAlchemy calls

### Security (Non-Negotiable)
- ✅ JWT authentication on all protected endpoints
- ✅ Workspace membership verified via `get_workspace` dependency
- ✅ Input validation via Pydantic on all user inputs
- ✅ No secrets in code, commits, or logs — `.env` only
- ✅ Error responses use HTTPException — never expose internals
- ✅ CORS restricted to configured origins

### Code Quality (Enforced)
- ✅ Type hints on every function (params + return)
- ✅ No `Any` types unless absolutely necessary
- ✅ No `print()` statements — use `structlog`
- ✅ No `*` imports — always import specific names
- ✅ No class exceeding 300 lines — decompose
- ✅ Absolute imports only — no relative imports
- ✅ `ruff check .` and `mypy .` clean (backend)
- ✅ `pnpm lint` and `pnpm build` clean (frontend)

### Testing (Per Phase PRD)
- ✅ Every new endpoint gets at least one happy-path and one failure test
- ✅ Mock external services (Claude API, OpenAI, S3) in unit tests
- ✅ Tests named descriptively: `test_<what>_<condition>_<expected>`
- ✅ Full test suite passes before marking any task complete
- ✅ Phase "Definition of Done" tests are required, not optional

---

## Error Recovery Protocol

### Build / Startup Errors
```
1. Document error in log.md with full traceback
2. Check docker-compose.yml and .env configuration
3. Verify alembic migrations are current: alembic current
4. Review recent code changes for breaking imports
5. Consult phase PRD for expected configuration
6. If unresolvable, document in log.md Blockers section
```

### Test Failures
```
1. STOP — do not proceed with new features
2. Document failing tests in log.md
3. Fix failing tests before any new work
4. Verify the fix doesn't break architecture guardrails
5. Re-run full test suite to confirm clean
6. Only then resume feature work
```

### Scope Confusion
```
1. Stop work immediately
2. Re-read CLAUDE.md scope rules (section 3)
3. Check if the feature is in the current phase PRD
4. If not found, check which phase it belongs to
5. Document the question in log.md
6. Ask for clarification — do not guess
```

### Dependency Conflicts
```
1. Document the conflict in log.md
2. Do NOT force-install or override versions
3. Check pyproject.toml / package.json for version constraints
4. Propose a resolution and get approval before applying
5. Log the resolution decision
```

---

## Phase-Specific Notes

**Phase 1 — Foundation**: Everything downstream depends on this. Get the DB schema, auth, and document pipeline right. Verify pgvector extension is enabled and HNSW index exists.

**Phase 2 — Startup Brain**: The shared context layer for ALL agents. Freshness-weighted RAG scoring must use the exact formula from the PRD. EventStore is append-only — test immutability.

**Phase 3 — Router + Agents**: Router latency is the critical metric (< 200ms). Test classification accuracy against the 50-case benchmark in the PRD. All 11 agents must extend BaseAgent — no ad-hoc patterns.

**Phase 4 — Artifacts**: Optimistic locking with `expected_version` prevents concurrent edit corruption. Diff engine uses `deepdiff`. Max 100 versions per artifact — implement pruning.

**Phase 5 — Frontend**: Mobile-first responsive design (375px minimum). All server state through React Query, all client state through Zustand. shadcn/ui for every primitive — no raw HTML inputs.

**Phase 6 — Advanced Features**: SSE streaming must be backward-compatible with JSON responses. Benchmark and success story datasets are static JSON — no external APIs. Rate limiting via `slowapi`.

---

## Final Checklist Before Declaring Any Task Complete

```markdown
- [ ] Feature matches current phase PRD specification
- [ ] Code follows CLAUDE.md architecture guardrails
- [ ] Type hints on all functions (no Any)
- [ ] Tests written and passing (matches PRD "Definition of Done")
- [ ] Linting clean: ruff check . && mypy . (backend) or pnpm lint && pnpm build (frontend)
- [ ] No hardcoded secrets or credentials
- [ ] No print() / console.log() left in code
- [ ] Error handling with proper HTTP status codes
- [ ] New DB models have Alembic migrations
- [ ] No out-of-scope features added
- [ ] No new dependencies without logged justification
- [ ] log.md updated with session details
```

---

## Priority Stack (Tiebreaker)

When you must choose, prioritize in this order:

1. **Correctness** — Code works and passes tests
2. **Compliance** — Code follows CLAUDE.md rules and the active phase PRD
3. **Clarity** — Code is readable, typed, and well-structured
4. **Completeness** — All "Definition of Done" items met
5. **Communication** — I always know what you're doing and why

---

## How to Use This Prompt

**Copy and paste this entire document** into Claude Code at the start of EVERY session. This ensures:

1. Consistent adherence to project rules via CLAUDE.md
2. Proper logging and documentation via log.md
3. Phase discipline — no building ahead, no scope drift
4. Architecture compliance — stateless agents, EventStore, deterministic router
5. Quality standards — typed, linted, tested, documented

**Remember**: This platform serves startup founders and VCs making high-stakes funding decisions. The code must be production-grade, the architecture must be sound, and every session must leave the project in a better, documented state than it started.

---

**Current Project Status**: [To be filled by reviewing log.md]
**Current Phase**: [To be determined from log.md]
**Next Task**: [To be identified from log.md or PRD]

BEGIN SESSION.
