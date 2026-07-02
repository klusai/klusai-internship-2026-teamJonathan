"""Exercise 7, task 1 — decide when to escalate, and why.

For each situation in scenarios.json the assistant must decide HANDLE vs ESCALATE
and name the trigger: policy_gap (outside what it's authorized to do), user_request
(the user asked for a human), no_progress (stuck / repeating / standard steps
exhausted), or none (just handle it). The work is in the policy you write: a vague
prompt mislabels the borderline cases; a precise one that spells out the three
triggers routes them correctly.

Run it with the empty/vague policy first and record the accuracy, then write a real
policy and run again. The delta is the point — same as ex3's tool descriptions.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task1_escalation_triggers.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic

# A good model to compare on — swap and re-run as a stretch.
MODEL = "claude-haiku-4-5"

HERE = Path(__file__).parent

# TODO(task 1): write the escalation policy. Define HANDLE vs ESCALATE and the four
# triggers precisely, including the authority limits that make case 3 a policy_gap
# and the "standard steps exhausted" idea behind no_progress. The classifier reads
# this as its system prompt, so be specific: vague guidance loses the borderline
# cases.
POLICY = ""  # TODO: fill in

CLASSIFY_TOOL = {
	"name": "route_request",
	"description": "Record the routing decision and the trigger for one situation.",
	"input_schema": {
		"type": "object",
		"properties": {
			"decision": {"type": "string", "enum": ["HANDLE", "ESCALATE"]},
			"trigger": {
				"type": "string",
				"enum": ["policy_gap", "user_request", "no_progress", "none"],
			},
		},
		"required": ["decision", "trigger"],
	},
}


def classify(client: anthropic.Anthropic, scenario: str) -> tuple[str, str]:
	"""Ask the model to route one situation; return (decision, trigger)."""
	resp = client.messages.create(
		model=MODEL,
		max_tokens=256,
		system=POLICY,
		tools=[CLASSIFY_TOOL],
		tool_choice={"type": "tool", "name": "route_request"},
		messages=[{"role": "user", "content": scenario}],
	)
	tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
	if tool_use is None:
		return ("?", "?")
	return (tool_use.input.get("decision"), tool_use.input.get("trigger"))


def is_correct(case: dict, decision: str, trigger: str) -> bool:
	"""A pick is correct if it matches the gold pair (or any accepted pair)."""
	if case.get("debatable"):
		return [decision, trigger] in case.get("accept", [])
	return decision == case["expected_decision"] and trigger == case["expected_trigger"]


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	cases = json.loads((HERE / "scenarios.json").read_text())["cases"]
	client = anthropic.Anthropic()

	scored = 0  # non-debatable cases only
	correct = 0
	debatable_ok = 0
	debatable_total = 0
	print(f"model={MODEL}\n")
	print(f"{'#':>2}  {'decision':<9}{'trigger':<13}result  scenario")
	print("-" * 90)
	for case in cases:
		decision, trigger = classify(client, case["scenario"])
		ok = is_correct(case, decision, trigger)
		if case.get("debatable"):
			debatable_total += 1
			debatable_ok += int(ok)
			mark = "DEBATE"
		else:
			scored += 1
			correct += int(ok)
			mark = "PASS" if ok else "FAIL"
		print(f"{case['id']:>2}  {str(decision):<9}{str(trigger):<13}{mark:<7} {case['scenario'][:48]}")

	print("-" * 90)
	print(f"accuracy (non-debatable): {correct}/{scored} = {correct / scored:.0%}")
	print(f"debatable: {debatable_ok}/{debatable_total} landed on an accepted answer (not scored)")
	# Record this number, then write a real POLICY and run again to see it climb.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
