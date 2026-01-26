---
description: Quality assurance—automated gates → review checklist (structure, naming, docs, errors, security) → dependency analysis → coverage → performance → final verification
---

# Workflow: Code Review & Quality Assurance

> Systematic approach to reviewing code quality, refactoring, and pre-commit validation.

---

## Trigger

- Before committing changes
- After completing a feature
- Periodic code quality check
- Preparing for code review
- Refactoring request

---

## Steps

### Step 1: Automated Quality Gates

```
ACTION: Run all automated checks first

Commands (all must pass):
$ pytest tests/ -v --tb=short
$ ruff check . --output-format=grouped
$ mypy . --ignore-missing-imports
$ ruff format --check .  # Check formatting

Quick summary command:
$ make lint && make test && echo "✅ All checks pass"

CHECKPOINT: Record results

**Quality Gate Results:**
- Tests: PASS / FAIL (X failures)
- Lint (ruff): PASS / FAIL (X issues)
- Types (mypy): PASS / FAIL (X errors)
- Format: PASS / FAIL

If any fail, fix before proceeding.
```

### Step 2: Review Changed Files

```
ACTION: List and examine all changed files

Commands:
$ git diff --name-only HEAD~1        # vs last commit
$ git diff --name-only main          # vs main branch
$ git diff --stat                    # with line counts

For each changed file, review:
1. Does change match intended purpose?
2. Any unintended modifications?
3. Any debug code left in?

CHECKPOINT: List files for review

**Files to review:**
- [ ] path/file1.py (X lines changed)
- [ ] path/file2.py (X lines changed)
```

### Step 3: Code Quality Checklist

```
ACTION: Review each file against quality criteria

For each file, check:

**Structure:**
- [ ] Functions under 50 lines
- [ ] Classes have single responsibility
- [ ] No deeply nested code (max 3-4 levels)
- [ ] Related code is grouped together

**Naming:**
- [ ] Functions describe what they do (verb_noun)
- [ ] Variables describe what they hold
- [ ] No abbreviations except common ones (id, url, etc.)
- [ ] Consistent with project conventions

**Documentation:**
- [ ] Public functions have docstrings
- [ ] Complex logic has comments explaining WHY
- [ ] No commented-out code
- [ ] No TODO without ticket/issue reference

**Error Handling:**
- [ ] Specific exceptions caught (not bare except)
- [ ] Errors logged with context
- [ ] User-facing errors are clear
- [ ] Failures don't leave system in bad state

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL uses parameterized queries
- [ ] No eval() or exec() with user input

CHECKPOINT: Note any issues found
```

### Step 4: Dependency Analysis

```
ACTION: Check import health

Commands:
# Find circular imports
$ python -c "from app.main import app" 2>&1 | grep -i circular

# Check for unused imports
$ ruff check . --select F401

# Check import organization
$ ruff check . --select I

# Find potentially missing dependencies
$ grep -rh "^from\|^import" --include="*.py" backend/ | sort | uniq -c | sort -rn | head -20

CHECKPOINT:
- [ ] No circular imports
- [ ] No unused imports
- [ ] Imports are organized (stdlib → third-party → local)
```

### Step 5: Test Coverage Review

```
ACTION: Verify test coverage for changed code

Commands:
$ pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

Review coverage report:
$ open htmlcov/index.html  # or view in terminal

For each changed file, verify:
- [ ] Has corresponding test file
- [ ] Key functions are tested
- [ ] Edge cases are covered
- [ ] Error paths are tested

Minimum coverage targets:
- Core business logic: 90%+
- API routes: 80%+
- Utilities: 70%+

CHECKPOINT:
- [ ] Coverage meets targets
- [ ] Critical paths are tested
- [ ] No obvious test gaps
```

### Step 6: Performance Review

```
ACTION: Check for performance issues

Look for:

**Database:**
- N+1 queries (query in a loop)
- Missing indexes for filtered columns
- Large result sets without pagination

**Memory:**
- Loading large files entirely into memory
- Unbounded list growth
- Missing generators for large iterations

**Async:**
- Sequential awaits that could be parallel
- Blocking calls in async functions
- Missing connection pooling

Commands:
# Find potential N+1 patterns
$ grep -rn "for.*in.*:" --include="*.py" -A3 | grep -i "query\|select\|get"

# Find sequential awaits
$ grep -rn "await.*\nawait" --include="*.py"

CHECKPOINT:
- [ ] No obvious N+1 queries
- [ ] No blocking calls in async
- [ ] Large data handled with streaming/pagination
```

### Step 7: API Contract Review

```
ACTION: Verify API consistency

For each API endpoint, check:

**Request:**
- [ ] Pydantic schema validates input
- [ ] Required fields are actually required
- [ ] Types match expected data

**Response:**
- [ ] Response model is defined
- [ ] Error responses are consistent
- [ ] Status codes are appropriate

**Documentation:**
- [ ] OpenAPI schema is accurate
- [ ] Examples are provided
- [ ] Description is clear

Commands:
# View OpenAPI schema
$ curl http://localhost:8000/openapi.json | python -m json.tool

# Test endpoint manually
$ curl -X POST http://localhost:8000/api/v1/endpoint/ \
    -H "Content-Type: application/json" \
    -d '{"field": "value"}'

CHECKPOINT:
- [ ] All endpoints have schemas
- [ ] Responses are consistent
- [ ] Error handling is uniform
```

### Step 8: Security Scan

```
ACTION: Check for security issues

Commands:
# Check for hardcoded secrets
$ grep -rn "password\|secret\|api_key\|token" --include="*.py" | grep -v "\.pyc\|test_\|#"

# Check for dangerous functions
$ grep -rn "eval\|exec\|__import__\|subprocess" --include="*.py"

# Check dependencies for vulnerabilities
$ pip-audit  # or safety check

Review:
- [ ] No credentials in code
- [ ] Environment variables for secrets
- [ ] Input sanitization present
- [ ] No SQL string concatenation

CHECKPOINT:
- [ ] No hardcoded secrets
- [ ] No dangerous patterns
- [ ] Dependencies are secure
```

### Step 9: Fix Issues

```
ACTION: Address all findings

Priority order:
1. Security issues (fix immediately)
2. Failing tests (fix immediately)  
3. Type errors (fix before commit)
4. Lint errors (fix before commit)
5. Performance issues (fix or document)
6. Style issues (fix if quick)

For each fix:
1. Make the change
2. Run relevant tests
3. Verify fix didn't break anything

CHECKPOINT:
- [ ] All critical issues fixed
- [ ] All tests still pass
- [ ] All quality gates pass
```

### Step 10: Final Verification

```
ACTION: Complete pre-commit checklist

Run full suite:
$ pytest tests/ -v
$ ruff check .
$ mypy . --ignore-missing-imports
$ ruff format .

Verify changes:
$ git diff --stat
$ git diff  # Review actual changes

CHECKPOINT: Ready to commit
- [ ] All tests pass
- [ ] All lint checks pass
- [ ] All type checks pass
- [ ] Changes are as intended
- [ ] No debug code left
- [ ] No unintended file changes
```

---

## Output

By the end of this workflow:

- [ ] All quality gates pass
- [ ] Code reviewed against checklist
- [ ] Issues fixed or documented
- [ ] Ready for commit/PR

---

## Common Issues Quick Fixes

```python
# Unused import (F401)
# Just delete the line

# Line too long (E501)
# Break into multiple lines or use parentheses

# Missing type hint
def func(arg: str) -> dict:  # Add types

# Bare except (E722)
except Exception as e:  # Specify exception

# f-string without placeholder (F541)
# Remove f prefix or add {variable}

# Mutable default argument (B006)
def func(items: list = None):  # Use None default
    items = items or []
```

---

## Review Checklist Summary

```
□ Tests pass
□ Lint passes  
□ Types pass
□ Functions < 50 lines
□ Clear naming
□ Docstrings present
□ No hardcoded secrets
□ Errors handled
□ Input validated
□ Tests cover changes
```
