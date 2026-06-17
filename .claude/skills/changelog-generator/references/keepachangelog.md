# Keep a Changelog — Format Reference

Source: https://keepachangelog.com/en/1.1.0/

## Guiding Principles

- Changelogs are for **humans**, not machines — write in plain language, not commit hashes.
- Group changes by **type** so readers can scan for what matters to them.
- Each version gets its own dated section; newest version comes **first**.
- Dates use ISO 8601 format: `YYYY-MM-DD`.
- Note whether a release is `[YANKED]` when it had to be pulled due to a critical bug.

## Section Types (in recommended order)

| Section      | Use for |
|--------------|---------|
| `Security`   | Vulnerability fixes. Always list first — high urgency. |
| `Added`      | New features and capabilities. |
| `Changed`    | Changes to existing functionality, including breaking changes. |
| `Deprecated` | Features that will be removed in a future release. |
| `Fixed`      | Bug fixes. |
| `Removed`    | Features, APIs, or config keys removed in this release. |

Omit any section that has no entries for the release.

## Canonical Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature that isn't yet tagged.

## [1.2.0] - 2024-03-15

### Security
- Upgrade `requests` to 2.31.0 to patch CVE-2023-32681.

### Added
- `--dry-run` flag for the deploy command.
- Support for PostgreSQL 16.

### Changed
- `Client.connect()` now raises `ConnectionError` instead of returning `None`
  on failure; callers must update exception handling.

### Fixed
- Race condition in the job queue that caused duplicate runs under high load.

## [1.1.0] - 2024-01-08

### Added
- User preference persistence across sessions.

### Removed
- Dropped support for Python 3.8 (EOL).

## [1.0.0] - 2023-11-20

- Initial stable release.

[Unreleased]: https://github.com/owner/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/owner/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/owner/repo/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/owner/repo/releases/tag/v1.0.0
```

## Entry Writing Rules

- **One idea per bullet.** Don't combine two changes on one line.
- **User perspective, not implementation detail.** "Add `--timeout` flag for API calls" beats "Add timeout parameter to RequestBuilder class".
- **Imperative mood, present tense.** "Add", "Fix", "Remove" — same as a commit subject.
- **Mention the public symbol** when a change is specific: a flag name, a function name, a config key.
- **Breaking changes** need a migration note. E.g., "`Config.db_url` renamed to `Config.database_url`; update your config files."
- **Security entries** should include a CVE number or brief description of the risk, but never enough detail to reproduce an exploit.
- No trailing period on one-liner bullets. Multi-sentence prose in a continuation line is fine.
- Scope or module prefix in backticks is encouraged when the project has clear modules:
  `` - `auth`: Add token refresh on 401 responses. ``

## Version Link Footer

Always append comparison links at the bottom. Pattern:

```
[Unreleased]: <repo>/compare/<latest-tag>...HEAD
[X.Y.Z]: <repo>/compare/<prev-tag>...<this-tag>
[initial]: <repo>/releases/tag/<first-tag>
```
