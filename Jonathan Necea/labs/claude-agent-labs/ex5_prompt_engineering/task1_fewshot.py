"""Exercise 5, task 1 — few-shot classification.

Classify each ticket in tickets.json as bug | feature | question. The classifier
starts ZERO-shot (the FEWSHOT slot is empty). Your job: fill FEWSHOT with a few
labeled examples and measure how accuracy changes — especially on the ambiguous
tickets (8, 13, 19).

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task1_fewshot.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-haiku-4-5"  # few-shot lift is most visible on a smaller model
LABELS = {"bug", "feature", "question"}
HERE = Path(__file__).parent

SYSTEM = (
	"You triage software support tickets. Classify each ticket as exactly one of: "
	"bug, feature, question. Reply with ONLY that single word, lowercase."
)

# TODO(task 1): fill this in with a handful of labeled examples (few-shot).
# Format is up to you — e.g. lines like:  "Login throws a 500." -> bug
# Start empty (zero-shot), record accuracy, then add examples and compare.
FEWSHOT = ""


def classify(client: anthropic.Anthropic, text: str) -> str:
	prompt = ""
	if FEWSHOT.strip():
		prompt += f"Examples:\n{FEWSHOT.strip()}\n\n"
	prompt += f"Ticket: {text}\nLabel:"
	resp = client.messages.create(
		model=MODEL,
		max_tokens=8,
		system=SYSTEM,
		messages=[{"role": "user", "content": prompt}],
	)
	raw = "".join(b.text for b in resp.content if b.type == "text").strip().lower()
	# Normalize: take the first recognized label token.
	for token in raw.replace(".", " ").split():
		if token in LABELS:
			return token
	return raw or "?"


def load_gold() -> dict[int, dict]:
	"""Gold labels live in ../instructor/gold_labels.json (present in the repo)."""
	path = HERE.parent / "instructor" / "gold_labels.json"
	if not path.exists():
		return {}
	data = json.loads(path.read_text())
	return {row["id"]: row for row in data["labels"]}


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	tickets = json.loads((HERE / "tickets.json").read_text())["tickets"]
	gold = load_gold()
	client = anthropic.Anthropic()

	mode = "few-shot" if FEWSHOT.strip() else "ZERO-shot (FEWSHOT is empty)"
	print(f"model={MODEL}  mode={mode}\n")

	firm_total = firm_correct = 0
	for t in tickets:
		pred = classify(client, t["text"])
		g = gold.get(t["id"])
		mark = ""
		if g:
			if g.get("debatable"):
				mark = f"[debatable; gold={g['label']}]"
			else:
				firm_total += 1
				firm_correct += int(pred == g["label"])
				mark = "PASS" if pred == g["label"] else f"FAIL (gold={g['label']})"
		print(f"{t['id']:>2}  {pred:<10} {mark}   {t['text']}")

	if firm_total:
		print(f"\naccuracy on non-debatable tickets: {firm_correct}/{firm_total} = {firm_correct / firm_total:.0%}")
		print("(tickets 8, 13, 19 are debatable and excluded from the score)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
