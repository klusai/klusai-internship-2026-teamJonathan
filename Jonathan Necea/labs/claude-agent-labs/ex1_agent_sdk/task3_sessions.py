"""Exercise 1, task 3 — sessions: capture, resume, then rename / tag / list.

Flow:
  1. Run a first turn and capture the `session_id` from the ResultMessage.
  2. Resume that session for a follow-up turn (it remembers the first turn).
  3. Rename it, tag it, and list sessions by tag.

⚠️ FLAG — verify the session-management API against YOUR installed SDK version.
Steps 1–2 (capture `ResultMessage.session_id`; resume via
`ClaudeAgentOptions(resume=<id>)`) are the well-supported path; `fork_session=True`
is the documented way to branch instead of continue. Step 3 — module-level
`rename_session` / `tag_session` / `list_sessions` helpers — was reported by our
research but could NOT be fully confirmed, and may differ by version (it may live
behind a session-store API, or be CLI-only). This file imports them defensively and
prints guidance if they're absent, so the rest of the task still runs.

Setup:
    pip install claude-agent-sdk
    python task3_sessions.py
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query

TAG = "labs-ex1"


async def first_turn() -> str | None:
	"""Run one turn; return its session_id."""
	session_id = None
	# max_turns must leave room to reach a natural end-of-turn. With max_turns=1 the
	# run hits the cap first, and the SDK RAISES that error result (error_max_turns)
	# instead of yielding a ResultMessage — so session_id is never captured. A simple
	# no-tool ack needs ~3 turns here; 5 gives margin at no extra cost (the model stops
	# on its own once it has answered).
	options = ClaudeAgentOptions(allowed_tools=[], max_turns=5)
	async for message in query(
		prompt="Remember this fact for later: my favorite number is 42.",
		options=options,
	):
		if type(message).__name__ == "ResultMessage":
			session_id = getattr(message, "session_id", None)
	print(f"captured session_id={session_id}")
	return session_id


async def resume_turn(session_id: str) -> None:
	"""Resume the captured session and prove it remembers."""
	# FLAG: `resume=` is the expected resume mechanism; if your SDK uses a different
	# name, check ClaudeAgentOptions for `resume` / `continue_conversation` /
	# `fork_session`.
	options = ClaudeAgentOptions(resume=session_id, allowed_tools=[], max_turns=5)
	async for message in query(prompt="What is my favorite number?", options=options):
		if type(message).__name__ == "AssistantMessage":
			for block in getattr(message, "content", []):
				if type(block).__name__ == "TextBlock":
					print(f"resumed answer: {block.text}")


def manage_sessions(session_id: str) -> None:
	"""Rename, tag, and list by tag — guarded because these helpers are unverified."""
	try:
		from claude_agent_sdk import list_sessions, rename_session, tag_session
	except ImportError:
		print(
			"\n[FLAG] rename_session / tag_session / list_sessions are not importable "
			"from claude_agent_sdk in this version.\n"
			"       Verify the session-management API for your installed SDK (it may "
			"be a session-store API or CLI-only), then wire it in here."
		)
		return

	# These helpers DO exist in this SDK version (0.2.110); they read/write the local
	# on-disk session store. IMPORTANT: list_sessions() has NO `tag=` filter — it
	# returns ALL sessions, so filter by the `.tag` field yourself.
	rename_session(session_id, "favorite-number-demo")  # -> SDKSessionInfo.custom_title
	tag_session(session_id, TAG)                         # -> SDKSessionInfo.tag
	tagged = [si for si in list_sessions() if si.tag == TAG]
	print(f"\nsessions tagged {TAG!r}: {len(tagged)} found")
	for si in tagged:
		marker = "  <- this run" if si.session_id == session_id else ""
		print(f"  {si.session_id}  title={si.custom_title!r}{marker}")


async def main() -> int:
	session_id = await first_turn()
	if not session_id:
		print("No session_id captured — cannot resume.")
		return 1
	await resume_turn(session_id)
	manage_sessions(session_id)
	return 0


if __name__ == "__main__":
	raise SystemExit(asyncio.run(main()))
