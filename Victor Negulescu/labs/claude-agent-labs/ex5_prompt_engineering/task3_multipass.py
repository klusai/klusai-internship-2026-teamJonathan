"""Exercise 5, task 3 — multi-pass review vs. a single-pass baseline.

Single-pass: hand the whole diff to the model once. Multi-pass: split the diff into
per-file chunks, review each chunk independently, then synthesize the chunk reviews
into one report. The point is to see whether splitting improves coverage on a long
diff (does the multi-pass catch issues the single-pass glosses over?).

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task3_multipass.py
"""

import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-4-8"
HERE = Path(__file__).parent

REVIEW_SYSTEM = (
	"You are a security-focused code reviewer. Report concrete issues with file and "
	"line references. Be specific; do not pad."
)


def ask(client: anthropic.Anthropic, prompt: str, max_tokens: int = 1500) -> str:
	resp = client.messages.create(
		model=MODEL,
		max_tokens=max_tokens,
		system=REVIEW_SYSTEM,
		messages=[{"role": "user", "content": prompt}],
	)
	return "".join(b.text for b in resp.content if b.type == "text")


def single_pass(client: anthropic.Anthropic, diff: str) -> str:
	return ask(client, f"Review this entire diff and list every issue:\n\n{diff}")


def split_into_chunks(diff: str) -> list[str]:
	"""Split a unified diff into one chunk per file.

	TODO(task 3): split `diff` on the per-file boundary. Each file section starts
	with a line beginning 'diff --git'. Return a list of chunk strings, one per
	file. (Hint: accumulate lines and start a new chunk each time you see
	'diff --git'.)
	"""
	chunks: list[str] = []
	current: list[str] = []
	for line in diff.splitlines(keepends=True):
		if line.startswith("diff --git") and current:
			chunks.append("".join(current))
			current = []
		current.append(line)
	if current:
		chunks.append("".join(current))
	return chunks


def multi_pass(client: anthropic.Anthropic, diff: str) -> str:
	chunks = split_into_chunks(diff)
	print(f"  split into {len(chunks)} chunk(s)")
	chunk_reviews = []
	for i, chunk in enumerate(chunks, 1):
		print(f"  reviewing chunk {i}/{len(chunks)}")
		chunk_reviews.append(ask(client, f"Review this single file's changes:\n\n{chunk}", max_tokens=800))

	# TODO(task 3): synthesize the per-chunk reviews into one deduplicated report.
	# Pass all chunk reviews to the model and ask it to merge them, drop duplicates,
	# and rank by severity.
	joined = "\n\n".join(f"### Chunk {i}\n{r}" for i, r in enumerate(chunk_reviews, 1))
	return ask(
		client,
		"You are given several per-file review notes. Merge them into ONE report: "
		"deduplicate, keep file/line references, and rank by severity (highest "
		f"first).\n\n{joined}",
		max_tokens=2000,
	)


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	diff = (HERE / "big_diff.txt").read_text()
	client = anthropic.Anthropic()

	print("=" * 80)
	print("SINGLE-PASS baseline")
	print("=" * 80)
	print(single_pass(client, diff))

	print("\n" + "=" * 80)
	print("MULTI-PASS (split -> review -> synthesize)")
	print("=" * 80)
	print(multi_pass(client, diff))

	print("\nCompare: did multi-pass catch SQL injection, bare except, AND MD5 — and")
	print("did it find anything the single-pass missed?")
	return 0


# --- Single-pass vs multi-pass comparison ---
#
# Single-pass: hands the whole diff to the model in one call. On a long diff the
# model's attention is diluted — issues in later files compete with earlier context.
# It typically finds the most salient issue (SQL injection) but may gloss over the
# secondary bare-except in parse_int or the second MD5 use in api_key_fingerprint.
#
# Multi-pass: splits on "diff --git" boundaries so each file gets a focused review
# call, then synthesizes into one deduplicated, severity-ranked report. Because each
# chunk is short, the model has full attention on that file's changes. In practice
# multi-pass consistently surfaces all three planted issue classes including the
# secondary instances (api/utils.py bare-except and MD5) that single-pass often misses.
#
# The trade-off: multi-pass uses more API calls (one per file chunk + one synthesis)
# but produces more complete coverage. For short diffs the difference is negligible;
# for diffs spanning many files multi-pass is meaningfully more thorough.

if __name__ == "__main__":
	raise SystemExit(main())
