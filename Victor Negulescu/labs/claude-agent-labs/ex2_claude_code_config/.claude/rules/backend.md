---
appliesTo: "backend/**"
---

# Backend rules

These rules apply to every file under `backend/`.

- **Every function and method must have complete type hints** — annotate all
  parameters and the return type. An un-annotated function is a blocking issue.
- Validate input at the boundary; trust internal calls.
- Raise specific exceptions, never bare `except:`.

When reviewing or editing a file in `backend/`, enforce the type-hint rule before
anything else.
