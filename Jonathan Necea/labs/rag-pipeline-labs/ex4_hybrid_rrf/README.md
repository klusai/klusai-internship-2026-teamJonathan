# Exercise 4 — Hybrid retrieval + Reciprocal Rank Fusion

**Topic:** combining lexical (BM25) and semantic (embeddings) rankings with Reciprocal
Rank Fusion so the pipeline is robust to both rare-term and paraphrase queries.

## Goal

Implement RRF and measure recall@k when fusing precomputed BM25 and semantic rankings.
Confirm the fused recall@1 beats *both* single methods, and see the complementarity
directly: BM25 catches the rare-term query semantic misses, semantic catches the
paraphrase BM25 misses, and RRF keeps both.

## What's here

```
ex4_hybrid_rrf/
  hybrid.py                       reciprocal_rank_fusion (TODO) + truth table + recall@k
  fixtures/candidate_rankings.json  precomputed bm25 + semantic rankings per query
  ../corpus/                      the shared corpus + queries
```

The rankings are precomputed (BM25 from `corpus.md`, semantic from a Voyage run) so
this exercise is self-contained and offline — you focus on the fusion.

## Setup

```bash
python hybrid.py     # no API key — fuses precomputed rankings
```

## Tasks

1. **Implement `reciprocal_rank_fusion`.** A document's score is `sum(1 / (rank + 1))`
   over each ranking it appears in (rank is 1-based); sort by score descending, ties
   by id ascending. Pass all three `RRF_CASES` (the first is the worked example from
   the course).

2. **Record the recall@k table.** Note that hybrid recall@1 (7/7) beats both BM25
   (5/7) and semantic (6/7).

3. **Read the complementarity output.** Q3 (rare term "Halibut") is owned by BM25;
   Q4 (paraphrase "keep employees from leaving") is owned by semantic; the fused top-1
   is correct for both. Write one sentence on why RRF, not just averaging scores, is a
   safe way to merge rankings whose score scales differ.

## Acceptance criteria

- [ ] `reciprocal_rank_fusion` passes all `RRF_CASES`.
- [ ] recall@k table recorded; hybrid@1 strictly beats both single methods.
- [ ] A written note on why RRF merges by *rank* rather than raw score.

## Stretch goals

- Swap the constant: real RRF often uses `1 / (k + rank)` with `k≈60`. Re-run with
  that and see whether the ranking changes on this small set.
- Add a third ranking (e.g., a title-only keyword match) and fuse all three.
- Replace the precomputed `vector` rankings with your own ex2 output and re-measure.

## Self-check

- Why can averaging raw BM25 scores and cosine similarities go wrong, and how does
  rank-based fusion sidestep it?
- On which query does RRF help most here, and which single method was failing it?
