---
name: task-breakdown
description: Takes a feature request or ticket and decomposes it into ordered, concrete implementation subtasks with dependencies and estimated complexity. Use when the user wants to plan a feature, break down a ticket, or create an implementation checklist.
---

You are decomposing a feature request into actionable subtasks.

## Input

The feature request or ticket description is provided in `$ARGS`. If `$ARGS` is empty, ask the user to describe the feature.

## Steps

### 1. Understand the scope
Read `$ARGS` carefully. If the codebase is available, scan relevant files to understand the existing structure before planning.

### 2. Identify the subtasks
Break the feature into the smallest independently completable units of work. Each subtask must:
- Have a single, clear goal
- Be implementable without completing future subtasks (unless a dependency is declared)
- Map to a concrete code change (file, function, API endpoint, test, config)

### 3. Order by dependency
Determine which subtasks must be completed before others. Build a dependency chain.

### 4. Estimate complexity
Rate each subtask:
- **S** (small): < 1 hour, trivial change
- **M** (medium): 1–4 hours, straightforward implementation
- **L** (large): 4–8 hours, requires design decisions
- **XL** (extra large): > 8 hours, should be broken down further

## Output format

```
## Feature: <feature name>

### Subtasks

1. [ ] [S] <Task title>
   - What: <one sentence describing the change>
   - Where: <file(s) or module>
   - Depends on: none

2. [ ] [M] <Task title>
   - What: <one sentence describing the change>
   - Where: <file(s) or module>
   - Depends on: #1

...

### Summary
- Total tasks: N
- Estimated effort: X–Y hours
- Highest risk: <task number and reason>
```

## Notes
- Flag any XL tasks with a note recommending further breakdown.
- If a task has external dependencies (third-party APIs, infrastructure), call that out explicitly.
- Do not include tasks for things that already exist in the codebase.
