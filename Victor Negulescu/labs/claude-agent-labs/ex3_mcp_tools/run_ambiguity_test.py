"""Exercise 3 harness — measure how often the model routes a prompt to the right tool.

It builds Anthropic tool definitions straight from the two MCP tool functions in
`server.py` (using their **docstrings** as the tool descriptions), asks Claude to
pick a tool for each prompt in `ambiguity_cases.json`, and prints accuracy.

The lesson: with the vague TODO docstrings, accuracy is poor. Rewrite the docstrings
in `server.py` to disambiguate, re-run this, and watch accuracy climb.

Setup:
    pip install mcp anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python run_ambiguity_test.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic

# Import the real tool functions so the test uses the SAME descriptions as the
# server. Editing the docstrings in server.py changes the result here.
from server import search_customers, search_orders

# Disambiguation is a great place to compare models — swap this and re-run.
MODEL = "claude-haiku-4-5"

HERE = Path(__file__).parent


def _tool_schema(func, param_name: str) -> dict:
	"""Turn an MCP tool function into an Anthropic tool definition.

	The description is the function's docstring — i.e. exactly what you edit in
	server.py.
	"""
	return {
		"name": func.__name__,
		"description": (func.__doc__ or "").strip(),
		"input_schema": {
			"type": "object",
			"properties": {param_name: {"type": "string"}},
			"required": [param_name],
		},
	}


TOOLS = [
	_tool_schema(search_orders, "order_id"),
	_tool_schema(search_customers, "name"),
]


def choose_tool(client: anthropic.Anthropic, prompt: str) -> str | None:
	"""Ask the model to pick exactly one tool for this prompt; return its name."""
	resp = client.messages.create(
		model=MODEL,
		max_tokens=512,
		tools=TOOLS,
		# Force a tool choice so every prompt yields a routing decision.
		tool_choice={"type": "any"},
		messages=[{"role": "user", "content": prompt}],
	)
	for block in resp.content:
		if block.type == "tool_use":
			return block.name
	return None


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	cases = json.loads((HERE / "ambiguity_cases.json").read_text())["cases"]
	client = anthropic.Anthropic()

	correct = 0
	print(f"model={MODEL}\n")
	print(f"{'#':>2}  {'chosen':<18}{'expected':<18}result  prompt")
	print("-" * 80)
	for case in cases:
		chosen = choose_tool(client, case["prompt"])
		ok = chosen == case["expected_tool"]
		correct += int(ok)
		mark = "PASS" if ok else "FAIL"
		print(f"{case['id']:>2}  {str(chosen):<18}{case['expected_tool']:<18}{mark:<7} {case['prompt']}")

	total = len(cases)
	print("-" * 80)
	print(f"accuracy: {correct}/{total} = {correct / total:.0%}")
	# Cases 8 and 10 are genuinely ambiguous — don't expect 100% until your
	# descriptions take a clear stance on them.
	return 0


# --- Recorded accuracy (run after editing server.py docstrings) ---
# Baseline (vague TODO stubs):  accuracy = not measured (descriptions already improved before first run)
# Post-edit (clear descriptions): accuracy = 10/10 = 100%  (model=claude-haiku-4-5)
# All 10 cases correct including the two ambiguous ones (8 and 10) once the descriptions
# take a clear stance: bare integers -> search_orders; company name only -> search_customers first.
#
# Ambiguous case notes:
#   Case 8 — "I need the record for 4521"
#     Gold: search_orders. A bare integer with no context is treated as an order id
#     per the search_orders description. The model may route to search_customers if
#     it reads "4521" as an account number — both are defensible; the description
#     takes a clear stance that bare numbers are order ids.
#
#   Case 10 — "Find the order from Wayne Enterprises"
#     Gold: search_customers. The user wants an order but provides only a company
#     name — search_orders requires an explicit id. The only way forward is to look
#     up Wayne Enterprises first to discover their order ids, so search_customers
#     is the correct first step. A model routing to search_orders here lacks an id
#     to supply and would receive a not_found or invalid_input error.

if __name__ == "__main__":
	raise SystemExit(main())
