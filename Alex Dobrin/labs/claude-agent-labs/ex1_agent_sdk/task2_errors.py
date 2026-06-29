"""Exercise 1, task 2 — error handling and a spend cap.

Point the agent at a path that does not exist, let it fail, and collapse the whole
failure into ONE structured log line (so an operator can grep it). Also cap how much
work the agent can do.

Cost ceiling — `max_budget_usd` IS available as of claude-agent-sdk 0.2.110.
(An earlier brief flagged it as missing; that is no longer true for this version.)
The SDK moves fast, so we use a layered approach:
  - `max_budget_usd` on ClaudeAgentOptions — the PRIMARY ceiling. Forwarded to the
    CLI as `--max-budget-usd`; the run is STOPPED if exceeded and the final
    ResultMessage comes back with is_error=True and an `error_max_budget_usd`
    subtype. This is a real, enforced cap (not just an after-the-fact reading).
  - `max_turns` on ClaudeAgentOptions — secondary bound on how many agent turns run.
  - `ResultMessage.total_cost_usd` — the actual dollar cost, reported AFTER the run;
    we keep this as a belt-and-suspenders cross-check.
If your installed SDK lacks `max_budget_usd`, the total_cost_usd check still flags
overruns reactively.

Setup:
    pip install claude-agent-sdk
    python task2_errors.py

Simulate infrastructure failures (to exercise the typed except branches):
    python task2_errors.py --simulate notfound   # -> CLINotFoundError
    python task2_errors.py --simulate fail        # -> ProcessError (exit_code/stderr)
Both work by pointing `cli_path` at a bogus / failing binary; your real Claude
Code install is untouched.
"""

import argparse
import asyncio
import json
import os
import tempfile
from pathlib import Path

from claude_agent_sdk import (
	ClaudeAgentOptions,
	CLIJSONDecodeError,
	CLINotFoundError,
	ProcessError,
	query,
)

# A path that does not exist — the agent will try to read it and fail.
MISSING_PATH = "does/not/exist/nowhere.py"
COST_CEILING_USD = 0.001  # we abort/flag if the reported cost exceeds this


def _simulated_cli_path(mode: str) -> str:
	"""Return a `cli_path` that deterministically forces a given failure.

	`notfound` points at a path that doesn't exist (-> CLINotFoundError).
	`fail` writes a throwaway executable that exits non-zero (-> ProcessError).
	"""
	if mode == "notfound":
		return "/no/such/claude"
	if mode == "fail":
		fd, path = tempfile.mkstemp(prefix="fake_claude_")
		with os.fdopen(fd, "w") as f:
			f.write("#!/bin/sh\necho 'simulated CLI failure' >&2\nexit 3\n")
		os.chmod(path, 0o755)
		return path
	raise ValueError(f"unknown simulate mode: {mode!r}")


async def run(simulate: str | None = None) -> dict:
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
		# PRIMARY ceiling: the CLI stops the run if cost exceeds this — see docstring.
		max_budget_usd=COST_CEILING_USD,
		# Secondary bound on how many agent turns run.
		max_turns=4,
		cwd=str(Path(__file__).parent),
		# When simulating, override the CLI binary to force an infrastructure failure.
		cli_path=_simulated_cli_path(simulate) if simulate else None,
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
				# PRIMARY: the CLI stops the run and returns this subtype when
				# max_budget_usd is exceeded.
				subtype = str(getattr(message, "subtype", "") or "")
				if getattr(message, "is_error", False) and subtype.startswith("error_max_budget"):
					record["over_budget"] = True
				# Belt-and-suspenders: also flag if the reported cost overshot anyway.
				elif record["cost_usd"] is not None and record["cost_usd"] > COST_CEILING_USD:
					record["over_budget"] = True
		record["ok"] = not record["over_budget"]
		if record["over_budget"]:
			record["error"] = "agent exceeded budget"
	# Distinguish a failure only when an operator's NEXT ACTION differs. Each branch
	# below maps to a different fix; everything else collapses to the catch-all.
	# NOTE: the missing FILE (MISSING_PATH) does NOT land here — the agent's Read tool
	# fails inside the run and comes back as tool output, so the run completes normally.
	# These handlers are for infrastructure failures, not file-not-found.
	except CLINotFoundError as exc:
		# Claude Code CLI is missing / not on PATH — environment problem, not retryable.
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
		record["cli_path"] = getattr(exc, "cli_path", None)
	except ProcessError as exc:
		# CLI started but exited non-zero — capture exit_code/stderr; may be transient.
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
		record["exit_code"] = getattr(exc, "exit_code", None)
		record["stderr"] = getattr(exc, "stderr", None)
	except CLIJSONDecodeError as exc:
		# CLI output didn't parse — almost always an SDK/CLI version mismatch.
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)
		record["bad_line"] = getattr(exc, "line", None)
	except Exception as exc:  # noqa: BLE001 — genuine safety net for unknown failures.
		record["error_type"] = type(exc).__name__
		record["error"] = str(exc)

	return record


async def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--simulate",
		choices=["notfound", "fail"],
		help="force an infrastructure failure to exercise the typed except branches",
	)
	args = parser.parse_args()

	record = await run(simulate=args.simulate)
	# One structured log line — the whole point of the task.
	print(json.dumps(record))
	return 0 if record["ok"] else 1


if __name__ == "__main__":
	raise SystemExit(asyncio.run(main()))
