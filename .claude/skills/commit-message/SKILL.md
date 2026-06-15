---
name: commit-message
description: Generate a clear, properly formatted Conventional Commits message from staged git changes. Use this whenever the user wants to commit, write or improve a commit message, asks "what should the commit message be", says they're about to commit, or wants help describing changes they've made — even if they don't say "conventional commits" explicitly. Reads the diff, infers type/scope/summary/body/footers, shows the message, and offers to commit.
---

# Commit Message

Turn staged changes into a commit message that follows the [Conventional Commits](https://www.conventionalcommits.org) spec. The goal is a message a teammate can read in six months and understand *what* changed and *why* — not just a restatement of the diff.

## Workflow

Follow these steps in order. Each one exists for a reason explained below.

### 1. Inspect what's being committed

Run these together to understand the change:

```bash
git diff --staged --stat   # which files, how much
git diff --staged          # the actual changes
```

**If nothing is staged** (`git diff --staged` is empty), don't guess from unstaged work. Show the user `git status --short` and offer to stage everything with `git add -A`, then continue once they confirm or stage things themselves. Committing the wrong set of files is worse than asking.

Also glance at recent history to match the repo's existing style — some projects use scopes heavily, some never do:

```bash
git log --oneline -10
```

### 2. Understand the change before naming it

Read the diff for intent, not just mechanics. Ask yourself: what does this change *accomplish*? A diff that touches `auth.ts` might be a new feature, a bugfix, or a refactor — the files don't tell you, the intent does. If the diff bundles several unrelated changes, say so: a good commit is one logical change, and the user may want to split it. Recommend splitting, but it's their call.

### 3. Compose the message

Use this exact structure:

```
<type>(<scope>): <summary>

<body>

<footer>
```

**Type** — pick the one that matches the *primary* intent:

| Type | Use for |
|------|---------|
| `feat` | A new capability or user-facing feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | A change that improves performance |
| `test` | Adding or correcting tests |
| `build` | Build system, dependencies, tooling config |
| `ci` | CI configuration and scripts |
| `style` | Formatting, whitespace, semicolons — no logic change |
| `chore` | Routine maintenance that fits nothing above |
| `revert` | Reverting a previous commit |

**Scope** — the area of the codebase affected, in parentheses, lowercase (e.g. `auth`, `api`, `pii`). Infer it from the changed paths or the repo's existing convention. Omit the parentheses entirely if the change is broad or no clear scope fits — a forced scope is noise.

**Summary** — the rest of the first line:
- Imperative mood: "add", "fix", "remove" — *not* "added" / "adds" / "fixing". (Read it as "this commit will _add_…".)
- Lowercase first letter, no trailing period.
- Keep the whole first line ≤ ~50 characters where you can, 72 is the hard ceiling. If you can't say it in 72 chars, the body is where detail goes.

**Body** — always include one. Separate it from the summary with a blank line and wrap at 72 columns. The body's job is the **why**: the motivation, the problem being solved, the approach, and any consequence a reader should know. Don't narrate the diff line-by-line ("changed x to y") — the diff already says that. Explain what the diff can't. For genuinely trivial changes where the summary is fully self-explanatory, a single short sentence of context is fine — but write something.

**Footer** — only when applicable:
- **Breaking changes:** add a `!` after the type/scope (`feat(api)!:`) *and* a footer line `BREAKING CHANGE: <what broke and how to migrate>`. This is load-bearing for semver tooling, so don't skip the footer even with the `!`.
- **Issue references:** if the context, branch name, or the user mentions an issue, add `Closes #123` (or `Refs #123` if it doesn't fully resolve it).

### 4. Show it, then offer to commit

Present the full message to the user in a code block. Then ask whether to commit it. Only run `git commit` after they say yes — and when you do, pass the message via multiple `-m` flags or a heredoc so the body and footer survive:

```bash
git commit -m "feat(auth): add passwordless email login" -m "$(cat <<'EOF'
Users repeatedly asked for a login option that doesn't require
managing a password. This adds a magic-link flow backed by the
existing token service.

Closes #218
EOF
)"
```

Never amend, force, or push unless the user explicitly asks.

## Examples

**Example 1 — feature with body and issue ref**
Diff: new React hook + endpoint enabling magic-link login, branch `feat/passwordless-218`.
```
feat(auth): add passwordless email login

Users repeatedly asked for a login option that doesn't require
managing a password. This adds a magic-link flow backed by the
existing token service, reusing the email templates from signup.

Closes #218
```

**Example 2 — bug fix, narrow scope**
Diff: corrects an off-by-one in pagination so the last page isn't dropped.
```
fix(api): include final page in paginated results

The cursor advanced past the last record because the loop used a
strict less-than on a count that was already zero-indexed, so the
final page was silently omitted from responses.
```

**Example 3 — breaking change**
Diff: renames the `token` response field to `access_token`.
```
feat(api)!: rename token field to access_token

Aligns the auth response with the OAuth2 naming clients expect and
removes ambiguity with the refresh token introduced last release.

BREAKING CHANGE: the login response field `token` is now
`access_token`. Clients reading `token` must update to the new key.
```

**Example 4 — small change, still gets context**
Diff: bumps a dependency to patch a CVE.
```
build(deps): bump axios to 1.7.4

Picks up the fix for CVE-2024-28849 (follow-redirects credential
leak). No code changes required on our side.
```
