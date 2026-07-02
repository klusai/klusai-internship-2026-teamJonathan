"""Exercise 1, task 2 — error handling and a spend cap.

Point the agent at a path that does not exist, let it fail, and collapse the whole
failure into ONE structured log line (so an operator can grep it). Also cap how much
work the agent can do.

⚠️ FLAG — `max_budget_usd` does NOT exist in the Claude Agent SDK.
The original brief asked for `max_budget_usd`, but verification against the
claude-agent-sdk-python docs/repo found no such option. The real levers are:
  - `max_turns` on ClaudeAgentOptions  — bounds how many agent turns run (the
    practical "budget" knob), and
  - `ResultMessage.total_cost_usd`      — the actual dollar cost, reported AFTER the
    run, which you read and enforce yourself.
This file uses both. If a future SDK version adds a real budget option, swap it in.

Setup:
    pip install claude-agent-sdk
    python task2_errors.py
"""

import asyncio
import json
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query

# A path that does not exist — the agent will try to read it and fail.
MISSING_PATH = "does/not/exist/nowhere.py"
COST_CEILING_USD = 0.50  # we abort/flag if the reported cost exceeds this


async def run() -> dict:
	"""Run the agent and return a single structured record of what happened."""
	record = {
		"event": "agent_run",
		"ok": False,
		"error_type": None,
		"error": None,
		"turns_seen": 0,
		"cost_usd": None,
		"session_id": None,
		"over_budget": False,
	}

	options = ClaudeAgentOptions(
		allowed_tools=["Read", "Glob"],
		# max_turns is the real spend lever — see the FLAG at the top of this file.
		max_turns=4,
		cwd=str(Path(__file__).parent),
	)
	prompt = f"Read the file {MISSING_PATH} and summarize it."

	try:
		async for message in query(prompt=prompt, options=options):
			kind = type(message).__name__
			if kind == "AssistantMessage":
				record["turns_seen"] += 1
			elif kind == "ResultMessage":
				record["session_id"] = getattr(message, "session_id", None)
				record["cost_usd"] = getattr(message, "total_cost_usd", None)
				# Enforce the dollar ceiling ourselves (no built-in cap exists).
				if record["cost_usd"] is not None and record["cost_usd"] > COST_CEILING_USD:
					record["over_budget"] = True
		record["ok"] = not record["over_budget"]
	except Exception as exc:  # noqa: BLE001 — task: collapse ANY failure to one line
		# TODO(task 2): decide which exception types are worth distinguishing
		# (e.g. CLINotFoundError vs. process errors) instead of catching them all.
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)

	return record


async def main() -> int:
	record = await run()
	# One structured log line — the whole point of the task.
	print(json.dumps(record))
	return 0 if record["ok"] else 1


if __name__ == "__main__":
	raise SystemExit(asyncio.run(main()))
