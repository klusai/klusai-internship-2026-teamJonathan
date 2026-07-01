# Cost / throughput comparison — `extract.py` vs. `batch.py`

Extracting the same 6 invoices two ways. Model: `claude-opus-4-8`
($5.00 / MTok input, $25.00 / MTok output). Measured by driving the real
`extract.extract_one()` loop six times in sequence and submitting the real
`batch.build_requests()` payload as one Message Batch.

## Measured numbers

| Metric                | Sequential (`extract.py` ×6) | Batch (`batch.py`) |
| --------------------- | ---------------------------: | -----------------: |
| Wall-clock time       | **24.44 s** (~4 s / invoice) | **115.78 s**       |
| API calls             | 6 synchronous                | 1 batch of 6       |
| Input tokens          | 6,116                        | 6,116              |
| Output tokens         | 1,856                        | 1,857              |
| Token cost (full)     | $0.07698                     | $0.077005          |
| **Billed cost**       | **$0.07698**                 | **$0.038503**      |
| Validated OK          | 6 / 6                        | 6 / 6              |
| `tax_id: null`        | inv_03, inv_05               | inv_03, inv_05     |

Token counts are effectively identical (same prompt, same tool, same 6
documents) — the only cost lever is the per-token rate.

## How much cheaper is the batch?

**50% cheaper.** The Batches API bills every token at half the synchronous
rate. Same work, same tokens: $0.077 → **$0.0385**, a saving of ~$0.0385 on
this 6-invoice run. The discount is purely on token price, so it scales
linearly: at 10,000 invoices the same 50% applies (~$64 vs ~$128 here).

## How does latency differ?

Opposite trade-off from cost:

- **Sequential** is fast and predictable: 6 blocking calls, ~4 s each,
  ~24 s total. You get each result the moment it returns, and a validation
  failure can be retried in-line immediately (the `extract.py` retry loop).
- **Batch** is slow to first result but cheap: one async submit, then poll
  until `ended`. This run took **115.78 s** — already ~5× the sequential
  wall-clock for only 6 tiny documents, because of fixed queue/scheduling
  overhead. The API only guarantees completion **within 1 hour** (24 h hard
  max), and there is **no per-item retry** — a failed item is one you note and
  resubmit in a new batch.

So sequential wins on latency for small N; batch's overhead is fixed, so it
amortizes and its throughput advantage only shows up at large N where you'd
otherwise pay for thousands of serial round-trips.

## When would you choose each?

| Choose **sequential** (`extract.py`) when… | Choose **batch** (`batch.py`) when… |
| ------------------------------------------ | ----------------------------------- |
| A user is waiting on the result (interactive, single-doc) | Bulk / offline work where minutes-to-an-hour of latency is fine |
| You need the answer in seconds             | You want the 50% cost cut and don't need results now |
| You want immediate, in-line validate-and-retry | Volume is large enough that serial round-trips would dominate cost/time |
| Volume is low (a handful of docs)          | Overnight or scheduled bulk runs over hundreds/thousands of invoices |

**Rule of thumb:** interactive single-document extraction → `extract.py`;
overnight bulk extraction → `batch.py` for the half-price tokens, accepting the
up-to-an-hour latency and no per-item retry.
