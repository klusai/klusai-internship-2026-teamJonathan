"""Exercise 3 — BM25 lexical search.

Semantic search (ex2) matches meaning but can miss exact terms — a product codename,
an incident id, a rare word. BM25 is the classic lexical counterweight: it ranks
documents by how many of the query's *rare* terms they contain, weighting rare terms
above common ones. This exercise builds a BM25 index over the corpus sections and
measures recall@k, with a spotlight on the rare-term query ("Project Halibut") that
lexical search should nail at rank 1.

You implement the BM25 score; everything else (tokenizer, index, recall harness) is
provided. Pure Python, no API key.

Setup:
    python bm25.py
"""

import json
import math
import re
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE.parent / "corpus" / "corpus.md"
QUERIES = HERE.parent / "corpus" / "queries.json"

K1 = 1.5   # term-frequency saturation
B = 0.75   # length normalization


def tokenize(text: str) -> list[str]:
	"""Lowercase tokens; keeps hyphenated ids like 'inc-2023-014' as one token."""
	return re.findall(r"[a-z0-9][a-z0-9\-]*", text.lower())


def chunk_by_section(text: str) -> list[str]:
	"""One chunk per '## ' section (same splitter as ex1's reference)."""
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


class BM25Index:
	def __init__(self) -> None:
		self.docs: list[str] = []
		self.doc_tokens: list[list[str]] = []
		self.df: dict[str, int] = {}

	def add_document(self, text: str) -> None:
		toks = tokenize(text)
		self.docs.append(text)
		self.doc_tokens.append(toks)
		for term in set(toks):
			self.df[term] = self.df.get(term, 0) + 1

	@property
	def avgdl(self) -> float:
		if not self.doc_tokens:
			return 0.0
		return sum(len(t) for t in self.doc_tokens) / len(self.doc_tokens)

	def idf(self, term: str) -> float:
		n = len(self.doc_tokens)
		df = self.df.get(term, 0)
		# Probabilistic IDF (always positive form): rarer term -> higher idf.
		return math.log(1 + (n - df + 0.5) / (df + 0.5))

	def score(self, query_terms: list[str], doc_idx: int) -> float:
		"""BM25 score of document `doc_idx` for `query_terms`.

		TODO(task 1): sum, over each query term, the contribution
		    idf(term) * (f * (K1 + 1)) / (f + K1 * (1 - B + B * dl / avgdl))
		where f = how many times the term appears in this document's tokens, and
		dl = this document's length in tokens. Terms not in the doc contribute 0.
		"""
		toks = self.doc_tokens[doc_idx]
		dl = len(toks)
		avgdl = self.avgdl
		score = 0.0
		for term in query_terms:
			f = toks.count(term)
			if f == 0:
				continue
			denom = f + K1 * (1 - B + B * dl / avgdl)
			score += self.idf(term) * (f * (K1 + 1)) / denom
		return score

	def search(self, query: str, k: int = 3) -> list[tuple[str, float]]:
		qterms = tokenize(query)
		scored = [(self.score(qterms, i), i) for i in range(len(self.docs))]
		scored.sort(key=lambda x: (-x[0], x[1]))
		return [(self.docs[i], s) for s, i in scored[:k]]


def build_index(text: str) -> BM25Index:
	idx = BM25Index()
	for chunk in chunk_by_section(text):
		idx.add_document(chunk)
	return idx


def main() -> int:
	text = CORPUS.read_text()
	queries = json.loads(QUERIES.read_text())["queries"]
	clean = [q for q in queries if q["id"] <= 7]  # the clean retrieval set
	idx = build_index(text)

	print("BM25 recall@k over the 7 clean queries:")
	for k in (1, 2, 3):
		hits = sum(
			1 for q in clean
			if any(q["answer_contains"].lower() in doc.lower() for doc, _ in idx.search(q["query"], k))
		)
		print(f"  recall@{k}: {hits}/{len(clean)} = {hits / len(clean):.0%}")

	q3 = next(q for q in queries if q["id"] == 3)
	top_doc, top_score = idx.search(q3["query"], 1)[0]
	nailed = q3["answer_contains"].lower() in top_doc.lower()
	print(f"\nrare-term spotlight — Q3 '{q3['query']}'")
	print(f"  '{q3['answer_contains']}' is the rank-1 chunk: {nailed} (score={top_score:.2f})")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())


# Results (K1=1.5, B=0.75):
#   recall@1: 5/7 = 71%
#   recall@2: 6/7 = 86%
#   recall@3: 6/7 = 86%
# Rare-term spotlight: Q3 "What is Project Halibut?" lands 'Halibut' at rank 1
# (score=5.72). IDF makes the rare codename dominate the score, so the one section
# that mentions it wins outright — exactly what pure semantic search can fumble.
#
# Query BM25 handles poorly: Q4 "What did the company do to keep employees from
# leaving?" The answer section is about *attrition*, but the query shares no rare
# terms with it — "keep employees from leaving" is a paraphrase, and the words it
# does share ("company", "employees") are common and low-IDF. BM25 is lexical: with
# no rare term overlap it cannot bridge the vocabulary gap between "keep employees
# from leaving" and "attrition". This is the semantic-match case (ex2) that a hybrid
# (ex4) recovers by combining lexical exactness with meaning.
