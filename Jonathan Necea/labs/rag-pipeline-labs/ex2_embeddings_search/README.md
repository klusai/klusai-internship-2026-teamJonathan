# Exercise 2 — Embeddings & semantic search

**Topic:** turning text into vectors with an embedding model, and retrieving by cosine
similarity so meaning — not shared words — drives the match.

## Goal

Implement cosine similarity, build a vector index over the corpus sections, and measure
semantic recall@k. Confirm the win lexical search can't make: the paraphrase query
("keep employees from leaving") retrieves the *attrition* section despite zero shared
keywords.

## What's here

```
ex2_embeddings_search/
  semantic_search.py   cosine_similarity (TODO) + VectorIndex + Voyage embed + recall@k
  ../corpus/           the shared corpus + queries
```

## Setup

```bash
pip install voyageai
export VOYAGE_API_KEY=...        # Voyage is separate from Anthropic; free tier is fine
python semantic_search.py
```

The cosine self-test runs with **no key**, so you can implement and verify the core
offline; the recall run needs the Voyage key.

## ✅ Verified vs. ⚠️ flagged

- ✅ Cosine similarity + vector index retrieval are plain math, gradeable offline.
- ⚠️ The **Voyage SDK** surface (`voyageai.Client()`, `client.embed(...)`, the model
  name, `input_type`) was current when this pack was built — the embedding provider is
  not Anthropic, so verify against your installed `voyageai` and adjust `MODEL` if your
  account doesn't have `voyage-3`.

## Tasks

1. **Implement `cosine_similarity`** and pass the offline `COSINE_CASES` truth table
   (identical → 1.0, orthogonal → 0.0, parallel → 1.0, opposite → -1.0; zero-magnitude
   → 0.0).

2. **Run the live recall** (with a Voyage key) and record semantic recall@1/2/3.

3. **Confirm the semantic win.** Check that Q4 retrieves the People-and-Culture
   (attrition) section, and note the query where semantic search does *worse* than BM25
   would — the rare term "Halibut" (Q3). That contrast sets up ex4 (hybrid).

## Acceptance criteria

- [ ] `cosine_similarity` passes `COSINE_CASES` (offline).
- [ ] Semantic recall@1/2/3 recorded with a Voyage key.
- [ ] Noted the paraphrase win (Q4) and the rare-term weakness (Q3).

## Stretch goals

- Compare `input_type="query"` vs `"document"` for the queries — does using the right
  one change recall?
- Try a smaller/cheaper Voyage model and see how recall shifts.
- Swap section chunks for ex1's size-based chunks and re-measure.

## Self-check

- Why does cosine similarity ignore vector magnitude, and why is that the right choice
  for comparing embeddings?
- Semantic search found "attrition" from "leaving" — what is it actually comparing, and
  why would BM25 score that pair near zero?
