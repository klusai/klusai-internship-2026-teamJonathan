# PR description template

Use this exact structure. Omit the "Breaking changes" section entirely when there are none, and the trailing issue line when no references exist. Keep every other section, even when short - a one-line Testing section saying "No automated tests in this branch; verify X manually" is informative.

## Template

```markdown
**Title:** type(scope): imperative summary under 72 characters

## Summary

Two to four sentences. First the why: what problem or need motivated this
branch. Then the what: the approach taken, at the level of design rather
than file-by-file detail.

## Changes

- Concrete, diff-verifiable bullet, grouped by logical area
- Another group of related changes, naming key files or symbols in backticks
- Tests and docs changes get their own bullets when present

## Testing

- What automated tests were added or updated, and what they cover
- What was verified manually, if the commits or user say so
- What a reviewer should exercise to gain confidence, when coverage is thin

## Breaking changes

- `old_symbol()` renamed to `new_symbol()` - callers must update imports
- Each entry: what breaks, who is affected, the migration step

Closes #123
```

## Title rules

- Conventional Commit types: `feat`, `fix`, `refactor`, `docs`, `test`, `perf`, `chore`, `build`, `ci`.
- Scope is optional but helpful when the repo has clear modules: `feat(auth): ...`.
- Imperative mood, no trailing period, 72 characters maximum.
- Describe the outcome ("add token refresh to auth client"), not the work ("fixed stuff", "changes for review").

## Filled example

```markdown
**Title:** feat(auth): add JWT authentication middleware

## Summary

API routes were unprotected, blocking the public beta (see #42). This PR
introduces JWT-based authentication as Express middleware: tokens are issued
on login, validated on every request, and refreshed transparently within a
15-minute expiry window. The previous ad-hoc session check in `routes.js` is
removed in favor of the middleware.

## Changes

- Add `middleware/auth.js` implementing JWT issue/verify/refresh with `jsonwebtoken`
- Replace the legacy `login(user, pass)` helper with `authenticate(credentials)` in `lib/session.js`
- Wire the middleware into all `/api/*` routes in `app.js`
- Add unit tests for token expiry and refresh (`test/auth.test.js`, 12 cases)
- Document the auth flow and required `JWT_SECRET` env var in `README.md`

## Testing

- `npm test` passes; new suite covers issue, verify, expiry edge (off-by-one
  fixed in 3f2a1c9), and refresh paths
- Manually verified login -> protected route -> token expiry -> refresh against
  a local server

## Breaking changes

- `login(user, pass)` is removed; call `authenticate({user, pass})` instead.
  External scripts using the old helper must migrate.
- All `/api/*` requests now require an `Authorization: Bearer <token>` header.

Closes #42
```

## Why this structure

Reviewers triage dozens of PRs; the Summary lets them route or approve without opening files. The grouped Changes map to how they will actually review (area by area, not file by file). Testing tells them where confidence comes from and where it is missing. Breaking changes are the one thing that must never be discovered after merge, so they get their own loud section near the end, right before the auto-linking issue reference.
