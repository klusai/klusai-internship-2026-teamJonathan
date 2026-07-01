# RAG Pipeline Labs

A hands-on lab pack that builds a retrieval-augmented generation (RAG) pipeline end to
end, one technique per exercise. Same shape as the other `labs/` packs: each exercise
has its own `README.md` (goal, tasks, acceptance criteria, stretch goals), starter code
with `TODO` markers, and shared fixture data. `instructor/` holds the answer key,
rubric, and gold labels.

Every exercise retrieves over one shared document — `corpus/corpus.md`, a fictional
company annual report — and is graded on the same evaluation queries in
`corpus/queries.json`. The relevance oracle is deliberately simple: a retrieved chunk
counts as relevant to a query if it contains the query's `answer_contains` string, so
recall@k is comparable across chunking and search strategies.

## The five exercises

| # | Folder | Topic |
|---|--------|-------|
| 1 | `ex1_chunking/` | Chunking strategies — size-based windows, the overlap trick, structure-based sections; measure what survives intact. |
| 2 | `ex2_embeddings_search/` | Embeddings & semantic search — cosine similarity, a vector index, recall@k (Voyage embeddings). |
| 3 | `ex3_bm25/` | BM25 lexical search — idf + term-frequency saturation + length normalization; the rare-term win. |
| 4 | `ex4_hybrid_rrf/` | Hybrid retrieval — fuse lexical + semantic rankings with Reciprocal Rank Fusion; beat both single methods. |
| 5 | `ex5_rerank_contextual/` | Reranking, contextual retrieval, and grounded answers with citations + prompt caching. |

## The pipeline these build

```
            ex1            ex2 / ex3 / ex4              ex5
   document ────► chunks ────► retrieve top-k ────► rerank ──► grounded answer
   (corpus.md)   (chunking)   (semantic / BM25 /    (LLM)      (+ citations,
                              hybrid RRF)                       prompt cache)
                                   ▲
                              ex5 contextual retrieval improves what's indexed
```

## Prerequisites

- **Python 3.11+** (the code uses 3.10+ syntax such as `X | None`).
- An **Anthropic API key** for ex5: `export ANTHROPIC_API_KEY=sk-ant-...`
- A **Voyage API key** for ex2 (embeddings; separate from Anthropic, free tier):
  `export VOYAGE_API_KEY=...`
- ex1, ex3, and ex4 are **pure Python** — no API key needed, fully offline-gradeable.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate

pip install anthropic     # ex5
pip install voyageai      # ex2 (embeddings)

export ANTHROPIC_API_KEY=sk-ant-...
export VOYAGE_API_KEY=...
```

Each exercise README lists exactly what it needs at the top.

## Model ids used in this pack

`claude-opus-4-8` (default), `claude-sonnet-4-6`, `claude-haiku-4-5`, and `voyage-3`
for embeddings. Each harness picks a sensible default and tells you where to swap.

## Suggested order & timing (~2.5–3 hours)

| Order | Exercise | Time | Why here |
|------:|----------|------|----------|
| 1 | **ex1 — Chunking** | ~25 min | The first decision; everything downstream depends on it. Offline. |
| 2 | **ex3 — BM25** | ~35 min | Lexical search from scratch; the rare-term baseline. Offline. |
| 3 | **ex2 — Embeddings** | ~30 min | Semantic search; the paraphrase win BM25 can't make. (Needs Voyage.) |
| 4 | **ex4 — Hybrid + RRF** | ~30 min | Fuse the two; the headline "hybrid beats both" result. Offline. |
| 5 | **ex5 — Rerank / contextual / citations** | ~45 min | The accuracy layer and the generation half. (Needs Anthropic.) |

(ex2 is placed after ex3 so you meet the lexical baseline first, but it only needs the
Voyage key — do it whenever your key is ready.)

## A note on API specifics

The Anthropic surface (messages, `tool_use` + forced `tool_choice`, citations on a
document block, `cache_control`) and the BM25 / RRF / cosine math were verified against
current docs when this pack was built. The **Voyage** embedding SDK (ex2) is a
non-Anthropic dependency and is flagged inline with `⚠️` — verify the client, `embed`
call, and `MODEL` against your installed `voyageai`. ex1, ex3, and ex4 depend on no
external service and grade fully offline.
