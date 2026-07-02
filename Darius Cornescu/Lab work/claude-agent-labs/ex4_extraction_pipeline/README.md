# Exercise 4 — Build a data-extraction pipeline

**Topic:** `tool_use` with JSON schemas, validation/retry loops, optional/nullable
fields, and batch processing via the Message Batches API.

## Goal

Extract structured invoice data reliably: the model returns data by calling a tool,
you validate it against a JSON schema, and you feed validation errors back so the
model self-corrects. Then run the same extraction over all 6 invoices as a single
batch and compare cost and throughput.

## What's here

```
ex4_extraction_pipeline/
  schema.py        INVOICE_SCHEMA (required: vendor, total, line_items; tax_id nullable) + EXTRACT_TOOL
  extract.py       single-doc extraction with a jsonschema validate/retry loop  (has TODOs)
  batch.py         all 6 invoices via the Message Batches API: submit, poll, validate, aggregate  (has TODOs)
  invoices/        inv_01..inv_06 — plain-text invoices; inv_03 and inv_05 have NO tax id
```

## Setup

```bash
pip install anthropic jsonschema
export ANTHROPIC_API_KEY=sk-ant-...
```

## Tasks

1. **Finish the retry loop** in `extract.py`. Validate the tool output against
   `INVOICE_SCHEMA`; on failure, append a `tool_result` (with `is_error: true`) that
   explains the problem and loop again. Run it on `inv_03.txt` and confirm `tax_id`
   comes back as `null` (not invented) and validation still passes.

2. **Prove the nullable field.** Run `extract.py` on all six invoices. inv_03 and
   inv_05 must produce `tax_id: null`; the others must produce a real id. If the
   model ever fabricates a tax id, tighten the tool description / system prompt.

3. **Finish `batch.py`.** Complete the validate-and-aggregate step. Submit all six
   in one batch, poll to completion, validate each result, and print: how many
   succeeded, the sum of totals, and which invoices had no tax id.

4. **Cost / throughput comparison.** Write a short note (`comparison.md`) answering:
   - How much cheaper is the batch (hint: Batches API = 50% off token cost)?
   - How does latency differ (6 sequential synchronous calls vs. one batch that may
     take up to an hour)?
   - When would you choose each? (interactive single-doc vs. overnight bulk)

## Acceptance criteria

- [ ] `extract.py` validates output and retries on failure with the error fed back.
- [ ] inv_03 and inv_05 → `tax_id: null`; inv_01/02/04/06 → a real tax id; all six
      validate against the schema.
- [ ] `batch.py` submits all six, polls to `ended`, validates, and aggregates.
- [ ] `comparison.md` states the cost delta, the latency trade-off, and when to pick
      each path.

## Stretch goals

- Add a `line_items` cross-check: assert the sum of line-item `amount`s is within a
  cent of `total`; feed mismatches back as a validation error.
- Add prompt caching for the shared system prompt across the batch.
- Add a 7th invoice that is intentionally malformed and confirm the retry loop (or
  the batch failure path) handles it without crashing.

## Self-check

- Why validate at all, when the tool's `input_schema` already constrains the shape?
  (What does `jsonschema` catch that the tool call doesn't always?)
- Why is `tax_id` *nullable* rather than just *optional*? What would break if you
  made it required?
