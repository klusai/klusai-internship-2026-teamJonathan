# Exercise 5 — Reranking, contextual retrieval & grounded answers

**Topic:** the accuracy techniques that sit on top of retrieval — LLM reranking and
contextual retrieval — plus the generation half of RAG: a grounded answer with
citations, served from a prompt-cached corpus.

## Goal

Three short capstone tasks that turn good retrieval into good answers:

- **Rerank** mis-ordered candidates with Claude so the right section reaches rank 1.
- **Contextualize** a chunk that lost its meaning when split, so it becomes findable.
- **Generate** an answer grounded in the corpus, with citations on and the corpus
  cached (the surrounding API features from the course).

## What's here

```
ex5_rerank_contextual/
  rerank.py                  LLM reranking of mis-ordered candidates (TODO: the rerank prompt)
  contextual.py              add situating context to a naked chunk (TODO: the context prompt)
  answer_with_citations.py   grounded answer + citations + prompt caching (TODO: the document block)
  ../corpus/                 the shared corpus + queries
```

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python rerank.py
python contextual.py
python answer_with_citations.py
```

## Tasks

1. **Reranking (`rerank.py`).** Write `RERANK_SYSTEM` so Claude reorders candidates by
   what actually answers the query's intent, not word overlap. Record gold-at-rank-1
   before vs after; "after" should beat "before".

2. **Contextual retrieval (`contextual.py`).** Write `context_prompt` so Claude returns
   one situating sentence for the naked chunk. Confirm the added context names the
   chunk's topic (so "who issued hardware security keys?" can now match it).

3. **Grounded answer (`answer_with_citations.py`).** Complete `build_document_block` to
   serve the corpus as a document with **citations enabled** and a **cache_control**
   breakpoint. Confirm the answer carries citation spans, and run it twice to watch
   `cache_read_input_tokens` jump on the second call.

## Acceptance criteria

- [ ] Reranking moves the gold section to rank 1 on the mis-ordered candidates
      (after > before).
- [ ] The contextualized chunk's added sentence names the security topic.
- [ ] The grounded answer returns at least one citation; the corpus is cached
      (cache tokens created on call 1, read on call 2).

## Stretch goals

- Rerank the *full* hybrid top-5 from ex4 and measure recall@1 before vs after.
- Contextualize every chunk, re-run ex2/ex3, and measure the recall lift from
  contextual retrieval.
- In `answer_with_citations.py`, ask a question the corpus can't answer and confirm the
  model declines rather than fabricating a citation.

## Self-check

- Reranking adds an LLM call to every query — when is that latency worth it, and when
  would you skip it?
- Contextual retrieval costs one LLM call per chunk at index time. Why is that a
  one-time cost you usually accept, unlike reranking's per-query cost?
- Why do citations matter specifically for RAG, where the model is summarizing
  retrieved text rather than answering from memory?
