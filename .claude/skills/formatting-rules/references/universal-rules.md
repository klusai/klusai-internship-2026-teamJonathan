# Universal rules (U001-U009)

These apply to every supported text file: code, Markdown, and notebook cells. Severity meaning: an error must be fixed before the code is considered clean; a warning should be fixed but may be deferred with a reason. "Auto-fix" means `format_check.py --fix` handles it; everything else needs a human or model decision because fixing it mechanically could change behavior.

## U001 no-emoji (error)

Emojis and pictographs (Unicode emoji blocks, dingbats, miscellaneous symbols, ZWJ sequences, variation selectors) do not belong in source code or project documents. They render inconsistently across terminals, fonts, and diff tools, break some encodings and linters, and read as noise in professional output.

- Auto-fixed in: comments, docstrings, Markdown prose, notebook markdown cells. Leftover double spaces and space-before-punctuation are tidied.
- Reported only (manual) in: string literals and code-block content, because removing a character from a string changes program output. Decide case by case; an emoji in user-facing copy may be intentional.

Bad: `# Train the model 🚀` / Good: `# Train the model`

## U002 no-midsentence-linebreak (error)

A sentence must not be split across lines by a manual line break. Mid-sentence breaks make diffs noisy (editing one word rewraps a paragraph), break grep-ability of phrases, and render as a single flowed paragraph anyway in Markdown. Write one sentence per line or one paragraph per line; separate paragraphs with a blank line.

Detection heuristic: a prose line that ends without sentence-ending punctuation (`.` `!` `?` `:` `;`) whose next line starts with a lowercase letter, digit, or opening bracket is treated as broken; the two lines are joined with a single space. The heuristic is deliberately conservative: continuations that begin with a capitalized word are skipped, so some broken sentences are missed rather than ever merging two distinct sentences. Domain specifics (which lines count as prose) live in the per-domain reference files.

Bad:

```markdown
The model is trained on the full
dataset using early stopping.
```

Good:

```markdown
The model is trained on the full dataset using early stopping.
```

## U003 trailing-whitespace (error)

Whitespace at end of line is invisible, churns diffs, and trips some tools. Auto-fixed by stripping. See the Markdown reference for the hard-break interaction.

## U004 eof-newline (error)

Every file ends with exactly one newline: POSIX defines a line as newline-terminated, `cat`, `diff` and many tools misbehave otherwise, and trailing blank lines are dead weight. Auto-fixed both ways (missing newline added, extra trailing blank lines removed). Does not apply inside notebook cells.

## U005 max-blank-lines (warning, default 2)

More than two consecutive blank lines adds no structure that two do not already provide. Auto-fixed by collapsing the run to the maximum. Interior runs only; trailing runs are handled by U004. Override with `--max-blank-lines`.

## U006 line-length (warning, default 100, manual)

Long code lines force horizontal scrolling and hurt side-by-side review. Limit 100 (override with `--max-line-length`). Exemptions: prose lines (U002 forbids re-wrapping sentences, so they win), comment-only lines, and lines containing URLs. Not auto-fixed: breaking a code line well requires understanding it (choosing the break point, adding parentheses). Reflow manually or with the project's formatter.

## U007 smart-quotes (warning)

Typographic quotes and dashes in code regions are almost always paste artifacts from chat tools or word processors and can break parsing or comparisons. Auto-fixed by straightening to ASCII equivalents in code regions of code files. Markdown prose is exempt (typography is legitimate there). Smart quotes used as string delimiters usually surface as a syntax error, which the analyzers tolerate by falling back to generic mode and still flagging the characters.

## U008 tabs-in-indent (error in Python, warning elsewhere)

Mixed tabs and spaces render differently per editor and are a syntax hazard in Python. Auto-fixed by replacing each leading tab with 4 spaces. Markdown files are exempt (tabs can be meaningful in code blocks).

## U009 line-endings (warning)

Repository files use LF. CRLF sneaks in from Windows editors and produces whole-file diffs. Auto-fixed by normalizing to LF (configure `.gitattributes` to keep it that way). When U009 is excluded from the run, the fixer preserves the file's original CRLF endings.

## Shared scope rules

Skipped everywhere: binaries, files over 2 MB, lock files, `.git`, virtualenvs, `node_modules`, caches, build output, `.ipynb_checkpoints`. Unknown extensions are not touched at all - predictability beats coverage.
