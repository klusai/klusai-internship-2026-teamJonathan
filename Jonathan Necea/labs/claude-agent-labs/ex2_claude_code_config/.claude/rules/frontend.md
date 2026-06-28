---
paths: "frontend/**"
---

# Frontend rules

These rules apply to every file under `frontend/`.

- **No `console.log` (or `console.debug` / `console.info`) in committed code.** Use
  the project logger instead. Debug logging left in source is a blocking issue.
- Components must be small and focused; extract anything over ~150 lines.
- Prefer `const` over `let`; never use `var`.

When reviewing or editing a file in `frontend/`, enforce the no-`console.log` rule
before anything else.
