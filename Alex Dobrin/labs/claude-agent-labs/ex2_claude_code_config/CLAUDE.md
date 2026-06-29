# CLAUDE.md — Sample Project

This file is the **project-level** memory for this sample repo. Claude Code loads
it automatically. Anything written here applies to every session opened in this
directory.

## Conventions

- **Indentation: use tabs, not spaces.** This applies to every language in the repo.
- Keep functions small and single-purpose.
- Prefer explicit names over abbreviations.

## Precedence

**When this project-level file conflicts with the user-level memory
(`~/.claude/CLAUDE.md`), this project-level file wins.** Project scope is more
specific than user scope, so a project instruction always overrides a broader
user-level one for sessions opened in this repo.

Concretely: the user-level memory says "indent with 4 spaces, never tabs," but
this file says **use tabs** (see Conventions above). In this project, **tabs
apply** — the project-level rule overrides the user-level preference.

Full order of precedence, highest to lowest:

1. Enterprise-managed policy
2. **Project memory** (`./CLAUDE.md` — this file)
3. User memory (`~/.claude/CLAUDE.md`)

Path-specific rules under `.claude/rules/` don't sit in this ranking — they add
constraints on top of whichever memory wins, scoped to their subtree.

## Path-specific rules

Two rule files live under `.claude/rules/`. They scope to subtrees via their
`appliesTo` frontmatter and add constraints on top of these conventions:

- `frontend/**` — see `.claude/rules/frontend.md`
- `backend/**` — see `.claude/rules/backend.md`
