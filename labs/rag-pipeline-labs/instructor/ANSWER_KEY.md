# Answer Key — RAG Pipeline Labs

Instructor reference. Expected solution per exercise plus the gotchas. Model ids:
`claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`; embeddings via Voyage
(`voyage-3`). All retrieval is over the shared `corpus/corpus.md` (8 sections + a
leading title chunk), evaluated with `corpus/queries.json`.

---

## ex1 — Chunking

`chunk_by_size` reference:

```python
def chunk_by_size(text, size=SIZE, overlap=0):
	if overlap >= size:
		overlap = 0            # never-advance guard
	step = size - overlap
	chunks, i = [], 0
	while i < len(text):
		chunks.append(text[i:i + size])
		if i + size >= len(text):
			break
		i += step
	return chunks
```

Expected (see `gold_chunking.json`): size=160 overlap=0 → **8/9** intact; overlap=40 →
**9/9**; section-based → **9/9**. The single no-overlap miss is one answer string the
boundary slices; overlap heals it. Watch for: an off-by-one that drops the tail, or
forgetting the `overlap >= size` guard (infinite loop).

## ex2 — Embeddings & semantic search

`cosine_similarity` reference:

```python
def cosine_similarity(a, b):
	dot = sum(x * y for x, y in zip(a, b))
	na = math.sqrt(sum(x * x for x in a))
	nb = math.sqrt(sum(y * y for y in b))
	return 0.0 if na == 0 or nb == 0 else dot / (na * nb)
```

Passes `COSINE_CASES` offline. Live recall depends on Voyage, so grade on the
qualitative wins: Q4 ("keep employees from leaving") retrieves People-and-Culture
(attrition) with no shared words; Q3 ("Halibut") is where semantic underperforms
lexical. Watch for: not normalizing (returns a dot product, not a cosine), or
crashing on a zero vector.

## ex3 — BM25

`score` reference:

```python
def score(self, query_terms, doc_idx):
	tf = Counter(self.doc_tokens[doc_idx])
	dl = len(self.doc_tokens[doc_idx])
	total = 0.0
	for term in query_terms:
		f = tf.get(term, 0)
		if not f:
			continue
		total += self.idf(term) * (f * (K1 + 1)) / (f + K1 * (1 - B + B * dl / self.avgdl))
	return total
```

Expected (see `gold_bm25.json`): recall@1/2/3 = **5/7, 6/7, 6/7**; Q3's rare term
"Halibut" is the rank-1 chunk. The query BM25 buries is Q4 (paraphrase, gold at rank
4). Watch for: summing term frequency without the saturation/length terms, or
recomputing idf wrong (rarer must score higher).

## ex4 — Hybrid + RRF

`reciprocal_rank_fusion` reference:

```python
def reciprocal_rank_fusion(rankings):
	scores = {}
	for ranking in rankings:
		for position, doc in enumerate(ranking, start=1):
			scores[doc] = scores.get(doc, 0) + 1 / (position + 1)
	return [doc for doc, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]
```

Passes all three `RRF_CASES` (case 1 is the course's worked example →
`[doc2, doc6, doc7]`). Expected recall (see `gold_hybrid.json`): bm25 5/6/6, semantic
6/6/7, **hybrid 7/7/7** — hybrid@1 beats both. Complementarity: BM25 owns Q3 (rare
term), semantic owns Q4 (paraphrase), RRF keeps both. Watch for: 0-based ranks
(changes the weights), forgetting the tie-break (nondeterministic order), or averaging
raw scores instead of rank-fusing.

## ex5 — Reranking, contextual retrieval, citations

- **rerank.py:** `RERANK_SYSTEM` should tell Claude to reorder by what answers the
  query's intent, most relevant first, via the `rank_documents` tool. The candidate
  lists start with `before_rank1_correct = 0`; after reranking the gold section should
  be rank 1 for all (or ≥2 of) the three cases. Watch for: a prompt that rewards word
  overlap (would keep the wrong doc on Q8).
- **contextual.py:** `context_prompt` gives Claude the whole document plus the chunk
  and asks for one situating sentence, no preamble. Success = the added sentence names
  the security/incident topic (`TOPIC_WORDS` hit). Watch for: returning the chunk
  itself, or a multi-paragraph essay.
- **answer_with_citations.py:** `build_document_block` returns
  `{"type": "document", "source": {"type": "text", "media_type": "text/plain",
  "data": corpus_text}, "title": ..., "citations": {"enabled": True},
  "cache_control": {"type": "ephemeral"}}`. Success = ≥1 citation attached and
  `cache_creation_input_tokens > 0` (then `cache_read_input_tokens > 0` on a repeat).
  Watch for: omitting `citations.enabled` (no spans), or putting `cache_control` on the
  wrong block.

---

### Grading notes

- **The numbers are the deliverable.** ex1/ex3/ex4 each produce a measured table —
  a solution that implements the function but records nothing has missed the point.
- **ex2 and ex5 call non-deterministic / external services** (Voyage, live Claude).
  Grade them on the offline truth tables (cosine, RRF is in ex4) and the qualitative
  expectations in the gold files, not on exact live numbers.
- **Flagged surface:** the Voyage SDK (ex2) and the citations/document-source shape
  (ex5c) were current at build time — reward a correct port if an SDK version differs.
- **Stretch goals** are unscored but good signal.
