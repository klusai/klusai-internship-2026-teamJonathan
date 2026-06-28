"""Exercise 6, task 2 — a scratchpad file as external memory.

You have 12 verbose incident reports to triage. The naive approach keeps every
record in one growing conversation, so by record 12 the model re-reads records
1-11 on every call — the context (and the per-call token bill) grows with each
step. The fix: process each record in its OWN independent call, write a one-line
finding to a scratchpad file, and let that file — not the conversation — be the
memory. The per-call context then stays flat no matter how many records there are,
and the final synthesis reads the tiny scratchpad instead of all 12 raw records.

The point of the exercise is the shape of the cost: per-step tokens stay O(1) with
the scratchpad and grow with the naive approach. Record both totals.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task2_scratchpad.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-haiku-4-5"

HERE = Path(__file__).parent
RECORDS_PATH = HERE / "fixtures" / "triage_records.json"
SCRATCHPAD_PATH = HERE / "scratchpad.md"

SYSTEM = (
	"You are an incident triage assistant. Assign exactly one severity:\n"
	"  P1 = outage, data loss, or security exposure (act now)\n"
	"  P2 = degraded or partial; a workaround exists\n"
	"  P3 = cosmetic, a single user, or a how-to question\n"
	"Call `triage` with the severity and a one-line finding (max ~12 words)."
)

# A fixed instruction prefix, so each per-record call sends the same overhead plus
# exactly one record. Keeping this constant is what makes per-step cost flat.
PER_RECORD_PROMPT = "Triage this single incident. Use only the text below."

TRIAGE_TOOL = {
	"name": "triage",
	"description": "Record the severity and a one-line finding for one incident.",
	"input_schema": {
		"type": "object",
		"properties": {
			"severity": {"type": "string", "enum": ["P1", "P2", "P3"]},
			"one_line": {"type": "string", "description": "<= ~12 words."},
		},
		"required": ["severity", "one_line"],
	},
}


def _render(record: dict) -> str:
	"""The user message for one record — note it contains ONLY this record."""
	return f"{PER_RECORD_PROMPT}\n\n<incident id={record['id']}>\n{record['body']}\n</incident>"


def count_tokens(client: anthropic.Anthropic, text: str) -> int:
	resp = client.messages.count_tokens(
		model=MODEL,
		messages=[{"role": "user", "content": text}],
	)
	return resp.input_tokens


def triage_one(client: anthropic.Anthropic, record: dict) -> dict:
	"""Triage ONE record in an independent call (no prior records in context)."""
	resp = client.messages.create(
		model=MODEL,
		max_tokens=256,
		system=SYSTEM,
		tools=[TRIAGE_TOOL],
		tool_choice={"type": "tool", "name": "triage"},
		messages=[{"role": "user", "content": _render(record)}],
	)
	tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
	if tool_use is None:
		raise RuntimeError(f"No triage for record {record['id']}.")
	return {"id": record["id"], **tool_use.input}


def append_finding(scratchpad_path: Path, finding: dict) -> None:
	"""Append one finding as a single markdown line.

	TODO(task 2): write a line like `- P1  #1  one-line finding` to the scratchpad
	(open in append mode so each record adds exactly one line). This file — not the
	conversation — is the durable memory.
	"""
	# TODO: implement
	raise NotImplementedError


def synthesize(client: anthropic.Anthropic, scratchpad_path: Path) -> str:
	"""Produce the end-of-shift summary from the scratchpad ALONE.

	TODO(task 2): read scratchpad.md (NOT the raw records) and ask the model for a
	short shift summary: the count per severity and which incidents are P1. The
	whole point is that this call's input is the small scratchpad, not 12 logs.
	"""
	# TODO: implement
	raise NotImplementedError


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	client = anthropic.Anthropic()
	records = json.loads(RECORDS_PATH.read_text())["records"]

	# Start each run with a fresh scratchpad.
	SCRATCHPAD_PATH.write_text("# Triage scratchpad\n\n")

	scratchpad_step_tokens: list[int] = []  # what we actually send per record
	naive_step_tokens: list[int] = []  # what we WOULD send if we never offloaded
	naive_prefix = ""

	for record in records:
		finding = triage_one(client, record)
		append_finding(SCRATCHPAD_PATH, finding)
		print(f"  #{finding['id']:>2}  {finding['severity']}  {finding['one_line']}")

		# Measurement only (count_tokens sends no generation request).
		scratchpad_step_tokens.append(count_tokens(client, _render(record)))
		naive_prefix += f"\n\n<incident id={record['id']}>\n{record['body']}\n</incident>"
		naive_step_tokens.append(count_tokens(client, PER_RECORD_PROMPT + naive_prefix))

	summary = synthesize(client, SCRATCHPAD_PATH)
	print("\n=== shift summary ===")
	print(summary)

	# What did each strategy cost in INPUT tokens across the 12 steps?
	final_context_scratchpad = count_tokens(client, SCRATCHPAD_PATH.read_text())
	final_context_naive = count_tokens(client, naive_prefix)
	print("\n" + "-" * 60)
	print(f"per-step tokens (scratchpad): {scratchpad_step_tokens}")
	print(f"per-step tokens (naive):      {naive_step_tokens}")
	print(f"total input tokens, scratchpad path: {sum(scratchpad_step_tokens)}")
	print(f"total input tokens, naive path:      {sum(naive_step_tokens)}")
	print(f"final synthesis reads (scratchpad):  {final_context_scratchpad} tokens")
	print(f"  vs. re-reading all 12 raw records: {final_context_naive} tokens")
	# The scratchpad per-step numbers should be flat; the naive ones climb. The
	# final synthesis should read a fraction of what the raw records would cost.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
