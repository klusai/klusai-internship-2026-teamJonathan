# CLAUDE.md Hierarchy — Notes

## Task 1: Precedence order

From broadest to most specific:

1. **Enterprise policy** (highest) — set by an organisation admin, applies to all
   projects in the workspace. Overrides everything below it.
2. **Project `CLAUDE.md`** — lives at the repo root, applies to every session
   opened in that directory.
3. **User `~/.claude/CLAUDE.md`** — personal defaults, applies across all projects
   unless overridden by a project or enterprise setting.
4. **Path-specific rules** (`.claude/rules/*.md`) — narrowest scope; fire only for
   files whose paths match the `appliesTo` glob.

Rules lower in the list only cover what the broader ones do not, so a project rule
beats a user rule, and a path rule adds constraints on top of the project rule for
its subtree.

## Task 2: Tabs vs. 4 spaces — which wins here?

**Tabs win in this project.**

The project `CLAUDE.md` explicitly states "use tabs, not spaces" and notes that the
project-level file takes precedence over user-level memory. More-specific scope
beats broader scope: the project setting overrides the user's "4 spaces" default for
any session opened in this directory.

## Task 3: Rules firing on sample files

- `frontend/app.js` contains `console.log(...)`. The `frontend/**` rule in
  `.claude/rules/frontend.md` flags it as a blocking issue.
- `backend/service.py` contains `get_user` and `create_order` with no type hints.
  The `backend/**` rule in `.claude/rules/backend.md` flags the missing annotations
  as a blocking issue.
- Neither rule fires in the other subtree: the frontend rule does not touch
  `backend/`, and the backend rule does not touch `frontend/`.

## Task 4: Skill frontmatter

`context: fork` — the skill runs in an isolated, forked context so its file edits
do not appear in the main conversation history.

`allowed-tools: [Read, Write]` — only file-read and file-write are permitted. If
the skill tries to call Bash (e.g. "run the tests"), Claude Code refuses because
`Bash` is not in the allow-list.
