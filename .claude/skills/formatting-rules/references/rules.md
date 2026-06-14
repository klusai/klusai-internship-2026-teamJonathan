# Rule catalog - index

The catalog is split by domain so only the relevant part needs to be read:

- `universal-rules.md` - U001-U009: rationale, examples, auto-fix policy, shared scope rules. Read when explaining or disputing a universal rule.
- `python-rules.md` - P001-P004, how Python is analyzed (tokenize/ast, docstrings, magic fallback), verification steps. Read when the target includes Python files or notebook code cells.
- `markdown-rules.md` - how prose rules apply to Markdown (line classification, U002 join conditions, hard-break tradeoff, prose exemptions). Read when the target includes Markdown/rst/txt.
- `notebooks.md` - Jupyter specifics: per-cell handling, preservation guarantees, reporting format, hand-editing warning. Read when .ipynb files are involved.
- `other-languages.md` - the generic analyzer (js/ts/c/java/sh/yaml/sql/json...), its scoping and known limitations. Read for non-Python code.

Quick severity/fix summary lives in the table in SKILL.md.
