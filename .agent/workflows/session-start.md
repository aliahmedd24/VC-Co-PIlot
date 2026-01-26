---
description: Initialize/resume sessions—read log.md, check git status, run health checks, identify incomplete work, state plan before coding
---

# Workflow: Session Start & Resume

> Run this workflow at the beginning of every coding session.

---

## Trigger

- Starting a new coding session
- Resuming after interruption
- Switching to this project from another

---

## Steps

### Step 1: Read Project Context

```
ACTION: Read core documentation files

1. Read log.md if it exists
2. Read PRD.md and use as context for the project
3. Read README.md if it exists

CHECKPOINT: Can you answer these questions?
- What is the current state of the project?
- What was the last completed work?
- Are there any open issues or incomplete tasks?
```

### Step 2: Assess Project State

```
ACTION: Check git and file status

Commands to run:
$ git status
$ git log --oneline -10
$ find . -name "*.py" -newer log.md 2>/dev/null | head -20

CHECKPOINT: Document findings
- Are there uncommitted changes?
- What were the recent commits about?
- Any files modified since last log entry?
```

### Step 3: Run Health Checks

```
ACTION: Verify project is in working state

Commands to run:
$ make test 2>&1 | tail -20
$ ruff check . 2>&1 | head -20
$ mypy . --ignore-missing-imports 2>&1 | head -20

CHECKPOINT: Record results
- Tests passing: YES / NO / PARTIAL (X of Y)
- Lint errors: YES (count) / NO
- Type errors: YES (count) / NO

If any failures, document in log.md before proceeding.
```

### Step 4: Identify Incomplete Work

```
ACTION: Search for incomplete markers

Commands to run:
$ grep -rn "TODO: INCOMPLETE" --include="*.py" .
$ grep -rn "FIXME" --include="*.py" .
$ grep -rn "HACK" --include="*.py" .

CHECKPOINT: List all incomplete items
- File: line: description
```

### Step 5: Initialize or Update Log

```
ACTION: Create/update log.md

If log.md doesn't exist, create it with this template:

---
# Development Log

## Session: [CURRENT DATE TIME]

### Context
- Starting point: [describe current state from steps 1-4]
- Goal: [what user wants to accomplish]

### Work Plan
1. [ ] First task
2. [ ] Second task

### Work Completed
(to be filled during session)

### Issues Encountered
(to be filled during session)

### Files Modified
(to be filled during session)

---

If log.md exists, append a new session entry.
```

### Step 6: Confirm Understanding

```
ACTION: State your plan to the user

Before writing any code, tell the user:
1. What you understand the current state to be
2. What you plan to work on
3. What order you'll do things
4. Any concerns or questions

WAIT for user confirmation before proceeding.
```

---

## Output

By the end of this workflow, you should have:

- [ ] Full understanding of project state
- [ ] log.md created or updated with new session
- [ ] List of any failing tests or incomplete work
- [ ] Clear plan confirmed with user

---

## Next Workflow

After completing session start, typically proceed to:
- `02-implement-feature.md` — if building something new
- `03-debug-fix.md` — if fixing an issue
- `04-code-review.md` — if reviewing/refactoring