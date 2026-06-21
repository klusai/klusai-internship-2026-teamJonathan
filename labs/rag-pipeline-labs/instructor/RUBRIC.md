# Rubric — RAG Pipeline Labs

**Total: 100 points — 20 per exercise.** Partial credit is fine; per-task points sum to
20 each. A passing grade is ≥ 70.

---

## Exercise 1 — Chunking (20 pts)

| Pts | Criterion |
|----:|-----------|
| 8 | `chunk_by_size` produces correct overlapping windows; `overlap=0` is non-overlapping; `overlap >= size` is guarded (no infinite loop); full text covered. |
| 7 | All three "answers intact" numbers recorded; overlap ≥ no-overlap and section-based = 9/9. |
| 5 | Written note on when to prefer size-based vs structure-based chunking. |

## Exercise 2 — Embeddings & semantic search (20 pts)

| Pts | Criterion |
|----:|-----------|
| 10 | `cosine_similarity` correct — passes `COSINE_CASES` and returns 0.0 on a zero vector. |
| 5 | Semantic recall@1/2/3 recorded (with a Voyage key). |
| 5 | Noted the paraphrase win (Q4 → attrition) and the rare-term weakness (Q3 → Halibut). |

## Exercise 3 — BM25 (20 pts)

| Pts | Criterion |
|----:|-----------|
| 12 | `score` implements the BM25 formula (idf + tf saturation + length norm); recall@1/2/3 recorded (5/7, 6/7, 6/7). |
| 4 | Q3's rare term is the rank-1 chunk. |
| 4 | Written note on a query BM25 handles poorly (Q4) and why. |

## Exercise 4 — Hybrid + RRF (20 pts)

| Pts | Criterion |
|----:|-----------|
| 10 | `reciprocal_rank_fusion` passes all three `RRF_CASES` (incl. the course's worked example). |
| 7 | recall@k table recorded; hybrid@1 (7/7) strictly beats both single methods. |
| 3 | Written note on why RRF merges by rank, not raw score. |

## Exercise 5 — Reranking / contextual / citations (20 pts)

| Pts | Criterion |
|----:|-----------|
| 7 | Reranking moves the gold section to rank 1 on the mis-ordered candidates (after > before). |
| 7 | Contextual retrieval: the added sentence names the chunk's security topic. |
| 6 | Grounded answer returns ≥ 1 citation and caches the corpus (created then read). |

---

## Grading notes

- **The numbers are the deliverable** — ex1/ex3/ex4 produce measured tables; no
  recorded numbers means the "recorded" half of those criteria is not met.
- **ex2 and ex5 call Voyage / live Claude** — grade the offline truth tables (cosine,
  and RRF in ex4) and the qualitative gold, not exact live numbers.
- **Flagged surface** (Voyage SDK in ex2, citations/document shape in ex5c): reward a
  correct port even if an installed version differs.
- **Stretch goals** are unscored but good signal for an A+ / discussion.
