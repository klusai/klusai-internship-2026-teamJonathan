---
name: code-review
description: Reviews a diff or file for bugs, style issues, security risks, and maintainability concerns, returning prioritized, actionable feedback with suggested fixes. Use when the user asks to review code, check a diff, audit a file, or find issues before merging.
---

You are performing a thorough code review. Follow these steps:

## 1. Gather the diff

If reviewing staged/unstaged changes:
```
git diff HEAD
```

If reviewing a specific file passed as an argument (`$ARGS`):
- Read the file directly.

If reviewing a branch diff:
```
git diff main...HEAD
```

## 2. Analyze for the following categories

For each finding, assign a severity: **Critical**, **Major**, or **Minor**.

- **Bugs**: logic errors, off-by-one errors, unhandled edge cases, incorrect conditionals, null/undefined dereferences.
- **Security**: SQL injection, XSS, command injection, hardcoded secrets, insecure deserialization, missing auth checks, path traversal.
- **Style**: naming inconsistencies, dead code, commented-out code, overly complex expressions, missing or misleading variable names.
- **Maintainability**: functions doing too much, missing error handling at system boundaries, magic numbers/strings without constants, duplicated logic that should be extracted.

## 3. Output format

List findings grouped by severity, most critical first. For each finding:

```
[SEVERITY] file.ext:line — Short description
  Problem: explain what is wrong and why it matters.
  Fix: concrete suggestion or corrected code snippet.
```

If no issues are found in a category, omit that category.

End with a one-sentence summary of the overall code quality and whether the change is safe to merge.

## Notes
- Do not flag issues that are already handled correctly.
- Do not suggest adding comments that explain obvious code.
- If `$ARGS` contains `--fix`, apply the suggested fixes directly to the files after reporting.
- If `$ARGS` contains `--comment`, post findings as inline PR review comments using the GitHub MCP tools.
