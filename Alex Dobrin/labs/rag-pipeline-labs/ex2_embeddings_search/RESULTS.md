# Exercise 2 — results

## Offline (verified here, no API key)

`cosine_similarity` passes all 5 `COSINE_CASES`:

```
=== cosine_similarity truth table (offline) ===
  cos([1.0, 0.0], [1.0, 0.0]) = 1.0000  expected 1.0  PASS
  cos([1.0, 0.0], [0.0, 1.0]) = 0.0000  expected 0.0  PASS
  cos([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) = 1.0000  expected 1.0  PASS
  cos([1.0, 0.0], [-1.0, 0.0]) = -1.0000  expected -1.0  PASS
  cos([0.0, 0.0], [1.0, 0.0]) = 0.0000  expected 0.0  PASS
  cosine_similarity is correct
```

## Voyage SDK surface

Verified against the installed `voyageai` 0.4.1 (no network calls). The code uses:

- `voyageai.Client()` — reads `VOYAGE_API_KEY` from the environment.
- `client.embed(texts, model=MODEL, input_type=input_type)` — `input_type` is
  `"document"` for corpus chunks and `"query"` for queries.
- `MODEL = "voyage-3"`.
- Result read via `result.embeddings`.

The installed signature is
`Client.embed(self, texts, model=None, input_type=None, truncation=True, output_dtype=None, output_dimension=None)`, which matches the call exactly.

## Live recall (measured with a Voyage key, `voyage-3`, section chunks)

```
=== semantic recall@k over the 7 clean queries ===
  recall@1: 7/7 = 100%
  recall@2: 7/7 = 100%
  recall@3: 7/7 = 100%
```

Semantic search over `voyage-3` embeddings retrieved the gold section at rank 1 for all
7 clean queries — including **Q4** (`"keep employees from leaving"` → the
People-and-Culture / **attrition** section), the paraphrase win BM25 cannot make since
the query and section share no keywords.

Note: on this small corpus `voyage-3` also placed **Q3** (`"What is Project Halibut?"`)
correctly at rank 1, so the rare-term weakness that motivates hybrid retrieval did not
surface here — but ex3 (BM25) and ex4 (hybrid) show the general case where a rare,
high-signal token like "Halibut" is exactly what lexical matching nails and embeddings
can fumble.
