---
name: pr-description
description: Drafts a complete pull request description from the current branch's commits and diff. Gathers history against the base branch, explains what changed and why, groups key changes, and flags testing notes and breaking changes. Use this whenever the user wants to open, describe, or document a PR or merge request - phrases like "write a PR description", "draft the pull request", "summarize this branch for review", "prepare this for review", "what should the PR say", or when the user has just finished work on a branch and wants to ship or submit it.
---

# PR Description

Produce a reviewer-ready pull request description that is grounded entirely in the branch's actual commits and diff. The goal is to save the reviewer time: they should understand the intent, the shape of the change, and the risks before reading a single line of code. Never invent changes, tests, or motivations that are not supported by the repository evidence.

## Step 1: Collect the branch data

Run the bundled script from the repository root. It auto-detects the base branch (origin/main, origin/master, origin/develop, then local equivalents), finds the merge base, and prints the commits, diffstat, uncommitted status, and the diff:

```bash
bash <skill-path>/scripts/collect_branch_data.sh [optional-base-branch]
```

If the user named a target branch, pass it explicitly. If the script reports that the diff is too large to print, work from the diffstat and read the most significant files selectively with targeted `git diff <merge-base>..HEAD -- <path>` calls.

If the script cannot run for some reason, gather the same data manually: `git log --no-merges <base>..HEAD`, `git diff --stat <base>...HEAD`, and `git diff <base>...HEAD`.

## Step 2: Analyze before writing

Read the commit messages for intent (the why) and the diff for substance (the what). Commit messages tell you what the author believed they were doing; the diff tells you what actually changed. When they disagree, trust the diff and mention the discrepancy if it matters.

Work out:

- The single underlying purpose of the branch. Most branches do one thing; lead with it.
- Logical groups of changes (feature code, tests, docs, refactors, config). A reviewer thinks in these groups, not in file order.
- Issue or ticket references in commit messages (`#123`, `PROJ-456`, `fixes`/`closes` keywords). Carry them into the description so the PR auto-links.
- Breaking changes. Look for: removed or renamed public functions, classes, or endpoints; changed function signatures or return types; renamed or removed config keys, CLI flags, or environment variables; database or schema migrations; major version bumps of dependencies; changed file or API formats. If callers outside this diff would have to change, it is breaking.
- Testing evidence. New or modified test files, CI config changes, or commit messages describing manual verification. Report only what is actually there. If the branch has no tests, say so plainly in the Testing section and suggest what a reviewer should exercise manually - an honest gap is more useful to a reviewer than silence.
- Uncommitted changes shown in the STATUS section. They will not be part of the PR; warn the user if they look related.

## Step 3: Write the description

Follow the exact structure in `references/template.md` (read it before writing the first PR description in a session; it also contains a filled example). The structure in brief:

```markdown
**Title:** type(scope): imperative summary, 72 chars max

## Summary
## Changes
## Testing
## Breaking changes   <- include this section only when there is at least one
Closes #123           <- only when references were found
```

Style rules that matter:

- The title follows Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `build`, `ci`) and states the outcome, not the activity ("add JWT auth middleware", not "worked on auth").
- The Summary explains why first, then what, in 2-4 sentences. The reviewer should be able to stop reading after the Summary and still approve-or-route correctly.
- Changes bullets are concrete and verifiable against the diff ("Add retry with exponential backoff to S3 uploads in `uploader.py`", not "improved uploads"). Group related files into one bullet; never list every file mechanically - the diffstat already does that.
- Breaking changes name the old symbol, the new symbol, and the migration step.
- No filler ("This PR aims to...", "In this pull request we..."). Start sentences with the substance.

## Step 4: Deliver

Present the finished description in a fenced markdown block so the user can paste it directly. If the user asked for a file (or wants to keep it), save it as `PULL_REQUEST.md` in the repository root. Only create a PR on a hosting service (for example `gh pr create`) if the user explicitly asks and the CLI is available.

## Edge cases

- Branch equals base or merge base is HEAD: there is nothing to describe. Tell the user and stop rather than describing an empty diff.
- Single commit: the description can expand the commit message, but still verify against the diff - single commits often understate their contents.
- Cannot detect a base branch: ask the user which branch the PR targets instead of guessing.
- Merge commits in history: the script already excludes them from the log; the diff against the merge base remains correct.
- Huge branches (hundreds of files): describe by group using the diffstat, read only the files that define the change's character, and say explicitly which areas the description covers in less detail.
