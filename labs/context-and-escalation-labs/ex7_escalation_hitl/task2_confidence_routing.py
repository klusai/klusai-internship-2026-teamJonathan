"""Exercise 7, task 2 — confidence-based routing with a hard guardrail.

The model proposes an action and rates its own confidence; your code decides what
happens to it. Two rules combine:

  confidence band:   >= 0.85 -> AUTO     (run it)
                     >= 0.60 -> REVIEW   (a human approves first)
                      < 0.60 -> ESCALATE (hand to a human)

  guardrail:         HIGH-RISK action types (refund, delete_account,
                     change_payment, send_external_email) are NEVER AUTO,
                     no matter how confident the model is — floor them at REVIEW.

The guardrail is the point: confidence alone must not be able to auto-execute an
irreversible action. `route()` is graded against the truth table below (it is the
spec — including the cases where high confidence is overridden to REVIEW).

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...   # only needed for the live Part B
    python task2_confidence_routing.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-6"
HERE = Path(__file__).parent

AUTO_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.60

# Irreversible / externally-visible actions. Never AUTO, regardless of confidence.
HIGH_RISK = {"refund", "delete_account", "change_payment", "send_external_email"}

# The spec for route(), as a truth table: (confidence, action_type) -> expected.
# Note the guardrail rows where a high confidence is deliberately knocked down to
# REVIEW because the action is high-risk.
ROUTE_CASES = [
	(0.95, "answer_faq", "AUTO"),
	(0.85, "answer_faq", "AUTO"),       # band boundary is inclusive
	(0.80, "read_order", "REVIEW"),
	(0.60, "read_order", "REVIEW"),     # band boundary is inclusive
	(0.59, "tag_ticket", "ESCALATE"),
	(0.40, "answer_faq", "ESCALATE"),
	(0.99, "refund", "REVIEW"),         # guardrail: high-risk never AUTO
	(0.85, "delete_account", "REVIEW"), # guardrail at the AUTO boundary
	(0.72, "change_payment", "REVIEW"), # already REVIEW by band; high-risk is fine here
	(0.55, "send_external_email", "ESCALATE"),  # low confidence wins (stricter than REVIEW)
	(0.30, "delete_account", "ESCALATE"),
	(0.90, "refund", "REVIEW"),         # guardrail
]


def route(confidence: float, action_type: str) -> str:
	"""Return 'AUTO', 'REVIEW', or 'ESCALATE'.

	TODO(task 2): implement both rules.
	  1. Pick a base route from the confidence band (AUTO_THRESHOLD /
	     REVIEW_THRESHOLD).
	  2. Apply the guardrail: if action_type is in HIGH_RISK, it must never be AUTO —
	     floor it at REVIEW. (ESCALATE is stricter than REVIEW, so a low-confidence
	     high-risk action still ESCALATEs.)
	"""
	# TODO: implement
	raise NotImplementedError


PROPOSE_TOOL = {
	"name": "propose_action",
	"description": "Propose how to handle the task and rate your confidence 0.0-1.0.",
	"input_schema": {
		"type": "object",
		"properties": {
			"action": {"type": "string", "description": "What you would do, in one line."},
			"confidence": {"type": "number", "description": "0.0 (unsure) to 1.0 (certain)."},
			"rationale": {"type": "string"},
		},
		"required": ["action", "confidence", "rationale"],
	},
}

PROPOSE_SYSTEM = (
	"You are a support agent. For the task, propose the single action you would take "
	"and honestly rate your confidence that it is correct and safe to perform "
	"automatically. Be conservative: if anything is ambiguous or risky, lower your "
	"confidence."
)


def grade_route() -> bool:
	"""Part A — check route() against the truth table. Deterministic; no API."""
	print("=== Part A: route() truth table ===")
	ok = True
	for confidence, action_type, expected in ROUTE_CASES:
		got = route(confidence, action_type)
		mark = "PASS" if got == expected else "FAIL"
		if got != expected:
			ok = False
		print(f"  route({confidence:>4}, {action_type:<19}) = {str(got):<9} expected {expected:<9} {mark}")
	print(f"  route() {'is correct' if ok else 'has FAILURES'}\n")
	return ok


def run_live() -> None:
	"""Part B — let the model propose+rate each task, then route it. Observational."""
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("(skip Part B: set ANTHROPIC_API_KEY to run the live routing)")
		return
	tasks = json.loads((HERE / "routing_tasks.json").read_text())["tasks"]
	client = anthropic.Anthropic()
	print("=== Part B: live model confidence -> route ===")
	print(f"{'#':>2}  {'action_type':<20}{'conf':>5}  {'route':<9} task")
	print("-" * 90)
	for t in tasks:
		resp = client.messages.create(
			model=MODEL,
			max_tokens=400,
			system=PROPOSE_SYSTEM,
			tools=[PROPOSE_TOOL],
			tool_choice={"type": "tool", "name": "propose_action"},
			messages=[{"role": "user", "content": t["task"]}],
		)
		tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
		conf = float(tool_use.input["confidence"]) if tool_use else 0.0
		decision = route(conf, t["action_type"])
		print(f"{t['id']:>2}  {t['action_type']:<20}{conf:>5.2f}  {decision:<9} {t['task'][:42]}")
	# Watch the HIGH_RISK rows: even at high confidence they must show REVIEW, not AUTO.


def main() -> int:
	route_ok = grade_route()
	if not route_ok:
		print("Fix route() before trusting Part B.\n")
	run_live()
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
