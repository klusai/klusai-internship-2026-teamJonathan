# Markdown and prose files

Applies to `.md`, `.rst`, `.txt`. The universal rules apply; this file covers how they are interpreted for prose, where "what counts as a sentence" is the whole game.

## Line classification

Every line is classified before any rule runs: code fences (``` or ~~~) toggle a code region; YAML front matter at the top of the file is code; headings, table rows, and lines indented 4+ spaces are structural; everything else is prose. Rules then apply by class:

- Prose, headings, tables: emoji removal is auto-fix; U002 applies to prose only.
- Fence content and front matter: treated as code samples - emojis there are reported as manual (the sample's output might be the point), and U002 never joins lines inside them.

## U002 in Markdown: what joins and what never joins

A prose line joins its successor only when all of these hold: the line ends without sentence punctuation, the next line starts with a lowercase letter / digit / opening bracket, both are plain prose, the blockquote depth matches, and the indent difference is small. Never joined across: blank lines, headings, fences, tables, list-item boundaries (a continuation may join into its own item's first line, but a new `-` / `1.` item never merges into the previous one), or blockquote depth changes.

The practical effect: paragraphs that were manually wrapped get unwrapped into one line per sentence/paragraph; document structure is never collapsed.

## The hard-break tradeoff (U003 interaction)

Markdown's two-trailing-spaces hard break is deliberately sacrificed: trailing whitespace is always stripped. This ruleset already forbids manual breaks inside sentences (U002), and the sanctioned way to separate blocks is a blank line. If a project genuinely relies on hard breaks, run with `--exclude-rules U003` and say so in the report.

## What is exempt in prose

- U006 line length: prose is exempt by design - U002 forbids re-wrapping, so prose lines win the conflict and may be long.
- U007 smart quotes: typography is legitimate in prose; smart quotes are only flagged in code files.
- U008 tabs: exempt in Markdown (tabs can be meaningful inside code blocks).

## Reporting style for docs

When reporting violations in documentation files to the user, quote a short before/after pair for one representative U002 join rather than listing every joined line - prose fixes are easier to approve by example than by enumeration.
