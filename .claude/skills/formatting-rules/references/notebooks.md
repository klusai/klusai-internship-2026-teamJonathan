# Jupyter notebooks (.ipynb)

Notebooks are first-class targets: the checker parses the JSON, analyzes each cell by type, and writes back without disturbing anything else.

## How cells are handled

- Code cells are analyzed as Python (universal + P-rules). Cells containing IPython magics (`%matplotlib`, `!pip install`, ...) cannot be AST-parsed, so they fall back to the generic analyzer: universal rules still apply, P-rules are skipped for that cell.
- Markdown cells are analyzed as Markdown prose (see markdown-rules.md): emoji removal and U002 sentence joins apply.
- Raw cells and cell outputs are never touched.

## What is guaranteed preserved

Fixes rewrite only the `source` arrays of cells. Outputs, execution counts, cell ids, kernelspec, language_info, and all other metadata stay byte-for-byte semantically identical. The file is re-serialized the way Jupyter does (indent 1, non-ASCII kept literal, trailing newline), so the diff shows only the changed source lines.

U004 (EOF newline) and U009 (CRLF) do not apply inside cells - they are file-level concepts handled by the serializer.

## Reporting

Violations are reported as `file.ipynb cell N, line M` with N being the 1-based cell index, so the user can jump straight to the cell in Jupyter.

## Verification step

After fixing, confirm the notebook still loads: `python3 -c "import json; json.load(open('nb.ipynb'))"` and, when convenient, that the code cells still parse (`ast.parse` on the joined source). The bundled fixer maintains validity by construction, but if any manual edits were made on top, verify before declaring the notebook clean.

## A warning about hand-editing

Never edit notebook JSON by hand or with text-replacement on the raw file: escaping mistakes corrupt the whole notebook and the failure mode is silent until Jupyter refuses to open it. Use the bundled checker for mechanical fixes; for manual-judgment items (emoji in a string literal inside a code cell), edit the cell source through proper JSON round-tripping.
