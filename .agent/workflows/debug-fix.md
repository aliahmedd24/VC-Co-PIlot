---
description: Systematic debugging—reproduce → isolate → root cause → write failing test → fix → check similar bugs → verify → document prevention
---

# Workflow: Debug & Fix Issues

> Systematic approach to diagnosing and resolving bugs.

---

## Trigger

- Test failure
- Runtime error reported
- Unexpected behavior
- User-reported bug

---

## Steps

### Step 1: Reproduce the Issue

```
ACTION: Confirm you can see the bug yourself

Never fix what you can't reproduce.

If test failure:
$ pytest tests/path/test_file.py::test_name -v -s

If runtime error:
$ poetry run uvicorn app.main:app --reload
$ curl -X [METHOD] http://localhost:8000/[endpoint] -d '[data]'

If user-reported:
- Get exact steps to reproduce
- Get error message/screenshot
- Get environment details

CHECKPOINT: Document in log.md

### Bug: [Brief description]
**Reproduced:** YES / NO
**Error message:** [exact text]
**Steps to trigger:**
1. Do X
2. Then Y
3. Error occurs

If cannot reproduce, STOP and gather more information.
```

### Step 2: Isolate the Problem

```
ACTION: Narrow down where the bug lives

Strategy A - Binary search with print/logging:
1. Add log at entry point → does it reach here?
2. Add log at midpoint → does it reach here?
3. Continue halving until you find the failing line

Strategy B - Minimal reproduction:
1. Create smallest possible test case
2. Remove dependencies one by one
3. Find minimum code that triggers bug

Strategy C - Stack trace analysis:
1. Read full traceback bottom to top
2. Identify first line in YOUR code (not library)
3. Examine that function

CHECKPOINT: Identify the specific location

**Bug location:** 
- File: [path]
- Function: [name]
- Line: [number]
- Cause hypothesis: [your theory]
```

### Step 3: Understand Root Cause

```
ACTION: Figure out WHY it's broken, not just WHERE

Questions to answer:
1. What is the code trying to do?
2. What is it actually doing?
3. What's the difference?
4. When was this code last changed?

Commands:
$ git log -p --follow -- backend/app/path/file.py | head -100
$ git blame backend/app/path/file.py | grep -A5 -B5 "[line_number]"

Common root causes:
- Type mismatch (expected X, got Y)
- None/null not handled
- Async/await missing
- Race condition
- Off-by-one error
- State mutation side effect
- Missing import
- Wrong variable scope

CHECKPOINT: Document root cause

**Root cause:** [clear explanation]
**Evidence:** [what confirmed this]
```

### Step 4: Write Failing Test First

```
ACTION: Capture the bug as a test BEFORE fixing

Create or update test file:

```python
def test_bug_[issue_description](self):
    """
    Regression test for: [bug description]
    
    Bug: [what was happening]
    Fix: [what should happen]
    """
    # Arrange - set up the buggy condition
    input_data = {"field": "value_that_triggers_bug"}
    
    # Act - do the thing that was broken
    result = function_under_test(input_data)
    
    # Assert - verify correct behavior
    assert result.status == "expected"
```

Run to confirm it fails:
$ pytest tests/path/test_file.py::test_bug_description -v

CHECKPOINT:
- [ ] Test exists that captures the bug
- [ ] Test fails with current code
- [ ] Test will pass when bug is fixed
```

### Step 5: Implement Fix

```
ACTION: Make the minimal change to fix the bug

Rules:
1. Fix ONLY the bug, don't refactor
2. Keep change as small as possible
3. Don't break existing tests

Common fix patterns:
- Add null check: `if value is None: return default`
- Add type conversion: `int(value)` or `str(value)`
- Add await: `result = await async_func()`
- Fix logic: `>=` instead of `>`
- Add exception handling: `try/except SpecificError`

CHECKPOINT: Verify fix
$ pytest tests/path/test_file.py::test_bug_description -v  # New test passes
$ pytest tests/ -v                                          # All tests pass
```

### Step 6: Check for Similar Bugs

```
ACTION: Search for same pattern elsewhere

Commands:
$ grep -rn "similar_pattern" --include="*.py" .
$ grep -rn "same_function_call" --include="*.py" .

Questions:
1. Is this bug repeated elsewhere?
2. Is this a symptom of a larger problem?
3. Should I create a helper function to prevent this?

CHECKPOINT:
- [ ] Searched for similar patterns
- [ ] Fixed or documented other occurrences
- [ ] Considered if refactor needed (but don't do it now)
```

### Step 7: Verify Complete Fix

```
ACTION: Full test suite and quality checks

Commands:
$ pytest tests/ -v                    # All tests pass
$ ruff check .                        # No lint errors
$ mypy . --ignore-missing-imports     # No type errors

Additional verification:
- Manually test the original reproduction steps
- Check that fix doesn't introduce new issues

CHECKPOINT: All green
- [ ] Bug test passes
- [ ] All other tests pass
- [ ] Lint passes
- [ ] Types pass
- [ ] Manual verification done
```

### Step 8: Document the Fix

```
ACTION: Update log and consider prevention

Update log.md:

### Bug Fixed: [Title]
**Symptom:** [what was observed]
**Root cause:** [why it happened]
**Fix:** [what you changed]
**Files modified:** [list]
**Prevention:** [how to avoid in future]

Consider:
- Should this be added to "Common Pitfalls" in CLAUDE.md?
- Should there be a lint rule?
- Should there be a type annotation?
- Should there be documentation?

CHECKPOINT:
- [ ] log.md updated
- [ ] Prevention measures documented
```

---

## Output

By the end of this workflow:

- [ ] Bug is fixed
- [ ] Regression test exists
- [ ] All tests passing
- [ ] Root cause documented
- [ ] Similar bugs checked

---

## If Fix is Not Obvious

If you can't figure out the fix:

1. Document everything you've learned in log.md
2. List hypotheses you've ruled out
3. Identify what information you need
4. Mark with `# FIXME: [description of bug and findings]`
5. Ask user for guidance or more context

Don't make random changes hoping something works.

---

## Debugging Commands Reference

```bash
# Python debugging
poetry run python -m pdb -c continue backend/app/script.py
import pdb; pdb.set_trace()  # Insert breakpoint

# Pytest with debugging
pytest tests/test_file.py -v -s --pdb  # Drop to debugger on failure
pytest tests/test_file.py -v -s -x     # Stop on first failure

# Logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable state: {var}")

# Async debugging
import asyncio
asyncio.get_event_loop().set_debug(True)
```
