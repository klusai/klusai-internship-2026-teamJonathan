"""Exercise 2 — embeddings and semantic search.

Lexical search matches words; semantic search matches meaning. You embed each chunk
into a vector, embed the query the same way, and retrieve the chunks whose vectors are
closest by cosine similarity. This is what lets "keep employees from leaving" find the
section about *attrition* even with no shared words.

You implement cosine similarity (the heart of the retrieval, and gradeable offline
against a truth table). The embedding call uses Voyage AI, exactly as the course does.

⚠️ FLAG — embeddings need a Voyage API key (separate from Anthropic; free tier):
    pip install voyageai
    export VOYAGE_API_KEY=...
The Voyage SDK surface (client, `embed`, model name, `input_type`) was current when
this pack was built — verify against your installed version; adjust MODEL if needed.
The cosine self-test runs with no key, so you can build and check the core offline.

Setup:
    pip install voyageai
    export VOYAGE_API_KEY=...
    python semantic_search.py
"""

import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE.parent / "corpus" / "corpus.md"
QUERIES = HERE.parent / "corpus" / "queries.json"

MODEL = "voyage-3"  # ⚠️ adjust to a model your Voyage account supports

# Offline truth table for cosine_similarity — runs without any API key.
COSINE_CASES = [
	([1.0, 0.0], [1.0, 0.0], 1.0),
	([1.0, 0.0], [0.0, 1.0], 0.0),
	([1.0, 2.0, 3.0], [2.0, 4.0, 6.0], 1.0),  # parallel vectors
	([1.0, 0.0], [-1.0, 0.0], -1.0),
	([0.0, 0.0], [1.0, 0.0], 0.0),  # zero-magnitude vector -> 0.0 (no divide-by-zero)
]


def cosine_similarity(a: list[float], b: list[float]) -> float:
	"""Cosine of the angle between two vectors: dot(a, b) / (||a|| * ||b||).

	Return 0.0 if either vector has zero magnitude.
	Range is -1.0 (opposite) to 1.0 (identical direction).
	"""
	dot = sum(x * y for x, y in zip(a, b))
	norm_a = math.sqrt(sum(x * x for x in a))
	norm_b = math.sqrt(sum(y * y for y in b))
	if norm_a == 0.0 or norm_b == 0.0:
		return 0.0
	return dot / (norm_a * norm_b)


def chunk_by_section(text: str) -> list[str]:
	chunks: list[str] = []
	current: list[str] = []
	for line in text.splitlines(keepends=True):
		if line.startswith("## ") and current:
			chunks.append("".join(current))
			current = []
		current.append(line)
	if current:
		chunks.append("".join(current))
	return chunks


class VectorIndex:
	def __init__(self) -> None:
		self.vectors: list[list[float]] = []
		self.docs: list[str] = []

	def add(self, vector: list[float], doc: str) -> None:
		self.vectors.append(vector)
		self.docs.append(doc)

	def search(self, query_vector: list[float], k: int = 3) -> list[tuple[str, float]]:
		scored = [
			(cosine_similarity(query_vector, v), i) for i, v in enumerate(self.vectors)
		]
		scored.sort(key=lambda x: (-x[0], x[1]))
		return [(self.docs[i], s) for s, i in scored[:k]]


def embed(texts: list[str], input_type: str) -> list[list[float]]:
	"""Embed a list of texts with Voyage. input_type is 'document' or 'query'."""
	import voyageai

	client = voyageai.Client()  # reads VOYAGE_API_KEY
	result = client.embed(texts, model=MODEL, input_type=input_type)
	return result.embeddings


def grade_cosine() -> bool:
	print("=== cosine_similarity truth table (offline) ===")
	ok = True
	for a, b, expected in COSINE_CASES:
		got = cosine_similarity(a, b)
		passed = abs(got - expected) < 1e-9
		ok = ok and passed
		print(f"  cos({a}, {b}) = {got:.4f}  expected {expected}  {'PASS' if passed else 'FAIL'}")
	print(f"  cosine_similarity {'is correct' if ok else 'has FAILURES'}\n")
	return ok


def main() -> int:
	if not grade_cosine():
		print("Fix cosine_similarity first (it's gradeable offline).")
		return 1
	if not os.environ.get("VOYAGE_API_KEY"):
		print("Set VOYAGE_API_KEY to run the live semantic-search recall.")
		return 0

	text = CORPUS.read_text()
	queries = [q for q in json.loads(QUERIES.read_text())["queries"] if q["id"] <= 7]

	chunks = chunk_by_section(text)
	index = VectorIndex()
	for chunk, vector in zip(chunks, embed(chunks, "document")):
		index.add(vector, chunk)

	query_vectors = embed([q["query"] for q in queries], "query")
	print("=== semantic recall@k over the 7 clean queries ===")
	for k in (1, 2, 3):
		hits = 0
		for q, qv in zip(queries, query_vectors):
			top = index.search(qv, k)
			if any(q["answer_contains"].lower() in doc.lower() for doc, _ in top):
				hits += 1
		print(f"  recall@{k}: {hits}/{len(queries)} = {hits / len(queries):.0%}")
	# Spotlight: Q4 ("keep employees from leaving") should retrieve the attrition
	# section even though they share no words — the semantic win BM25 can't make.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
