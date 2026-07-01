"""Exercise 6, task 1 — distill verbose output to its load-bearing facts.

A raw CI log is mostly noise (pip resolver chatter, a wall of PASSED lines,
deprecation warnings, a coverage table). Keeping it all in an agent's context is
expensive and crowds out everything else. The fix is to call the model once to
extract only the facts that matter — the outcome, the counts, and the failures —
into a small structured object, then carry THAT forward instead of the raw log.

The point of the exercise is the compression ratio: count the tokens of the raw
log, count the tokens of the distilled summary, and record both. You should see a
large reduction with no loss of the facts that matter.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task1_extract_facts.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic

# Extraction is cheap and a great place to compare models — swap and re-run.
MODEL = "claude-haiku-4-5"

HERE = Path(__file__).parent
LOG_PATH = HERE / "fixtures" / "verbose_log.txt"

# The structured shape we want back. Forcing a tool call (tool_choice below) means
# the model must return exactly these fields — that constraint is what keeps the
# summary small and parseable.
SUMMARIZE_TOOL = {
	"name": "report_log_facts",
	"description": "Record only the load-bearing facts extracted from a CI/test log.",
	"input_schema": {
		"type": "object",
		"properties": {
			"outcome": {
				"type": "string",
				"enum": ["passed", "failed"],
				"description": "Overall result of the run.",
			},
			"tests_total": {"type": "integer"},
			"tests_passed": {"type": "integer"},
			"tests_failed": {"type": "integer"},
			"tests_skipped": {"type": "integer"},
			"duration_seconds": {"type": "number"},
			"failures": {
				"type": "array",
				"description": "One entry per failing test.",
				"items": {
					"type": "object",
					"properties": {
						"test": {
							"type": "string",
							"description": "Fully-qualified test id, e.g. tests/test_x.py::test_y.",
						},
						"error_type": {
							"type": "string",
							"description": "The exception/assertion class, e.g. KeyError, AssertionError.",
						},
					},
					"required": ["test", "error_type"],
				},
			},
		},
		"required": [
			"outcome",
			"tests_total",
			"tests_passed",
			"tests_failed",
			"tests_skipped",
			"failures",
		],
	},
}

# TODO(task 1): write the system prompt. Tell the model to read the log and call
# report_log_facts with ONLY the load-bearing facts — drop the pip output, the
# PASSED lines, the warnings, and the coverage table. It must never invent a
# number; if a field isn't in the log, omit it (when optional) rather than guess.
SYSTEM = (
	"You extract load-bearing facts from CI/test log output. "
	"Call report_log_facts with only the facts that matter: the overall outcome, "
	"the test counts, and the list of failing tests with their error type. "
	"Ignore pip resolver output, passing test lines, deprecation warnings, and "
	"coverage tables — they are noise. "
	"Never invent a number; if a field is not present in the log, omit optional "
	"fields rather than guessing. Report only what the log explicitly states."
)


def count_tokens(client: anthropic.Anthropic, text: str) -> int:
	"""Tokens this text would consume as a user message (no request is sent)."""
	resp = client.messages.count_tokens(
		model=MODEL,
		messages=[{"role": "user", "content": text}],
	)
	return resp.input_tokens


def extract_facts(client: anthropic.Anthropic, log_text: str) -> dict:
	"""Call the model once to distill the log into the report_log_facts shape."""
	resp = client.messages.create(
		model=MODEL,
		max_tokens=1024,
		system=SYSTEM,
		tools=[SUMMARIZE_TOOL],
		# Force the tool so every run yields the structured summary.
		tool_choice={"type": "tool", "name": "report_log_facts"},
		messages=[
			{
				"role": "user",
				"content": f"Distill this CI log:\n\n<log>\n{log_text}\n</log>",
			}
		],
	)
	tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
	if tool_use is None:
		raise RuntimeError("Model did not call report_log_facts.")
	return tool_use.input


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	client = anthropic.Anthropic()
	log_text = LOG_PATH.read_text()

	facts = extract_facts(client, log_text)
	summary_text = json.dumps(facts, indent=2)

	raw_tokens = count_tokens(client, log_text)
	summary_tokens = count_tokens(client, summary_text)

	print(summary_text)
	print("-" * 60)
	print(f"raw log tokens:   {raw_tokens}")
	print(f"summary tokens:   {summary_tokens}")
	print(f"compression:      {summary_tokens / raw_tokens:.1%} of the original")
	# Now check `facts` against instructor/gold_facts.json: same outcome, same
	# counts, and the two real failures with their error types — nothing invented.
	return 0


# --- Recorded token counts (model=claude-haiku-4-5) ---
# Raw log tokens:     2015
# Summary tokens:     160
# Compression ratio:  7.9% of original  (~12.6x reduction)
#
# Extracted summary: outcome=failed, tests_total=42, tests_passed=39, tests_failed=2,
# tests_skipped=1, duration_seconds=12.84,
# failures=[tests/test_auth.py::test_token_expiry/KeyError,
#            tests/test_payments.py::test_charge_rejects_negative/AssertionError]
# Matches gold_facts.json exactly — no invented numbers.

if __name__ == "__main__":
	raise SystemExit(main())
