"""Exercise 6, task 3 — delegate discovery to a subagent.

Answering "what is the effective retry limit and where is it set?" means reading
several files in repo/ — config, the live client, a legacy client, tests. If the
PARENT agent reads them all, every byte lands in the parent's context. Instead, the
parent delegates the reading to a `code-scout` subagent. The subagent burns the
tokens reading files and returns ONE compact answer; the parent's context only ever
holds that answer, not the file contents. This is context isolation: the expensive
reading happens in a context you throw away.

There's a decoy on purpose — legacy/old_client.py hardcodes `retries = 3`, but the
live policy is config.settings.MAX_RETRIES. A scout that greps for "retries" and
stops will report the wrong number; the right answer needs actually tracing the
live client to config.

⚠️ FLAG — verify against your installed claude-agent-sdk (same caveats as ex1):
  1. `AgentDefinition` fields (description / prompt / tools / model) were not fully
     confirmed in docs; adjust if construction fails.
  2. The delegation tool is granted to the PARENT only. It is named "Task" in the
     ex1 pack; some SDK versions expose it as "Agent". If the parent never
     delegates, try swapping "Task" -> "Agent" in `allowed_tools` below.
  3. We enforce "the subagent does the reading, the parent does not" by giving the
     parent no Read/Grep/Glob — only the delegation tool.

Setup:
    pip install claude-agent-sdk
    python task3_delegate_discovery.py
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query

HERE = Path(__file__).parent
REPO = HERE / "repo"

# TODO(task 3): write the scout's prompt. It must (a) trace the LIVE retry policy —
# follow config/settings.py and client/http.py, not the legacy client — and
# (b) return a single compact line: the value, the file:line where it is defined,
# and which file reads it. Tell it NOT to dump file contents back; only the answer.
CODE_SCOUT = AgentDefinition(
	description="Finds one fact in a codebase and returns a compact answer. Read-only.",
	prompt="",  # TODO: fill in (the discovery contract above)
	tools=["Read", "Grep", "Glob"],
	model="sonnet",
)

# The parent delegates and reports — it has NO file tools, so it cannot read repo/
# itself. Its context only ever sees the scout's compact answer.
PARENT_PROMPT = (
	"Find the effective HTTP retry limit for the app in ./repo.\n"
	"You do NOT have file-reading tools. Delegate the investigation to the "
	"'code-scout' subagent and wait for its answer.\n"
	"Then report, in two lines: the retry value, and the file:line where it is "
	"defined. Do not ask the scout to paste file contents."
)


async def main() -> int:
	options = ClaudeAgentOptions(
		# Parent gets ONLY the delegation tool — no Read/Grep/Glob. (Try "Agent"
		# instead of "Task" if your SDK version names it that way.)
		allowed_tools=["Task"],
		agents={"code-scout": CODE_SCOUT},
		permission_mode="acceptEdits",
		cwd=str(REPO),
	)

	parent_text_chars = 0  # how much raw text the PARENT actually saw
	async for message in query(prompt=PARENT_PROMPT, options=options):
		kind = type(message).__name__
		if kind == "AssistantMessage":
			for block in getattr(message, "content", []):
				btype = type(block).__name__
				if btype == "TextBlock":
					print(block.text)
					parent_text_chars += len(block.text)
				elif btype == "ToolUseBlock":
					print(f"[delegate] {block.name} -> {block.input}")
		elif kind == "ResultMessage":
			print(f"[done] cost_usd={getattr(message, 'total_cost_usd', None)}")

	print("-" * 60)
	print(f"parent saw ~{parent_text_chars} chars of text (NOT the repo files).")
	# Confirm against instructor/gold_discovery.json: value 5, defined in
	# config/settings.py, read by client/http.py — and that the scout did not fall
	# for the legacy `retries = 3` decoy.
	return 0


if __name__ == "__main__":
	raise SystemExit(asyncio.run(main()))
