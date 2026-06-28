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

from claude_agent_sdk import (
	CLIConnectionError,
	CLIJSONDecodeError,
	CLINotFoundError,
	ClaudeAgentOptions,
	ClaudeSDKError,
	ProcessError,
	query,
)

# A path that does not exist — the agent will try to read it and fail.
MISSING_PATH = "does/not/exist/nowhere.py"
COST_CEILING_USD = 0.50  # we abort/flag if the reported cost exceeds this


async def run() -> dict:
	"""Run the agent and return a single structured record of what happened."""
	record = {
		"event": "agent_run",
		"ok": False,
		"error_category": None,
		"error_type": None,
		"error": None,
		"details": None,
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
	# Distinguish failures by what an operator would DO about each one. Order matters:
	# catch the most-specific subclass first (CLINotFoundError < CLIConnectionError <
	# ClaudeSDKError), or the broader clause would shadow it.
	except CLINotFoundError as exc:
		# Setup problem: the Claude Code CLI isn't installed or isn't on PATH.
		# Operator action: install the CLI / fix PATH.
		record["error_category"] = "cli_not_found"
		record["error_type"] = type(exc).__name__
		# str(exc) already includes the searched path, e.g.
		# "Claude Code not found: /usr/bin/claude" — no separate detail to capture.
		record["error"] = str(exc)
	except CLIConnectionError as exc:
		# Couldn't reach or talk to the CLI process — often transient/retryable.
		record["error_category"] = "connection"
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
	except ProcessError as exc:
		# The CLI ran but exited non-zero (auth failure, bad flag, crash). The exit
		# code and stderr are the most useful things to capture for debugging.
		record["error_category"] = "process"
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
		record["details"] = {
			"exit_code": getattr(exc, "exit_code", None),
			"stderr": getattr(exc, "stderr", None),
		}
	except CLIJSONDecodeError as exc:
		# The CLI emitted output the SDK couldn't parse — usually an SDK/CLI version
		# skew. Capture the offending line so you can see what didn't parse.
		record["error_category"] = "decode"
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
		record["details"] = {"line": getattr(exc, "line", None)}
	except ClaudeSDKError as exc:
		# Any other error from the SDK family — future-proofs us against new
		# subclasses we haven't enumerated here.
		record["error_category"] = "sdk"
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
	except Exception as exc:  # noqa: BLE001 — last resort: a bug on OUR side, not the SDK
		# Not an SDK error at all (logic bug, asyncio issue, etc.). Flag it distinctly
		# so it isn't mistaken for an agent/infrastructure failure.
		record["error_category"] = "unexpected"
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
