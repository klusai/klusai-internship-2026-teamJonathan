# Exercise 2 — Configure Claude Code for a real project

**Topic:** CLAUDE.md hierarchy, path-specific rules in `.claude/rules/`, skills with
`context: fork` and `allowed-tools`, and MCP server integration.

## Goal

Turn an empty project into one that is *configured* — so that Claude Code behaves
differently in `frontend/` than in `backend/`, refuses to do the wrong thing in a
skill, and resolves a deliberate conflict between project- and user-level memory the
right way.

## What's here

```
ex2_claude_code_config/
  CLAUDE.md                              project memory (tabs, TODO-precedence line)
  README.md                             ← you are here (also holds a conflicting note)
  .claude/rules/frontend.md              appliesTo frontend/** — forbids console.log
  .claude/rules/backend.md               appliesTo backend/**  — requires type hints
  .claude/skills/generate-endpoint/SKILL.md   skill with TODO frontmatter
  frontend/                              empty — add a file here to see the rule fire
  backend/                               empty — add a file here to see the rule fire
```

## ⚠️ Conflicting user-level note (read this)

Pretend the following line lives in your **user-level** memory
(`~/.claude/CLAUDE.md`), which applies across all your projects:

> **User-level memory says:** "In all my projects, indent with **4 spaces**. Never
> use tabs."

But `CLAUDE.md` in *this* project says **use tabs**, and states that the
project-level file wins. That is a real, deliberate conflict. Part of this exercise
is deciding — and documenting — which one Claude should follow here, and why.

## Tasks

1. **Read the hierarchy.** Open `CLAUDE.md` and both files in `.claude/rules/`.
   Write down, in your own words, the order of precedence between: enterprise
   policy → project `CLAUDE.md` → user `~/.claude/CLAUDE.md` → path-specific rules.

2. **Resolve the conflict.** Tabs vs. 4 spaces. State which one applies *in this
   project* and the rule that decides it. (Hint: more-specific / project scope beats
   broader / user scope.)

3. **Make the rules bite.** Add `frontend/app.js` containing a `console.log(...)`
   and `backend/service.py` containing a function with no type hints. Ask Claude
   Code to review each. Confirm the `frontend` rule flags the `console.log` and the
   `backend` rule flags the missing type hints.

4. **Finish the skill.** Open `.claude/skills/generate-endpoint/SKILL.md` and fill
   in the two TODO frontmatter keys: `context` and `allowed-tools`. The skill must
   run in a **forked context** and must be allowed **only** `Read` and `Write` —
   `Bash` must be blocked. Then describe how you'd verify Bash is actually blocked.

5. **Wire one MCP server.** Add a single MCP server to this project's
   `.claude/settings.local.json` (for example, a filesystem server). Capture
   **evidence** that it loaded: the `/mcp` output, or a screenshot, or the tool list.
   Save the evidence as `mcp-evidence.md` (or `.png`) in this folder.

## Acceptance criteria

- [ ] Precedence order written out, and the tabs-vs-spaces conflict resolved with a
      stated reason.
- [ ] A `console.log` in `frontend/` is flagged; a missing type hint in `backend/`
      is flagged; neither rule fires in the other subtree.
- [ ] `SKILL.md` frontmatter has `context: fork` and `allowed-tools: [Read, Write]`,
      and you can explain how a Bash attempt would be refused.
- [ ] One MCP server is configured and there is captured evidence it loaded.

## Stretch goals

- Add an **enterprise-level** rule (the highest tier) and show it overriding the
  project `CLAUDE.md`.
- Add a second rule file scoped to `**/*.test.*` and show two rules stacking on one
  file.
- Give the skill a third allowed tool and observe how its behavior changes.

## Self-check

- Can you predict, *before running Claude*, which rules apply to a given path?
- If you moved `console.log` into `backend/`, would the frontend rule still fire? Why?
