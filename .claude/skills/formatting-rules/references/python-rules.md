# Python rules (P001-P004) and how Python is analyzed

Applies to `.py` files and notebook code cells. The universal rules also apply; this file covers what is Python-specific.

## How the analyzer works (and why it matters)

Python files are tokenized with the stdlib `tokenize` module and parsed with `ast`. That means string literals and comments are identified exactly, not guessed by regex: a comma inside `"1,2"` is never flagged, a docstring is distinguished from an ordinary string, and naming/import rules come from the real syntax tree. Consequences worth knowing:

- Files that fail to parse (syntax errors, or notebook cells containing `%magics` / `!shell` lines) fall back to the generic analyzer: universal rules still apply, P-rules do not. After `--fix` repairs a blocking issue (for example tabs in indentation, which are a Python syntax hazard), the fix loop re-analyzes and the AST rules activate on later passes automatically.
- Docstrings are treated as prose: emojis are auto-removed there, and U002 joins broken sentences only between lines at identical indentation, so parameter blocks (`Args:` sections, indented continuations) are never collapsed. Bare quote lines (`"""` alone) are never joined.
- U008 (tabs in indentation) is severity error for Python, warning elsewhere.

## P001 python-naming (warning, manual)

PEP 8: functions, variables, and arguments use `snake_case`; classes use `PascalCase`; module-level constants use `UPPER_SNAKE`. Checked for function/class definitions, arguments, and module/class-level assignment targets - locals are deliberately not flooded with warnings. Dunders and `self`/`cls` are exempt.

Never auto-fixed: a rename is a refactor that must update every usage. Search the whole project for usages first; if all call sites are local and updated together, the rename is safe to propose. If the symbol could be imported externally, report instead.

Bad: `def getUserData(userId):` / Good: `def get_user_data(user_id):`

## P002 import-order (warning, manual)

PEP 8: imports live at the top of the file (after the module docstring), grouped stdlib first, then third-party, then local. Flagged: stdlib imports appearing after third-party ones, and any import after non-import code. `__future__` imports are exempt; imports nested in `try:` or `if TYPE_CHECKING:` blocks are not checked (they are usually deliberate).

Not auto-fixed: moving imports can change behavior (import side effects, circular-import workarounds), so reorder deliberately.

## P003 comma-spacing (error)

PEP 8: a comma is followed by a space, except before a closing bracket (`(1,)` is fine). Auto-fixed by inserting the space; strings and comments are masked first.

Bad: `f(a,b, c)` / Good: `f(a, b, c)`

## P004 blank-lines-before-def (warning)

PEP 8: two blank lines before top-level `def`/`class`. Decorators and comment blocks directly above the definition count as part of it - the blank lines go above them. First statement in a file is exempt. Auto-fixed by inserting the missing blank lines; works together with U005 (which caps runs at 2 from above).

## Verification step

After fixing Python files, confirm they still parse: `python3 -m py_compile <file>`. The fixer only makes behavior-preserving edits, but verification is cheap and catches surprises (including files that were already broken before the run).
