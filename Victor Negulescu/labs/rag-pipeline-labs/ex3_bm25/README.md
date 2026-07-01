# Exercise 3 — BM25 lexical search

**Topic:** lexical retrieval with BM25 — term-frequency saturation, length
normalization, and inverse document frequency — and why it complements semantic search
on rare, exact terms.

## Goal

Implement the BM25 score and measure recall@k over the corpus sections. Confirm that
the rare-term query ("What is Project Halibut?") lands its answer at rank 1 — exactly
the case pure semantic search can fumble.

## What's here

```
ex3_bm25/
  bm25.py     tokenizer + BM25Index (TODO: the score formula) + recall@k harness
  ../corpus/  the shared corpus + queries
```

## Setup

```bash
python bm25.py     # no API key — pure Python
```

## Tasks

1. **Implement `BM25Index.score`.** For each query term, add
   `idf(term) * (f * (K1 + 1)) / (f + K1 * (1 - B + B * dl / avgdl))`, where `f` is
   the term's frequency in the document and `dl` is the document's token length. The
   `idf`, tokenizer, and ranking are provided.

2. **Record recall@1/2/3** over the 7 clean queries, and confirm the rare-term
   spotlight: Q3's answer ("Halibut") is the rank-1 chunk.

3. **Reason about the failure mode.** Find a query where BM25 alone would do poorly
   (a paraphrase with no shared rare terms — Q4 is a good candidate) and explain why.
   That motivates ex2 (semantic) and ex4 (hybrid).

## Acceptance criteria

- [ ] `score` implements the BM25 formula; recall@1/2/3 recorded.
- [ ] Q3's rare term is the rank-1 chunk.
- [ ] A written note on a query BM25 handles poorly and why.

## Stretch goals

- Add a stopword list and re-measure — does dropping common words change ranking?
- Swap the section chunks for ex1's size-based chunks and see how recall@k shifts.
- Print each query's top chunk's score gap (rank-1 minus rank-2) as a confidence proxy.

## Self-check

- Why does IDF weight rare terms above common ones, and why is that the whole point of
  BM25 for codenames and ids?
- What does the `B` parameter do, and when would you lower it toward 0?
