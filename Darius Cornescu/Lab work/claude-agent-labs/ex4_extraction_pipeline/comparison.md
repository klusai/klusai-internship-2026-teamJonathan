# extract.py (synchronous) vs batch.py (Message Batches API)

## What each does
- **`extract.py`** — one synchronous `messages.create` per invoice, with a
  validate-and-retry loop (jsonschema; on `ValidationError` it feeds a `tool_result`
  with `is_error: True` back to the model and retries up to 3×). Interactive: you get a
  validated result in seconds, and each doc can self-correct.
- **`batch.py`** — submits all six invoices as ONE asynchronous batch
  (`client.messages.batches.create`), polls `processing_status` until `ended`, then
  streams `results(id)`. No per-item retry (a validation failure is recorded to
  resubmit later), and results arrive together after the whole batch finishes.

## Cost
The **Message Batches API is ~50% of the token cost** of the equivalent synchronous
calls (both input and output tokens are discounted). For 6 invoices the saving is tiny;
across thousands it is the dominant reason to batch.

## Latency / throughput
- **Synchronous:** ~1 round-trip per invoice, results in seconds — but you pay full
  price and drive concurrency yourself.
- **Batch:** a single submission covers all items, but completion is asynchronous —
  anywhere from a couple of minutes to **up to ~24h** (SLA), typically minutes for a
  small batch. You trade latency for throughput and cost.

## Verified aggregate (from extract.py on the six fixtures)
- All six validate against `INVOICE_SCHEMA`.
- `tax_id: null` on **inv_03 (Sunrise Bakery)** and **inv_05 (Maria Lopez)**; the other
  four carry real ids. The nullable-and-optional `tax_id` design lets the model return
  `null` (never a fabricated id) without a validation error.
- **Sum of all totals = 10721.49** (249.00 + 18.50 + 114.00 + 7999.99 + 1000.00 + 1340.00).

## When to pick each
- **Batch** — bulk/offline extraction, nightly jobs, backfills, anything where a
  minutes-to-hours delay is fine and the 50% cost cut matters.
- **Synchronous** — interactive/single-document flows, anything a user is waiting on, or
  when you need the per-item validate-and-retry self-correction loop.
