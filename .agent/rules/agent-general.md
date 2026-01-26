---
trigger: always_on
---

# agent.md — AI VC Co-Pilot Development Guide

> Agent instructions for coding sessions. Read this file completely before starting any work.

---

## 1. Session Management

### 1.1 Log File (REQUIRED)

Before writing any code, create or update `log.md` in the project root:

```markdown
# Development Log

## Session: YYYY-MM-DD HH:MM

### Context
- Starting point: [what exists, what's the current state]
- Goal: [what we're trying to accomplish this session]

### Work Completed
- [ ] Task 1
- [ ] Task 2

### Decisions Made
- Decision: [what] | Reason: [why]

### Issues Encountered
- Issue: [description] | Resolution: [how fixed or "OPEN"]

### Next Steps
- [ ] Immediate next task
- [ ] Follow-up items

### Files Modified
- `path/to/file.py` — [brief description of changes]

---
```

**Update `log.md` continuously during the session**, not just at the end. If a session is interrupted, the next session must be able to resume from reading this log.

### 1.2 Session Start Checklist

1. Read `log.md` to understand current state
2. Read `agent-general` (this file)
3. Run `make status` or check git status
4. Run existing tests to verify baseline
5. State your plan before coding

### 1.3 Session End Checklist

1. Run all tests
2. Run linter (`ruff check .`)
3. Run type checker (`mypy .`)
4. Update `log.md` with final status
5. List any incomplete work or known issues

---

## 2. Planning Before Execution

### 2.1 Mandatory Planning Phase

**Never write code immediately.** Always follow this sequence:

```
THINK → PLAN → VERIFY → IMPLEMENT → TEST
```

**THINK**: Understand the full scope of what's being asked. Ask clarifying questions if ambiguous.

**PLAN**: Write out the plan in `log.md` before touching any code:
- What files will be created/modified?
- What's the dependency order?
- What could go wrong?
- How will you verify it works?

**VERIFY**: Before implementing, check:
- Do referenced files/functions actually exist?
- Are imports available?
- Does this conflict with existing code?

**IMPLEMENT**: Write code in small, testable increments.

**TEST**: Run tests after each logical unit of work, not just at the end.

### 2.2 Code Analysis Before Modification

Before modifying any existing file:

1. **Read the entire file** (or relevant sections for large files)
2. **Trace dependencies**: What imports this? What does this import?
3. **Check for tests**: Does `test_<filename>.py` exist?
4. **Understand the pattern**: Match existing code style

```bash
# Useful commands before modifying
grep -r "from app.module import" .  # Find dependents
grep -r "def function_name" .        # Find definitions
pytest tests/test_<module>.py -v    # Run related tests
```

### 2.3 Architecture Decisions

For any non-trivial decision, document in `log.md`:

```markdown
### Decision: [Title]
**Options Considered:**
1. Option A — pros/cons
2. Option B — pros/cons

**Chosen:** Option X
**Rationale:** [why]
```

---

## 3. Implementation Standards

### 3.1 File Creation Order

When building a new feature, create files in this order:

1. **Schema/Models first** — Define data structures
2. **Core logic second** — Business logic, no I/O
3. **Service layer third** — Integrations, external calls
4. **API routes fourth** — HTTP layer
5. **Tests last** — But write test stubs early

### 3.2 Code Quality Gates

Before considering any task "done":

```bash
# All must pass
pytest tests/ -v                    # Tests pass
ruff check .                        # No lint errors
mypy . --ignore-missing-imports     # Type checks pass
```

### 3.3 Error Handling Pattern

```python
# Always use structured errors
class AppError(Exception):
    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}

# Log errors with context
logger.error(f"Operation failed: {error}", extra={"context": context})
```

### 3.4 Import Organization

```python
# Standard library
import asyncio
from datetime import datetime

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Local - absolute imports only
from app.core.config import settings
from app.models.user import User
```

---

## 4. Testing Requirements

### 4.1 Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Pure logic tests (no I/O)
│   ├── test_router.py
│   └── test_brain.py
├── integration/         # Tests with database/services
│   ├── test_api_chat.py
│   └── test_document_processing.py
└── e2e/                 # Full flow tests
    └── test_chat_flow.py
```

### 4.2 Test Before Implement (TBI)

For bug fixes and new features:

1. Write a failing test that demonstrates the requirement
2. Implement until the test passes
3. Refactor if needed

### 4.3 Minimum Coverage

- New code must have tests
- Critical paths (auth, payments, data mutations) require integration tests
- Don't mock what you don't own

---

## 5. Project-Specific Patterns

### 5.1 Agent Implementation

All agents must:
- Inherit from `BaseAgent`
- Implement `execute()` and `stream()` methods
- Use `self.brain.retrieve()` for context
- Return `AgentResponse` with citations

```python
class NewAgent(BaseAgent):
    name = "new_agent"
    description = "What this agent does"
    
    async def execute(self, message: str, context: dict) -> AgentResponse:
        # 1. Get relevant context from brain
        # 2. Build prompt with context
        # 3. Call LLM
        # 4. Extract citations
        # 5. Return structured response
```

### 5.2 Brain Updates

All brain mutations must:
- Go through `brain.propose_updates()` first
- Include confidence scores
- Be logged to EventStore
- Never directly mutate KG without proposal

### 5.3 API Response Format

```python
# All API responses follow this structure
class APIResponse(BaseModel):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    meta: dict = {}
```

---

## 6. Common Pitfalls

### 6.1 Avoid These Mistakes

| Mistake | Correct Approach |
|---------|------------------|
| Importing from `__init__.py` before it exists | Create `__init__.py` files first |
| Using sync code in async context | Always `await` async functions |
| Hardcoding config values | Use `settings.VARIABLE` |
| Catching bare `Exception` | Catch specific exceptions |
| Not closing database sessions | Use `async with` or dependency injection |
| Writing long functions | Split at 50 lines max |

### 6.2 Async/Await Checklist

- All database operations use `AsyncSession`
- All HTTP calls use `httpx.AsyncClient`
- Use `asyncio.gather()` for parallel operations
- Never use `time.sleep()` — use `asyncio.sleep()`

---

## 7. Recovery Procedures

### 7.1 If Tests Were Passing, Now Failing

1. Check `git diff` to see what changed
2. Run single failing test with `-v` for details
3. Check if it's a test isolation issue (run test alone vs. suite)
4. Revert to last known good state if needed

### 7.2 If Stuck on an Error

1. Read the full traceback
2. Check if the error is in your code or a dependency
3. Search codebase for similar patterns that work
4. Document the issue in `log.md` even if unresolved

### 7.3 If Resuming Incomplete Work

1. Read `log.md` completely
2. Find the last "Files Modified" section
3. Run tests to see current state
4. Look for any `# TODO: INCOMPLETE` markers in code

---

## 8. Commands Reference

```bash
# Development
make dev                    # Start dev server + dependencies
make test                   # Run all tests
make lint                   # Run ruff + mypy
make migrate                # Run database migrations

# Database
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
poetry run alembic downgrade -1

# Debugging
poetry run pytest tests/path/test_file.py::test_name -v -s
poetry run python -m pdb script.py

# Search
grep -rn "pattern" --include="*.py" .
```

---

## 9. File Markers

Use these markers for incomplete work:

```python
# TODO: INCOMPLETE - [description of what's left]
# FIXME: [description of known bug]
# HACK: [explanation of temporary workaround]
# NOTE: [important context for future readers]
```

When resuming, search for these:
```bash
grep -rn "TODO: INCOMPLETE\|FIXME" --include="*.py" .
```

---

## 10. Final Checklist

Before ending any session, verify:

- [ ] `log.md` is updated with session summary
- [ ] All tests pass (`make test`)
- [ ] No lint errors (`make lint`)
- [ ] No incomplete code without `TODO: INCOMPLETE` marker
- [ ] Git status is clean or changes are documented

---

*Last updated: 2025-01-24*