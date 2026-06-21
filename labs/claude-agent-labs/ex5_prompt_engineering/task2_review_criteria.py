"""Exercise 5, task 2 — vague vs. explicit-criteria review.

Run a VAGUE review prompt 3 times and an EXPLICIT-CRITERIA review prompt 3 times
over big_diff.txt. Compare: the vague prompt finds different things each run and
often misses planted issues; the explicit prompt finds the same real issues every
time. The diff has three planted problems — SQL injection, a bare `except: pass`,
and unsalted MD5 password hashing.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task2_review_criteria.py
"""

import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-4-8"
RUNS = 3
HERE = Path(__file__).parent

VAGUE_PROMPT = "Review this diff and tell me about any problems.\n\n{diff}"

# TODO(task 2): complete the criteria checklist. One item is seeded; add the rest
# so the review reliably catches the three planted issues (and anything else worth
# flagging). Be specific — explicit criteria are the whole point.
CRITERIA = [
	"Security: flag any SQL built by string concatenation / f-strings (injection risk).",
	# TODO: add a criterion about exception handling (bare except / except: pass).
	# TODO: add a criterion about password hashing (unsalted / fast hashes like MD5).
	# TODO: add any other criteria you think a reviewer should always apply.
]

EXPLICIT_PROMPT = (
	"Review this diff against these explicit criteria. For EACH criterion, state "
	"whether it is violated and cite the file and line.\n\nCriteria:\n{criteria}\n\n{diff}"
)


def review(client: anthropic.Anthropic, prompt: str) -> str:
	resp = client.messages.create(
		model=MODEL,
		max_tokens=1500,
		messages=[{"role": "user", "content": prompt}],
	)
	return "".join(b.text for b in resp.content if b.type == "text")


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	diff = (HERE / "big_diff.txt").read_text()
	client = anthropic.Anthropic()
	criteria_block = "\n".join(f"- {c}" for c in CRITERIA)

	print("=" * 80)
	print("VAGUE prompt — 3 runs (expect inconsistent coverage)")
	print("=" * 80)
	for i in range(1, RUNS + 1):
		print(f"\n--- vague run {i} ---")
		print(review(client, VAGUE_PROMPT.format(diff=diff)))

	print("\n" + "=" * 80)
	print("EXPLICIT-CRITERIA prompt — 3 runs (expect the same real issues each time)")
	print("=" * 80)
	for i in range(1, RUNS + 1):
		print(f"\n--- explicit run {i} ---")
		print(review(client, EXPLICIT_PROMPT.format(criteria=criteria_block, diff=diff)))

	print("\nCompare: did the explicit runs find SQL injection, bare except, and MD5 every time?")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
