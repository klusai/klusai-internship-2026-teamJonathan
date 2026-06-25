# Rubric — Claude Agent Labs

**Total: 100 points — 20 per exercise.** Partial credit is fine; the per-task points
below sum to 20 for each exercise. A passing grade is ≥ 70.

---

## Exercise 1 — Claude Agent SDK (20 pts)

| Pts | Criterion |
|----:|-----------|
| 5 | **task1** — agent fixes all four bugs (utils ×2, payments ×2) via Edit, and the run streams reasoning → tool → result. |
| 5 | **task2** — recognizes `max_budget_usd` doesn't exist; bounds work with `max_turns` and enforces a ceiling using `total_cost_usd`; failure collapses to one structured log line. |
| 5 | **task3** — captures `session_id` and resumes successfully (recalls "42"); rename/tag/list either works or is correctly documented as version-dependent. |
| 5 | **task4** — two subagents with the right tool sets; `Task` only in the parent; one stitched Findings+Tests report. |

---

## Exercise 2 — Claude Code config (20 pts)

| Pts | Criterion |
|----:|-----------|
| 4 | Precedence order written correctly (enterprise → project → user → path rules). |
| 4 | Tabs-vs-spaces conflict resolved as **tabs**, with the project-scope reason stated. |
| 4 | `frontend` rule flags `console.log`; `backend` rule flags missing type hints; no cross-firing. |
| 4 | `SKILL.md` frontmatter: `context: fork` and `allowed-tools: [Read, Write]`; explains how Bash is blocked. |
| 4 | One MCP server wired with captured evidence it loaded. |

---

## Exercise 3 — MCP tools (20 pts)

| Pts | Criterion |
|----:|-----------|
| 6 | Both tool descriptions rewritten to disambiguate (when-to-use, the argument, an example, what it's not for). |
| 6 | Accuracy improves from baseline to post-edit; both numbers recorded. |
| 4 | `make_error` correct: `retryable` True only for `rate_limit`; one extra category added. |
| 4 | Defensible answers for ambiguous cases 8 and 10. |

---

## Exercise 4 — Extraction pipeline (20 pts)

| Pts | Criterion |
|----:|-----------|
| 6 | `extract.py` validates with jsonschema and retries on failure with the error fed back. |
| 5 | Nullable proof: inv_03 & inv_05 → `tax_id: null`; the other four → real ids; all six validate. |
| 5 | `batch.py` submits all six, polls to `ended`, validates, aggregates (total ≈ 10721.49, no-tax set = {inv_03, inv_05}). |
| 4 | `comparison.md`: states the 50% cost saving, the latency trade-off, and when to pick each. |

---

## Exercise 5 — Prompt engineering (20 pts)

| Pts | Criterion |
|----:|-----------|
| 6 | **task1** — zero-shot and few-shot accuracies both recorded; few-shot ≥ zero-shot on the 17 non-debatable tickets. |
| 6 | **task2** — `CRITERIA` names all three issue classes; explicit runs find all three consistently; vague-run variance noted. |
| 5 | **task3** — chunk split + synthesis implemented; written single-pass vs. multi-pass comparison. |
| 3 | Correctly names all three planted issues in `big_diff.txt` with file/line. |

---

## Grading notes

- **Debatable tickets (ex5):** 8, 13, 19 — accept either label in `gold_labels.json`;
  never count them against the student. Score the other 17.
- **Unverified SDK surface (ex1):** reward investigation. If the installed
  `claude-agent-sdk` lacks `rename_session`/`tag_session`/`list_sessions`, a correct
  written explanation of the real mechanism earns the task3 points.
- **Stretch goals** are not scored but are good signal for an A+ / discussion.
