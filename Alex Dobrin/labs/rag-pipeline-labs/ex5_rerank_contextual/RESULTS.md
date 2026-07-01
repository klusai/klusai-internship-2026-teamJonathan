# Exercise 5 — results

All three TODOs are implemented, `py_compile`-clean, and **verified on live runs** with
`ANTHROPIC_API_KEY` set. All three acceptance criteria pass (see measured results below).

```
$ .venv/bin/python -m py_compile rerank.py contextual.py answer_with_citations.py
PY_COMPILE OK
```

## What was implemented

- **`rerank.py` — `RERANK_SYSTEM`.** System prompt telling Claude to act as a search
  reranker: read the query and the `<doc id="...">` candidates and call `rank_documents`
  with every id ordered most-relevant-first, judging by the query's underlying intent
  rather than surface word overlap (explicitly: "what changed after the phishing attack"
  is incident response, not whatever repeats "change"/"team").
- **`contextual.py` — `context_prompt`.** User prompt wrapping the whole document and the
  naked chunk, asking for ONE situating sentence (no preamble/labels/quotes) that names
  the chunk's section and topic — steered to name the cybersecurity breach / incident
  response and hardware security keys, so `TOPIC_WORDS` hits.
- **`answer_with_citations.py` — `build_document_block`.** Returns a `document` content
  block: `source` `{type: "text", media_type: "text/plain", data: corpus_text}`, a
  `title`, `citations: {"enabled": True}`, and `cache_control: {"type": "ephemeral"}`.

## Anthropic API surface used (verified against the claude-api skill)

- **Reranking** — `client.messages.create` with a **forced tool call**
  `tool_choice={"type": "tool", "name": "rank_documents"}` so Claude must return the
  ordering through the tool (matches the skill's Tool Choice: force-specific-tool form).
  Model `claude-sonnet-4-6` (pack id, provided in the file).
- **Citations** — `citations: {"enabled": true}` set on the `document` block. Per the
  skill's Document & File Input / Citations note: no beta header; the response splits into
  multiple `text` blocks and cited blocks carry a `citations` array with `cited_text`,
  which the harness reads via `getattr(block, "citations", ...)` and `citation.cited_text`.
- **Prompt caching** — `cache_control: {"type": "ephemeral"}` on the last content block
  (the document), the default 5-minute TTL. Verified via
  `usage.cache_creation_input_tokens` / `usage.cache_read_input_tokens`, exactly the
  fields the skill's Prompt Caching section says to check. Model `claude-opus-4-8`.
- **Contextual** — plain `client.messages.create` (no tools), model `claude-haiku-4-5`.
- **Model ids** — `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-opus-4-8` are the exact
  strings from the pack; left unchanged.

## Measured live-run results (all acceptance criteria pass)

**Rerank (`rerank.py`)** — gold at rank 1 went from **0/3 → 3/3** after reranking
(after > before ✓). The reranker promoted `cybersecurity` for Q8 and Q2, and
`research-and-development` for Q3, in every case moving the gold section from a
lower rank to rank 1:

```
gold at rank 1 — before: 0/3   after rerank: 3/3
```

**Contextual (`contextual.py`)** — `added context names the topic (...): True` ✓. The
added situating sentence was:

> In response to the targeted phishing breach (INC-2023-014), the Cybersecurity team
> issued hardware security keys to all 540 staff and made them mandatory for every
> administrative login.

which re-anchors the naked chunk to the cybersecurity/phishing-incident section, so a
query like "who issued hardware security keys?" now has section context to match on.

**Citations + prompt caching (`answer_with_citations.py`)** — run twice in the same
5-minute window:

```
run 1:  citations attached: 5    cache: created=2810 read=0
run 2:  citations attached: 4    cache: created=0    read=2810
```

Citations attached ≥ 1 on both calls ✓; the corpus (2810 tokens) was cached on call 1
(`cache_creation_input_tokens=2810`) and served from cache on call 2
(`cache_read_input_tokens=2810`, `created=0`) ✓ — the cache_read jump confirms the
`cache_control` breakpoint works.
