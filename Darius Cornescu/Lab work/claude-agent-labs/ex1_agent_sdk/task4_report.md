# task4 — subagent orchestration: stitched report

Produced by running `task4_subagents.py`. The **parent** (tools: `Task`, `Read`, `Glob`)
delegated to two subagents and neither subagent had `Task`, so delegation stayed
parent-only.

- **security-reviewer** — tools `Read`, `Grep`, `Glob` (read-only). Reviewed
  `app/payments.py` and `buggy/utils.py`, returned 6 findings.
- **test-writer** — tools `Read`, `Write`, `Bash`. Wrote
  `tests/test_security_findings.py` (9 tests, one+ per finding).

## Findings (from security-reviewer)

| ID | File:line | Severity | Issue |
|----|-----------|----------|-------|
| F1 | payments.py:13 | Critical | `make_token` uses **unsalted MD5** of the PAN — reversible via rainbow tables. |
| F2 | payments.py:16-20 | High | `charge` handles money as **float** — precision loss (`0.1+0.2 != 0.3`). |
| F3 | payments.py | High | **No card_number validation** — `""` is accepted; `None` raises a raw `AttributeError`. |
| F4 | payments.py:17 | Medium | **NaN/Infinity bypass** the `amount <= 0` guard (`nan <= 0` is `False`). |
| F5 | utils.py:8-11 | Low | `calculate_average([])` returns `0.0` instead of raising (silently hides "no data"). |
| F6 | utils.py:14-20 | Low | `get_user_name` with a **non-string name** crashes (`42.upper()`) or silently returns `""` (`0`). |

## Tests (from test-writer) + execution result

`tests/test_security_findings.py` encodes each finding as the *desired secure behavior*,
so a **FAIL confirms the bug**. The test-writer's sandboxed Bash could not invoke
`python`/`pytest`, so the suite was executed in the host environment:

```
9 failed in 0.15s
F1 token == raw MD5                          -> FAIL (bug confirmed)
F2 amount != Decimal('0.30')                 -> FAIL (float money)
F3 charge(10,"") / charge(10,None)           -> FAIL (no validation)
F4 charge(nan|inf,...) not rejected          -> FAIL (guard bypass)
F5 calculate_average([]) returns 0.0         -> FAIL (should raise)
F6 name=42 -> AttributeError; name=0 -> ""   -> FAIL (should TypeError)
```

## Verdict

Delegation, tool-boundary, and Task-in-parent-only contracts all held. The security
review + failing tests together confirm **6 issues**, the most serious being F1
(unsalted MD5 tokenization) — which is the 4th original bug left unfixed by task1 and is
hardened in the follow-up commit. Note: the test-writer *wrote* correct tests but could
not *run* them in its sandbox; execution evidence was gathered on the host.
