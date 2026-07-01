# Rubric — Exercises 6 & 7

**40 points total — 20 per exercise.** Partial credit is fine; per-task points sum to
20 each. A passing grade is ≥ 70% (28/40), matching the ex1–ex5 pack.

---

## Exercise 6 — Context management (20 pts)

| Pts | Criterion |
|----:|-----------|
| 7 | **task1** — summary captures `outcome=failed`, all four counts (42/39/2/1), and both real failures with their error types (KeyError, AssertionError); nothing invented. Raw-log and summary token counts both recorded. |
| 7 | **task2** — `append_finding` writes one line per record; `synthesize` reads the scratchpad only; the 12 severities match the gold (P1×3, P2×4, P3×5); per-step tokens flat for the scratchpad path and climbing for the naive path, with both totals recorded. |
| 6 | **task3** — `code-scout` returns a compact answer (value `5`, defined in `config/settings.py`); the parent delegates and never reads the files itself; the legacy `3` decoy is avoided. |

---

## Exercise 7 — Escalation & human-in-the-loop (20 pts)

| Pts | Criterion |
|----:|-----------|
| 7 | **task1** — `POLICY` written; all 10 non-debatable cases route correctly (decision **and** trigger); the empty-policy and real-policy accuracies are both recorded and the real one is higher. |
| 7 | **task2** — `route()` passes all 12 `ROUTE_CASES`, including the guardrail rows where a high-confidence high-risk action is floored to REVIEW and the low-confidence high-risk actions stay ESCALATE. |
| 6 | **task3** — `requires_approval` gates exactly the high-risk tools; the final audit shows no high-risk tool ran without approval and the read-only tool auto-ran. |

---

## Grading notes

- **Debatable cases (ex7 task1):** 11 and 12 — accept any pair in their `accept`
  list; never count them against the student. Score the other 10.
- **Unverified SDK surface:** ex6 task3 (subagent delegation tool `"Task"` vs
  `"Agent"`) and ex7 task3 (the `can_use_tool` permission callback's return type).
  Reward investigation: a working port against the installed SDK **or** a correct
  written explanation of the real mechanism earns the points, exactly as the ex1
  pack handles the session helpers.
- **The numbers are the deliverable.** ex6 is about *measured* context savings and
  ex7 task1 is about a *measured* policy delta — a student who implements the
  mechanics but records no before/after numbers has missed the point; dock the
  "recorded" half of those criteria.
- **Stretch goals** are not scored but are good signal for an A+ / discussion.
