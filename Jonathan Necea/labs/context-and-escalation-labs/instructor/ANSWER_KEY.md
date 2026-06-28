# Answer Key — Exercises 6 & 7

Instructor reference for these add-on exercises (ex6-ex7). Expected solution per
task plus the gotchas to watch for. Model ids: `claude-opus-4-8`,
`claude-sonnet-4-6`, `claude-haiku-4-5`.

---

## Exercise 6 — Context management

### task1 — extract facts

The `SYSTEM` prompt must tell the model to read the log and call `report_log_facts`
with **only** the load-bearing facts, dropping the pip output, the wall of PASSED
lines, the warnings, and the coverage table — and to never invent a number.

Expected summary (see `gold_facts.json`): `outcome=failed`, `tests_total=42`,
`tests_passed=39`, `tests_failed=2`, `tests_skipped=1`, and the two failures —
`tests/test_auth.py::test_token_expiry` (KeyError) and
`tests/test_payments.py::test_charge_rejects_negative` (AssertionError). Capturing
`duration_seconds=12.84` is a bonus.

The measurement is the teaching point: the raw log is on the order of ~900-1,100
tokens; the JSON summary is on the order of ~80-120 tokens — roughly a 10x reduction
with no loss of what matters. **Both numbers must be recorded.**

Watch for: inventing a third failure or a wrong count; listing passing tests;
forgetting the skipped test; reporting `ValueError` for the second failure (that was
the *expected* exception in the original assertion — the gold error type is
`AssertionError`).

### task2 — scratchpad

- `append_finding` opens the scratchpad in append mode and writes exactly one line
  per record (e.g. `- P1  #1  checkout fully down`).
- `synthesize` reads `scratchpad.md` **only** (never the raw records) and asks for a
  short shift summary — counts per severity and which incidents are P1.
- Severities must match `gold_triage.json`: P1 = {1, 6, 9}, P2 = {2, 4, 7, 11},
  P3 = {3, 5, 8, 10, 12} (3 / 4 / 5).

The measurement: the scratchpad per-step token counts are **flat** (each step sends
one record plus the fixed prompt), while the naive per-step counts **climb** (each
step re-sends every prior record). The final synthesis reads the small scratchpad,
not the ~12 raw records. Both totals must be recorded.

Watch for: passing previously-seen records into a per-record call — that quietly
restores the growing-context problem the exercise is about; `synthesize` reading the
records instead of the scratchpad (defeats the point).

### task3 — delegate discovery

The `code-scout` prompt must trace the **live** policy — `client/http.py` reads
`config.settings.MAX_RETRIES` — and return one compact line: the value (`5`), the
file:line where it's defined (`config/settings.py`, the `MAX_RETRIES = 5` line), and
that `client/http.py` reads it. It must NOT paste file contents back.

The parent has `allowed_tools=["Task"]` and no Read/Grep/Glob, so it cannot read
`repo/` itself — its context only ever holds the scout's short answer. Expected
report: retry limit `5`, defined in `config/settings.py`.

Watch for: a scout that greps `retries`, hits the legacy `retries = 3` first, and
reports `3` (the decoy — see `gold_discovery.json`); a parent that has file tools and
reads the repo itself (misses the isolation point). Per the ex1 convention: if the
installed SDK names the delegation tool `"Agent"` rather than `"Task"`, swapping it is
correct, not a deduction.

---

## Exercise 7 — Escalation & human-in-the-loop

### task1 — escalation triggers

The `POLICY` must define HANDLE vs ESCALATE and the four triggers precisely,
including the authority limits. With the empty policy, expect mislabels on the
borderline cases (often 3, 5, 6, 8, 9). With a good policy, all 10 non-debatable
cases route correctly. Decision **and** trigger must both match the inline gold in
`scenarios.json`.

The non-debatable gold (rationales in `gold_escalation.json`):
1 HANDLE/none, 2 ESCALATE/user_request, 3 ESCALATE/policy_gap, 4 HANDLE/none,
5 ESCALATE/no_progress, 6 ESCALATE/policy_gap, 7 HANDLE/none, 8 ESCALATE/no_progress,
9 ESCALATE/policy_gap, 10 HANDLE/none. Cases 11 and 12 are debatable — see the
accept lists; never count them against the student. Record the empty-policy accuracy
and the real-policy accuracy; the second should be higher.

Watch for: tagging case 2 as policy_gap instead of user_request (the user *asked* for
a human — that trigger wins); calling case 3/6/9 HANDLE; over-escalating the plain
FAQ cases (1, 4, 7, 10).

### task2 — confidence routing

`route()` implements two rules:

```python
def route(confidence, action_type):
	if confidence >= AUTO_THRESHOLD:      base = "AUTO"
	elif confidence >= REVIEW_THRESHOLD:  base = "REVIEW"
	else:                                 base = "ESCALATE"
	if action_type in HIGH_RISK and base == "AUTO":
		base = "REVIEW"   # guardrail: high-risk is never AUTO
	return base
```

It must pass all 12 `ROUTE_CASES` (mirrored in `gold_routing.json`). The
guardrail rows are the ones that matter: `(0.99, refund)`, `(0.85, delete_account)`,
`(0.90, refund)` are all REVIEW, not AUTO. Note the asymmetry: the guardrail only
overrides AUTO → REVIEW; a low-confidence high-risk action stays ESCALATE (stricter),
e.g. `(0.55, send_external_email)` and `(0.30, delete_account)`.

In Part B, the live model usually rates the safe tasks (1-4) high and the risky ones
(5-8) lower — but even if it rates a refund 0.95, the guardrail must show REVIEW.

Watch for: flipping the boundary inclusivity (0.85 and 0.60 are inclusive); applying
the guardrail to ESCALATE (it should remain ESCALATE); raising a low-confidence
high-risk action up to REVIEW (wrong direction).

### task3 — HITL gate

`requires_approval(tool_name)` returns `tool_name in HIGH_RISK_TOOLS`. Read-only
tools (`lookup_order`, `get_account`) return False and run automatically; the three
high-risk tools require `approve(...)`.

Expected run: the agent looks up the order (AUTO-RAN), then proposes `issue_refund`
and/or `delete_account`, which are gated. With the default (deny) they show DENIED in
the audit and the agent tells the customer the action was sent for review. With
`HITL_AUTO=allow` they show APPROVED+RAN. Either way the final check —
`high-risk tools that ran WITHOUT approval` — must be empty.

Watch for: gating the read-only tools too (over-restrictive); relying only on the
prompt rather than the gate (the whole point is that the gate holds even if the model
ignores the prompt). The Agent SDK `can_use_tool` mapping at the bottom of the file
is flagged: reward a correct port even if the return type differs from the SDK
version, exactly as ex1 treats the session helpers.
