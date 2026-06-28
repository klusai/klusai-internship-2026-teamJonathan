# CLAUDE.md — Sample Project

This file is the **project-level** memory for this sample repo. Claude Code loads
it automatically. Anything written here applies to every session opened in this
directory.

## Conventions

- **Indentation: use tabs, not spaces.** This applies to every language in the repo.
- Keep functions small and single-purpose.
- Prefer explicit names over abbreviations.

## TODO precedence

> When this file and a user-level memory (`~/.claude/CLAUDE.md`) disagree, the
> **project-level file you are reading now wins**. The user-level note in
> `README.md` claims the opposite — that conflict is intentional and is the
> thing you must resolve in Task 2 of this exercise.

## Path-specific rules

Two rule files live under `.claude/rules/`. They scope to subtrees via their
`paths` frontmatter and add constraints on top of these conventions:

- `frontend/**` — see `.claude/rules/frontend.md`
- `backend/**` — see `.claude/rules/backend.md`
