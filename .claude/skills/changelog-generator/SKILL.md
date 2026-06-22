---
name: changelog-generator
description: Builds a structured changelog from commit history or merged PRs, grouping entries (Added, Changed, Fixed, Removed) and formatting them for a release following Keep a Changelog conventions. Use when the user asks to generate a changelog, prepare release notes, summarise changes between tags, or document what changed since the last version.
---

# Changelog Generator

Produce a human-readable changelog entry that follows the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
The goal is entries a non-technical stakeholder can read and a developer can act on — not a reformatted `git log`.
Read `references/keepachangelog.md` (relative to this skill) before writing the first changelog in a session.

## Step 1 — Understand the scope

Ask yourself (or the user, if ambiguous) two questions before running anything:

1. **What version is this changelog entry for?**
   - If the user supplies a version string (`1.3.0`, `v2.0.0-rc1`), use it.
   - If they say "Unreleased" or haven't shipped yet, label the section `[Unreleased]`.
   - If neither, inspect the tag list the script returns and suggest the next semver bump based on the types of changes found (breaking → major, features → minor, fixes/chores → patch). State your reasoning and let the user confirm.

2. **What commit range should be covered?**
   - Default: everything since the most recent tag up to HEAD.
   - If the user specifies a range ("since v1.1.0", "between v1.0 and v1.2"), translate that to `--since` and `--until` flags.
   - If the repo has no tags, cover all commits and note that in the output.

## Step 2 — Collect the data

Run the bundled script from the repository root:

```bash
python <skill-path>/scripts/collect_commits.py [--since TAG] [--until REF] [--prs]
```

- `--since TAG` — the exclusive lower bound (the last released tag). Omit to auto-detect.
- `--until REF` — the inclusive upper bound. Defaults to HEAD.
- `--prs` — pass this when the user wants PR titles instead of (or in addition to) commit subjects, and `gh` is available.

The script prints JSON with these top-level keys:

| Key | Contents |
|-----|----------|
| `grouped` | Commits bucketed into `added`, `changed`, `fixed`, `removed`, `deprecated`, `security`, `uncategorized` |
| `breaking` | Commits where a `!` conventional-commit marker was detected |
| `latest_tag` | Most recent tag, useful for the comparison link footer |
| `all_tags` | Up to 10 recent tags for context |
| `repo_url` | Remote URL for building comparison links |
| `raw` | All commits in order, for your own pass |

If the script errors or `git` isn't available, gather data manually:

```bash
git log --no-merges --pretty=format:"%h %as %s" <base>..<until>
```

## Step 3 — Classify and curate

The script does a first-pass classification based on conventional-commit type prefixes.
Your job is to **verify and improve** that classification, because many commits are not conventional-format and the script puts them in `uncategorized`.

Work through `raw` and apply judgment:

- **Added** — introduces a new capability the user of the project can discover and use: new endpoints, flags, functions, config keys, integrations.
- **Changed** — modifies existing behaviour in a way that could affect users or callers: renamed symbols, altered defaults, updated dependencies that change behaviour, performance improvements (when user-visible), breaking changes.
- **Fixed** — corrects unintended behaviour: bug fixes, incorrect outputs, error handling, off-by-ones.
- **Removed** — deletes something that existed before: dropped endpoints, removed flags, deleted modules.
- **Deprecated** — marks something for future removal (often a commit that adds a deprecation warning).
- **Security** — patches a vulnerability; may also go in Fixed, but surfaces here for visibility.
- **Skip entirely** — internal-only chores invisible to users: CI tweaks, test-only changes, whitespace/lint fixes, dependency bumps that don't change behaviour. Use judgment: a security-patch dependency bump is Security, not skip.

**Merging duplicates:** commits that say the same thing (e.g., three "bump dependency" commits) collapse into one entry. Pick the most informative subject.

**Uncategorized commits:** read the body or diff (if needed) to place them. If truly ambiguous, put them in Changed with a note.

**Breaking changes:** any commit in `breaking` (detected by `!`) OR any commit whose subject or body says "breaking", "BREAKING CHANGE", "removed", "renamed" for a public API, must appear in Changed with a clear migration note. Also add a `### Breaking Changes` sub-heading if there are multiple, or a prominent inline note for one-offs.

## Step 4 — Write the entries

Transform each grouped commit into a plain-English bullet following the rules in `references/keepachangelog.md`.

Key rules:
- One bullet per logical change, not per commit (multiple commits about the same feature → one entry).
- Imperative mood: "Add", "Fix", "Remove" — not "Added" / "Fixes" / "Removes".
- Name the public surface: a flag, a function, a config key, an endpoint — not an internal class or file.
- Breaking changes get a migration note inline: `- Rename `Config.db_url` to `Config.database_url`; update config files.`
- Security entries include the CVE or a one-sentence risk description.
- If PR titles were fetched and are clearer than commit subjects, prefer them.

## Step 5 — Assemble the changelog block

Use this exact structure (from `references/keepachangelog.md`):

```markdown
## [VERSION] - YYYY-MM-DD

### Security
- ...

### Added
- ...

### Changed
- ...

### Deprecated
- ...

### Fixed
- ...

### Removed
- ...
```

- Omit any section that has no entries.
- Date is today's date in ISO 8601 unless the user specifies otherwise.
- If the repo has a `CHANGELOG.md` file, the new block goes **above** the most recent existing entry (changelogs are newest-first).
- Append the comparison link to the footer block:
  ```
  [VERSION]: <repo_url>/compare/<prev-tag>...v<VERSION>
  ```
  If `repo_url` is null, leave a placeholder: `[VERSION]: <compare-url>`.

## Step 6 — Deliver

Present the finished block in a fenced markdown code block so the user can paste it directly.

Then ask whether to:
1. **Prepend it to `CHANGELOG.md`** (create the file if it doesn't exist, with the standard header).
2. **Write it to a new file** (`RELEASE_NOTES.md` or similar).
3. **Leave it in the conversation only** (default if the user doesn't say).

Only write files after the user confirms.

If the user wants you to also create a git tag, suggest the command but don't run it without confirmation:

```bash
git tag -a v<VERSION> -m "Release v<VERSION>"
```

## Edge cases

- **No commits found:** the range is empty (e.g., HEAD is already tagged). Say so and stop — don't invent entries.
- **All commits are chores:** tell the user — a changelog with only internal entries is normal for a patch; they may want to skip the release note or write a one-liner summary.
- **Very large history (200+ commits):** process the `grouped` buckets rather than reading every raw commit individually. Note how many commits contributed and say if any were folded or skipped.
- **No tags at all:** cover all commits, label the section `[Unreleased]` or `[1.0.0]` based on user intent, and skip the comparison link footer.
- **Monorepo with unrelated changes:** ask the user which package/directory this changelog is for, then re-run with `git log -- <path>` filtering if needed (pass the path after `--` in the script invocation; it forwards to `git log`).
- **Existing CHANGELOG.md:** read the first 30 lines to detect the format before writing. Match whatever style is already there (some projects use slightly different heading levels or link styles). Don't rewrite history — only prepend.
