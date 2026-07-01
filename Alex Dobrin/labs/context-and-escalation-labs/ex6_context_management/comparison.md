# Task 1 — Context Compression Comparison

Distilling a verbose CI log down to only its load-bearing facts, then carrying
the small structured summary forward instead of the raw log.

- **Model:** `claude-haiku-4-5`
- **Source:** `fixtures/verbose_log.txt`
- **Method:** one forced `report_log_facts` tool call; token counts via
  `messages.count_tokens` (no inference billed for the counts).

## Token comparison

| Measure          | Tokens | Share of raw |
| ---------------- | -----: | -----------: |
| Raw log          |  2015  |       100.0% |
| Distilled summary |   160  |         7.9% |
| **Reduction**    | **1855** | **−92.1%** |

The summary costs **~12.6×** fewer tokens than the raw log to keep in context.

## Extracted summary

```json
{
  "outcome": "failed",
  "tests_total": 42,
  "tests_passed": 39,
  "tests_failed": 2,
  "tests_skipped": 1,
  "duration_seconds": 12.84,
  "failures": [
    {
      "test": "tests/test_auth.py::test_token_expiry",
      "error_type": "KeyError"
    },
    {
      "test": "tests/test_payments.py::test_charge_rejects_negative",
      "error_type": "AssertionError"
    }
  ]
}
```

## Fidelity check (vs. the gold facts)

Every load-bearing fact survived the compression — nothing dropped, nothing
invented.

| Field             | Expected | Extracted | Match |
| ----------------- | -------- | --------- | :---: |
| outcome           | failed   | failed    | ✅ |
| tests_total       | 42       | 42        | ✅ |
| tests_passed      | 39       | 39        | ✅ |
| tests_failed      | 2        | 2         | ✅ |
| tests_skipped     | 1        | 1         | ✅ |
| duration_seconds  | 12.84    | 12.84     | ✅ |
| failure 1         | test_token_expiry / KeyError | same | ✅ |
| failure 2         | test_charge_rejects_negative / AssertionError | same | ✅ |

## What got dropped (the noise)

The 92% reduction comes from discarding everything that wasn't load-bearing:

- pip / dependency-resolver install chatter
- the wall of 39 `PASSED` lines and progress percentages
- the full `FAILURES` tracebacks (kept only test id + error class)
- the `DeprecationWarning` summary
- the coverage table

## Takeaway

A single cheap extraction call replaces a 2015-token log with a 160-token
structured fact set that an agent can carry forward indefinitely — preserving
the outcome, the counts, and the two real failures while shedding the noise that
would otherwise crowd out the rest of the context window.

---

# Task 2 — Scratchpad as External Memory

Triaging 12 incident reports. Each record is processed in its OWN independent
call, with a one-line finding appended to a scratchpad file. That file — not a
growing conversation — is the memory, so per-step cost stays O(1) and the final
synthesis reads the tiny scratchpad instead of all 12 raw records.

- **Model:** `claude-haiku-4-5`
- **Source:** `fixtures/triage_records.json` (12 records)
- **Scratchpad:** `scratchpad.md` (one markdown line per finding)
- **Method:** per-record forced `triage` tool call; token counts via
  `messages.count_tokens`.

## Per-step input tokens — flat vs. climbing

| Step | Scratchpad (flat) | Naive (climbing) |
| ---: | ----------------: | ---------------: |
|  #1  |  150 |  150 |
|  #2  |  116 |  246 |
|  #3  |   87 |  313 |
|  #4  |  116 |  409 |
|  #5  |   94 |  483 |
|  #6  |  118 |  581 |
|  #7  |  107 |  668 |
|  #8  |   94 |  742 |
|  #9  |  112 |  834 |
| #10  |   83 |  897 |
| #11  |  114 |  991 |
| #12  |   83 | 1054 |

The scratchpad path sends the same fixed prefix plus exactly one record each
call, so it never grows. The naive path re-sends every prior record, so step #12
costs **7×** what step #1 did and keeps climbing with each new record.

## Totals across the 12 steps

| Path        | Total input tokens | Share |
| ----------- | -----------------: | ----: |
| Scratchpad  |  **1274**          | 17.3% |
| Naive       |  **7368**          | 100%  |

The scratchpad path costs **~5.8× fewer** input tokens over the run — and the
gap widens with every additional record, since the naive cost grows
quadratically (each new record is re-read by every later step).

## Final synthesis cost

| Synthesis reads        | Tokens | Share |
| ---------------------- | -----: | ----: |
| Scratchpad alone       |  **272** | 26.1% |
| Re-reading 12 records  | **1042** | 100%  |

The end-of-shift summary is produced from a 272-token scratchpad instead of the
1042 tokens the raw records would cost — **~3.8× cheaper** — with no loss of the
facts that matter (3 P1, 4 P2, 5 P3; P1s are #1, #6, #9).

## Takeaway

Offloading each finding to a scratchpad file turns a cost that grows with every
record into a flat per-step cost, and lets the final synthesis read a small
digest rather than the full history. With only 12 records the scratchpad path
already costs 5.8× less in total and reads 3.8× less at synthesis; the advantage
compounds as the record count grows.
