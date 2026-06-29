"""Exercise 1, task 1 — a bug-fixer agent built on the Claude Agent SDK.

The agent is restricted to Read, Edit, and Glob, runs in acceptEdits mode (so it
applies edits without asking), and we stream its trajectory: reasoning -> tool call
-> tool result.

Setup:
    pip install claude-agent-sdk     # provides the `claude_agent_sdk` module
    # Claude Code CLI must be installed and on PATH; auth via ANTHROPIC_API_KEY
    # or `claude login`.
    python task1_bugfixer.py

VERIFIED against the claude-agent-sdk-python docs/repo:
  - import path `claude_agent_sdk`, `query()` async generator, `ClaudeAgentOptions`
  - `allowed_tools` is a list of tool-name strings; `permission_mode="acceptEdits"`
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query

HERE = Path(__file__).parent

PROMPT = (
	"Two files in this project have bugs.\n"
	"1. buggy/utils.py — calculate_average crashes on an empty list; get_user_name "
	"crashes on a missing 'name' key or a None user.\n"
	"2. app/payments.py — make_token uses unsalted MD5; charge() does not validate "
	"that the amount is positive.\n\n"
	"Find them with Glob/Read and fix them with Edit. Make calculate_average return "
	"0.0 for an empty list, make get_user_name handle missing/None safely, and add a "
	"positive-amount check to charge(). Keep changes minimal."
)


def render(message) -> None:
	"""Stream the agent's trajectory: reasoning -> tool -> result.

	The SDK yields message objects; we switch on the class name so we don't have to
	import every type. AssistantMessage carries content blocks (text / thinking /
	tool_use); tool results arrive on a UserMessage as ToolResultBlock; the final
	ResultMessage carries cost and the session id.
	"""
	kind = type(message).__name__
	if kind == "AssistantMessage":
		for block in getattr(message, "content", []):
			btype = type(block).__name__
			if btype == "TextBlock":
				print(f"[reasoning] {block.text}")
			elif btype == "ThinkingBlock":  # may not be emitted on all models
				print(f"[thinking] {getattr(block, 'thinking', '')}")
			elif btype == "ToolUseBlock":
				print(f"[tool] {block.name} -> {block.input}")
	elif kind == "UserMessage":
		for block in getattr(message, "content", []):
			if type(block).__name__ == "ToolResultBlock":
				print(f"[result] {getattr(block, 'content', '')}")
	elif kind == "ResultMessage":
		cost = getattr(message, "total_cost_usd", None)
		print(f"[done] session={getattr(message, 'session_id', '?')} cost_usd={cost}")


async def main() -> None:
	options = ClaudeAgentOptions(
		allowed_tools=["Read", "Write", "Glob"],
		permission_mode="acceptEdits",
		cwd=str(HERE),
		# TODO(task 1): try adding "Write" or removing "Edit" and watch how the
		# agent's options change (e.g. it can no longer modify files).
	)
	async for message in query(prompt=PROMPT, options=options):
		render(message)


if __name__ == "__main__":
	asyncio.run(main())
