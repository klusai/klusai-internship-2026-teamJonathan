"""Exercise 4 — hybrid retrieval with Reciprocal Rank Fusion (RRF).

Lexical (BM25) and semantic (embeddings) search fail on different queries: BM25 nails
rare terms but fumbles paraphrases; semantic does the reverse. Hybrid search runs both
and merges their rankings. RRF is the standard, parameter-light way to merge: each
document scores sum(1 / (rank + 1)) across the rankings it appears in, and you re-sort
by that score. Documents ranked high by *both* methods rise to the top.

You implement `reciprocal_rank_fusion`. It's graded two ways: a small truth table (the
RRF spec, including the worked example from the course), and the recall@k it produces
when fusing the precomputed BM25 + semantic rankings in fixtures/. You should see the
fused recall@1 beat BOTH single methods.

Setup:
    python hybrid.py     # no API key — fuses precomputed rankings
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
FIXTURE = HERE / "fixtures" / "candidate_rankings.json"

# The RRF spec, as a truth table. Each case is (list_of_rankings, expected_fused).
# Case 1 is the worked example from the course. Scoring: a doc's RRF score is
# sum(1 / (position + 1)) over each ranking it appears in (position is 1-based);
# ties break by doc id ascending.
RRF_CASES = [
	([["doc2", "doc7", "doc6"], ["doc6", "doc2", "doc7"]], ["doc2", "doc6", "doc7"]),
	([["a", "b", "c"], ["a", "b", "c"]], ["a", "b", "c"]),
	([["a", "b", "c"], ["b", "c", "a"]], ["b", "a", "c"]),
]


def reciprocal_rank_fusion(rankings: list[list[str]]) -> list[str]:
	"""Merge ranked id lists into one fused ranking.

	TODO(task 1): for every id across all rankings, sum 1 / (position + 1) for each
	ranking it appears in (position is 1-based: 1st place -> 1/2, 2nd -> 1/3, ...);
	an id absent from a ranking adds nothing. Return the unique ids sorted by total
	score descending, breaking ties by id ascending.
	"""
	# TODO: implement
	raise NotImplementedError


def grade_rrf() -> bool:
	print("=== RRF truth table ===")
	ok = True
	for rankings, expected in RRF_CASES:
		got = reciprocal_rank_fusion(rankings)
		mark = "PASS" if got == expected else "FAIL"
		if got != expected:
			ok = False
		print(f"  {rankings} -> {got}  expected {expected}  {mark}")
	print(f"  reciprocal_rank_fusion {'is correct' if ok else 'has FAILURES'}\n")
	return ok


def recall_at_k(get_ranking, data, k: int) -> int:
	hits = 0
	for qid, rec in data["queries"].items():
		gold = data["gold"][qid]
		if gold in get_ranking(rec)[:k]:
			hits += 1
	return hits


def main() -> int:
	if not grade_rrf():
		print("Fix reciprocal_rank_fusion before trusting the recall numbers.")
		return 1

	data = json.loads(FIXTURE.read_text())
	n = len(data["queries"])

	getters = {
		"bm25 only": lambda rec: rec["bm25"],
		"semantic only": lambda rec: rec["vector"],
		"hybrid (RRF)": lambda rec: reciprocal_rank_fusion([rec["bm25"], rec["vector"]]),
	}
	print("=== recall@k over the 7 clean queries ===")
	print(f"{'method':<16}{'@1':>6}{'@2':>6}{'@3':>6}")
	for name, get in getters.items():
		row = "".join(f"{recall_at_k(get, data, k)}/{n}".rjust(6) for k in (1, 2, 3))
		print(f"{name:<16}{row}")

	# Complementarity spotlight: BM25 owns the rare term, semantic owns the paraphrase,
	# RRF keeps both.
	print("\ncomplementarity:")
	for qid in ("3", "4"):
		rec = data["queries"][qid]
		gold = data["gold"][qid]
		fused = reciprocal_rank_fusion([rec["bm25"], rec["vector"]])
		print(f"  Q{qid} ({gold}): bm25@1={rec['bm25'][0]}  semantic@1={rec['vector'][0]}  fused@1={fused[0]}")
	# Expect fused recall@1 to beat both single methods (7/7 vs 5/7 and 6/7).
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
