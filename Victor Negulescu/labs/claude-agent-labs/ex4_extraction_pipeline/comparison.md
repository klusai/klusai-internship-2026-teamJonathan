# Batches API vs. Synchronous Calls — Comparison

## Cost

The Batches API costs **50% less per token** compared to synchronous API calls.
For 6 invoices processed with `claude-opus-4-8`, this roughly halves the extraction
cost with no change to the prompt, tools, or schema.

## Latency

| Approach | Latency |
|---|---|
| Synchronous (6 sequential calls) | Seconds — results arrive immediately |
| Batches API | Up to ~1 hour — results are polled until the batch ends |

The trade-off is direct: batches are much cheaper but you give up immediate results.

## When to use each

**Use synchronous extraction** when:
- The user is waiting for the result interactively (e.g. "extract this invoice now")
- You need the structured data to drive the next step in real time
- You are processing a single document

**Use the Batches API** when:
- You have a large set of documents to process in bulk (end-of-day, nightly job)
- Cost matters more than turnaround time
- Individual failures can be noted and resubmitted rather than blocking the workflow

## Resubmission note

The Batches API has no per-item retry: if one invoice fails validation, you collect
it from `failures` and resubmit it in a new batch. With synchronous extraction,
`extract.py` retries within the same request via the tool-result feedback loop.
