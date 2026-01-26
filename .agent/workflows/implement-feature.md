---
description: Full feature build—spec → analyze existing code → schemas → test stubs → core logic → service layer → API routes → integration tests → docs
---

# Workflow: Implement Feature

> Systematic approach to building new features from specification to tested code.

---

## Trigger

- User requests a new feature
- Implementing a component from the engineering spec
- Adding new functionality to existing system

---

## Steps

### Step 1: Understand Requirements

```
ACTION: Gather complete requirements before any code

Ask yourself (and user if unclear):
1. What is the feature supposed to do?
2. What are the inputs and outputs?
3. What existing code does this interact with?
4. Are there edge cases to handle?
5. What does "done" look like?

CHECKPOINT: Write a brief spec in log.md

### Feature: [Name]
**Purpose:** [one sentence]
**Inputs:** [list]
**Outputs:** [list]
**Integrates with:** [list existing modules]
**Success criteria:** [how to verify it works]
```

### Step 2: Analyze Existing Code

```
ACTION: Map the integration points

Commands to run:
$ find . -name "*.py" | xargs grep -l "relevant_pattern"
$ cat backend/app/core/[related_module].py

Questions to answer:
1. What existing patterns should I follow?
2. What imports will I need?
3. Are there base classes to inherit from?
4. What's the naming convention?

CHECKPOINT: Document in log.md
- Files that will need modification: [list]
- New files to create: [list]
- Patterns to follow: [description]
```

### Step 3: Design Data Structures First

```
ACTION: Define schemas and models before logic

Create in order:
1. Pydantic schemas (request/response)
2. SQLAlchemy models (if database)
3. TypedDict or dataclass for internal state

Example structure:
backend/app/schemas/[feature].py   # Pydantic schemas
backend/app/models/[feature].py    # SQLAlchemy models

CHECKPOINT: 
- [ ] All fields have type hints
- [ ] Required vs optional is clear
- [ ] Validation rules defined
- [ ] Run: mypy backend/app/schemas/[feature].py
```

### Step 4: Write Test Stubs

```
ACTION: Define tests before implementation

Create test file: tests/unit/test_[feature].py

Write test stubs for:
- Happy path (basic success case)
- Edge cases (empty input, max values)
- Error cases (invalid input, failures)

Example:
```python
import pytest
from app.core.[feature] import FeatureClass

class TestFeature:
    def test_basic_success(self):
        """Feature handles normal input correctly."""
        pytest.skip("Not implemented")
    
    def test_empty_input(self):
        """Feature handles empty input gracefully."""
        pytest.skip("Not implemented")
    
    def test_invalid_input_raises(self):
        """Feature raises ValueError on invalid input."""
        pytest.skip("Not implemented")
```

CHECKPOINT:
- [ ] Test file created
- [ ] All major cases have stubs
- [ ] Run: pytest tests/unit/test_[feature].py (should show skipped)
```

### Step 5: Implement Core Logic

```
ACTION: Build the feature incrementally

Implementation order:
1. Create __init__.py if new package
2. Implement core class/functions
3. Add error handling
4. Add logging

Rules:
- Functions under 50 lines
- Single responsibility per function
- Type hints on all signatures
- Docstrings on public methods

After each logical unit:
$ pytest tests/unit/test_[feature].py -v
$ ruff check backend/app/core/[feature].py

CHECKPOINT: Update test from stub to real assertion
```

### Step 6: Implement Service Layer

```
ACTION: Add external integrations

If feature needs:
- Database access → add repository methods
- External API → add service client
- Background work → add Celery task

Files:
backend/app/services/[feature]_service.py
backend/app/repositories/[feature]_repo.py
backend/app/workers/[feature]_tasks.py

CHECKPOINT:
- [ ] Service is injected via dependency, not imported directly
- [ ] External calls are wrapped in try/except
- [ ] Timeouts configured for external calls
```

### Step 7: Implement API Routes

```
ACTION: Expose feature via HTTP

Create: backend/app/api/routes/[feature].py

Structure:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.[feature] import FeatureRequest, FeatureResponse
from app.core.[feature] import FeatureClass
from app.api.deps import get_current_user, get_db

router = APIRouter(prefix="/[feature]", tags=["[feature]"])

@router.post("/", response_model=FeatureResponse)
async def create_feature(
    request: FeatureRequest,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    # Implementation
```

Register in: backend/app/api/routes/__init__.py
Add to: backend/app/main.py

CHECKPOINT:
- [ ] Route registered and accessible
- [ ] Auth dependency included
- [ ] Request validation working
- [ ] Test: curl -X POST http://localhost:8000/api/v1/[feature]/ -d '{}'
```

### Step 8: Write Integration Tests

```
ACTION: Test full flow with real dependencies

Create: tests/integration/test_[feature]_api.py

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_feature_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/[feature]/",
            json={"field": "value"},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
```

CHECKPOINT:
- [ ] Integration tests pass
- [ ] Tests use fixtures, not hardcoded data
```

### Step 9: Final Verification

```
ACTION: Complete quality checks

Commands:
$ pytest tests/ -v                         # All tests
$ ruff check .                             # Lint
$ mypy . --ignore-missing-imports          # Types
$ pytest tests/ --cov=app --cov-report=term-missing  # Coverage

CHECKPOINT: All must pass
- [ ] All tests green
- [ ] No lint errors
- [ ] No type errors
- [ ] New code has test coverage
```

### Step 10: Update Documentation

```
ACTION: Document the feature

Update:
1. log.md — record completion
2. README.md — if user-facing
3. API docs — FastAPI auto-generates, but add docstrings
4. CLAUDE.md — if new pattern introduced

CHECKPOINT:
- [ ] log.md updated with "Feature complete"
- [ ] Files Modified section filled in
```

---

## Output

By the end of this workflow:

- [ ] Feature fully implemented
- [ ] Unit and integration tests passing
- [ ] Lint and type checks passing
- [ ] Documentation updated
- [ ] log.md reflects completed work

---

## Rollback

If feature is incomplete at session end:

1. Mark incomplete code with `# TODO: INCOMPLETE - [what's left]`
2. Ensure partial code doesn't break tests (skip or comment)
3. Document stopping point in log.md
4. List exact next steps to resume
