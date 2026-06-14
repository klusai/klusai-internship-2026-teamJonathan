# Other languages (generic analyzer)

Applies to: js, jsx, ts, tsx, java, c, h, cpp, hpp, cs, go, rs, css, scss, sql, sh, bash, zsh, yaml, yml, toml, r, R, rb, jl, json - and to Python files that fail to parse (syntax errors, notebook magics).

## How it works

A line scanner tracks quote state (`'`, `"`, backtick, with escapes) and the language's comment syntax (`//`, `#`, `--`, `/* */` per extension), producing for each line: the code region, the string regions, and the comment region. Rules are then scoped:

- Comments are prose: emoji auto-removed, U002 joins consecutive full-line comment runs at the same indent (`//`, `#`, `--`).
- Strings are behavior: emojis inside string literals are reported as manual, never removed.
- Code regions: smart quotes / typographic dashes straightened (U007) - in JS this can turn a file that does not even parse (curly quotes pasted as delimiters) back into valid code.
- Universal whitespace rules (U003, U004, U005, U008 as warning, U009) apply to the whole file.

JSON gets only the structural rules (no comment syntax, strings respected). Shebang lines are never modified.

## Known limitations (by design, keep them in mind when reporting)

- Inside block comments (`/* ... */`) continuation prose is not joined by U002; only runs of full-line `//` / `#` / `--` comments are. If a block comment is badly wrapped, propose the edit manually.
- No naming / import-order / definition-spacing rules outside Python. If the project clearly follows a convention (e.g. camelCase in JS), violations of it are out of scope for the checker - mention them conversationally if blatant, but do not present them as ruleset violations.
- P003 comma spacing is Python-scoped; for other languages defer to the project's formatter (prettier, gofmt, rustfmt). In general, when a language has an authoritative formatter configured in the repo, defer to it for the rules it covers and run this ruleset only for what it does not (emoji, prose breaks, CRLF).

## Verification step

For languages with a cheap syntax check, run it after fixing: `node --check file.js`, `bash -n script.sh`, `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" file.yaml` (if PyYAML is available). This catches pre-existing breakage and proves the fixes were safe.
