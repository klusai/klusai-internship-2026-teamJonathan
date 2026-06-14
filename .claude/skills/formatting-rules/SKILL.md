---
name: formatting-rules
description: Enforces the project's code style and formatting conventions by detecting violations and auto-fixing them. The ruleset covers universal rules (no emojis, no mid-sentence line breaks in prose and comments, trailing whitespace, end-of-file newline, blank-line limits, line length, smart quotes, tabs, CRLF) plus Python rules (naming conventions, import order, comma spacing, blank lines before definitions). Works on source code, Markdown, and Jupyter notebooks. Use this whenever the user asks to format, lint, clean up, standardize, audit, or check the style or conventions of code or documents - phrases like "fix the formatting", "clean this up before commit", "does this follow our style", "check for style violations", or any mention of formatting rules or code conventions.
---

# Formatting Rules

Enforce a defined, documented ruleset: detect violations precisely (file, line, rule ID), auto-fix everything that is safe to fix mechanically, and report the rest for manual action. Never silently change program behavior - that principle decides what is auto-fixable.

## The ruleset

Universal rules (any text file):

| ID   | Rule                                                        | Severity | Auto-fix |
|------|-------------------------------------------------------------|----------|----------|
| U001 | No emojis. In comments, docstrings, Markdown: removed. In string literals: reported only, since removal changes behavior | error | partial |
| U002 | No mid-sentence line breaks in prose (Markdown text, comments, docstrings). A sentence ends on the line it starts or flows without an arbitrary break | error | yes |
| U003 | No trailing whitespace                                       | error    | yes      |
| U004 | File ends with exactly one newline                           | error    | yes      |
| U005 | At most 2 consecutive blank lines                            | warning  | yes      |
| U006 | Code lines at most 100 characters (prose exempt - U002 forbids wrapping mid-sentence; URLs exempt) | warning | no |
| U007 | No smart quotes or typographic dashes in code (likely paste artifacts) | warning | yes |
| U008 | No tabs in indentation (Python: error, 4 spaces; others: warning) | error | yes |
| U009 | LF line endings, not CRLF                                    | warning  | yes      |

Python rules (.py files and notebook code cells):

| ID   | Rule                                                        | Severity | Auto-fix |
|------|-------------------------------------------------------------|----------|----------|
| P001 | Naming: functions and variables snake_case, classes PascalCase, module constants UPPER_SNAKE | warning | no (rename = refactor) |
| P002 | Imports at top of file, stdlib group before third-party/local | warning | no |
| P003 | Space after comma                                            | error    | yes      |
| P004 | Two blank lines before top-level def/class                   | warning  | yes      |

The full catalog is split by domain under `references/` - read only what the task at hand needs, when a violation needs explaining, the user questions a rule, or a case is borderline:

| Read | When |
|------|------|
| `references/universal-rules.md` | rationale/examples for any U-rule; shared scope rules |
| `references/python-rules.md` | target includes Python files or notebook code cells (P-rules, analyzer behavior, docstring handling) |
| `references/markdown-rules.md` | target includes Markdown/rst/txt (what counts as prose, U002 join conditions, hard-break tradeoff) |
| `references/notebooks.md` | .ipynb files involved (preservation guarantees, cell reporting, hand-editing warning) |
| `references/other-languages.md` | non-Python code (js/ts/c/java/sh/yaml/sql/json scoping and limitations) |

A typical mixed repo needs at most two of these; do not load all five up front.

## Workflow

**1. Scope.** Determine which files the user means: explicit paths, or the whole project (the checker walks directories itself and skips `.git`, virtualenvs, `node_modules`, caches, lock files, and binary files). Supported: code files, Markdown/text, and `.ipynb` notebooks (code cells get Python rules, markdown cells get prose rules; outputs and metadata are never touched).

**2. Check.** Run the bundled checker in report mode:

```bash
python3 <skill-path>/scripts/format_check.py <paths>
```

Useful flags: `--json report.json` for machine-readable output, `--rules U001,U002` or `--exclude-rules U006` to narrow the set, `--max-line-length N`, `--list-rules` for the catalog. Exit code 0 means clean, 1 means violations.

**3. Report.** Summarize for the user grouped by rule, with counts and representative `file:line` examples - not a raw dump of hundreds of lines. State clearly which violations are auto-fixable and which need manual work.

**4. Fix.** If the user asked for fixes (or asks now), run:

```bash
python3 <skill-path>/scripts/format_check.py --fix <paths>
```

The fixer applies only behavior-preserving fixes and prints what it fixed and what remains. It iterates internally until stable, so one invocation is enough.

**5. Handle the manual remainder.** What `--fix` leaves behind (naming, import order, long lines, emojis inside string literals) needs judgment. For each remaining violation either propose a concrete edit and apply it with the Edit tool after explaining it, or tell the user why it is better left alone (for example an emoji in a user-facing string that may be intentional product copy). Renames must update all usages - search before renaming.

**6. Verify.** Re-run the checker. Report the final state honestly: "clean" or "N violations remain, here is why". Run the per-domain verification steps listed at the end of the relevant reference file (py_compile for Python, JSON load for notebooks, `node --check` and friends for other languages).

## Judgment calls

- Audit-only requests ("check but do not change anything") mean exactly that: run check mode, write the report, modify nothing.
- Generated files, vendored code, and minified assets are not worth fixing; skip them and say so.
- When a fix would conflict with an external formatter config the project clearly uses (black, prettier, .editorconfig), defer to the project's formatter for the overlapping rule and apply only the rules it does not cover.
- The two-space Markdown hard break is treated as trailing whitespace (U003) by design: this ruleset forbids manual line breaks inside sentences anyway (U002), and an explicit blank line is the sanctioned way to separate paragraphs.
