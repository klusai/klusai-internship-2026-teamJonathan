"""Exercise 1 — chunking strategies.

Chunking quality decides what retrieval can even find. If a chunk boundary cuts
through the answer, no amount of clever search will retrieve it. This exercise
compares three strategies on the shared corpus and measures how many of the 9
evaluation answers survive *intact* in some chunk:

  - size-based, no overlap  — fixed-width windows; boundaries can slice an answer
  - size-based, with overlap — windows share characters, so boundary cuts are healed
  - structure-based         — one chunk per markdown section; answers always intact

Record the three "answers intact" numbers. The point is the ordering:
overlap >= no-overlap, and section-based keeps everything (at the cost of uneven
chunk sizes).

Setup:
    python chunk.py        # no API key needed — this is pure text processing
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE.parent / "corpus" / "corpus.md"
QUERIES = HERE.parent / "corpus" / "queries.json"

SIZE = 160
OVERLAP = 40


def chunk_by_size(text: str, size: int = SIZE, overlap: int = 0) -> list[str]:
	"""Split `text` into windows of `size` characters that share `overlap` chars.

	TODO(task 1): slide a window of width `size` across the text, stepping forward
	by (size - overlap) each time, so each chunk shares its last `overlap`
	characters with the next chunk's start. With overlap=0 the windows don't share
	anything (and can slice an answer in half); a positive overlap heals those cuts.
	Return a list of chunk strings covering the whole text. Guard against overlap >=
	size (that would never advance).
	"""
	# TODO: implement
	raise NotImplementedError


def chunk_by_section(text: str) -> list[str]:
	"""Reference strategy: one chunk per '## ' markdown section."""
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


def answers_intact(chunks: list[str], queries: list[dict]) -> int:
	"""How many query answers appear, uncut, inside at least one chunk."""
	return sum(
		1 for q in queries
		if any(q["answer_contains"].lower() in c.lower() for c in chunks)
	)


def main() -> int:
	text = CORPUS.read_text()
	queries = json.loads(QUERIES.read_text())["queries"]
	total = len(queries)

	strategies = {
		f"size={SIZE}, overlap=0": chunk_by_size(text, SIZE, 0),
		f"size={SIZE}, overlap={OVERLAP}": chunk_by_size(text, SIZE, OVERLAP),
		"section-based": chunk_by_section(text),
	}
	print(f"{'strategy':<26}{'chunks':>7}{'answers intact':>16}")
	print("-" * 50)
	for name, chunks in strategies.items():
		print(f"{name:<26}{len(chunks):>7}{answers_intact(chunks, queries):>13}/{total}")
	# Expect: overlap healed the one answer the no-overlap boundary cut; section-based
	# keeps all of them. Record the three numbers.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
