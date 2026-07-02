# Exercise 1 — Build an agent with the Claude Agent SDK

**Topic:** a full agent loop with tool calling, error handling, and session
management. Practice subagents and explicit context passing.

## Goal

Drive the Claude Agent SDK end to end: a restricted bug-fixer that streams its
trajectory, structured error handling with a spend cap, session capture/resume, and
a parent agent that delegates to two subagents and stitches one report.

## What's here

```text
ex1_agent_sdk/
  buggy/utils.py        calculate_average (crashes on empty list), get_user_name (crashes on missing key/None)
  app/payments.py       make_token (unsalted MD5), charge() (no negative-amount check)
  task1_bugfixer.py     agent: allowed_tools=[Read,Edit,Glob], acceptEdits, streams reasoning->tool->result
  task2_errors.py       point at a missing path; collapse failure to one structured log line; cap spend
  task3_sessions.py     capture session_id, resume it, then rename/tag/list sessions
  task4_subagents.py    security-reviewer (Read,Grep,Glob) + test-writer (Read,Write,Bash); Task in parent only
```

## Setup

```bash
pip install claude-agent-sdk          # the `claude_agent_sdk` Python module
# Requires the Claude Code CLI on PATH. Auth via ANTHROPIC_API_KEY or `claude login`.
```

## ✅ Verified vs. ⚠️ flagged (read before you run)

These were checked against the `claude-agent-sdk-python` docs/repo on the date this
pack was built. **Verify against your installed version** — the SDK moves fast.

- ✅ Package `claude-agent-sdk`; `from claude_agent_sdk import query, ClaudeSDKClient, ClaudeAgentOptions`.
- ✅ `ClaudeAgentOptions(allowed_tools=[...], permission_mode="acceptEdits", cwd=..., max_turns=..., agents={...})`.
- ✅ `query(prompt=..., options=...)` is an async generator; iterate it with `async for`.
- ✅ Model ids: `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`.
- ⚠️ **`max_budget_usd` does not exist.** Use `max_turns` to bound work and read
  `ResultMessage.total_cost_usd` to enforce a dollar ceiling yourself (see
  `task2_errors.py`).
- ⚠️ **Session helpers** `rename_session` / `tag_session` / `list_sessions` were
  reported but not fully confirmed — `task3_sessions.py` imports them defensively
  and degrades gracefully. Capture + resume (`ResultMessage.session_id`,
  `ClaudeAgentOptions(resume=...)`) is the solid path.
- ⚠️ **Subagents** use `AgentDefinition` + `agents={...}`; the exact field names
  (`description`/`prompt`/`tools`/`model`) and whether nested `Task` is structurally
  blocked were not fully confirmed. We enforce "no delegation in subagents" by not
  granting them the `Task` tool.
- ⚠️ `ThinkingBlock` may not be emitted as a message block on all models; the
  renderers handle it if present.

## Tasks

1. **Bug-fixer (task1).** Run `task1_bugfixer.py`. Confirm the agent finds and fixes
   both bugs in `buggy/utils.py` and both in `app/payments.py`, and that you can see
   the reasoning → tool → result stream. Note that with `allowed_tools=[Read,Edit,
   Glob]` it cannot run shell commands.

2. **Errors + spend cap (task2).** Run `task2_errors.py`. It points at a missing
   path, catches the failure, and prints exactly one structured JSON log line. Make
   sure a failure still yields one clean line (not a stack trace). Read the
   `max_budget_usd` flag and implement the real cost ceiling using
   `ResultMessage.total_cost_usd`.

3. **Sessions (task3).** Run `task3_sessions.py`. Capture the `session_id`, resume
   the session, and prove it remembers ("favorite number is 42"). Then make the
   rename/tag/list step work against *your* installed SDK (or document why it isn't
   available and what the real API is).

4. **Subagents (task4).** Run `task4_subagents.py`. The parent must delegate to both
   subagents and produce one stitched report. Confirm the subagents never call
   `Task` (only the parent delegates), and that each subagent only used its allowed
   tools.

## Acceptance criteria

- [ ] task1: all four bugs fixed by the agent (not by you); trajectory streamed.
- [ ] task2: any failure collapses to a single structured log line; a cost ceiling
      is enforced via `total_cost_usd` (with the `max_budget_usd` flag understood).
- [ ] task3: session captured and resumed successfully; rename/tag/list either works
      or is documented as unavailable with the correct alternative.
- [ ] task4: one stitched report with Findings + Tests; subagents stayed within
      their tool allow-lists and did not delegate.

## Stretch goals

- Give task1 a `Write`-only allow-list and watch it fail to edit in place.
- In task4, add a third subagent (e.g. `doc-writer`) and have the parent fan out to
  all three, then merge.
- Replace the streaming `query()` loop in task1 with the `ClaudeSDKClient`
  context-manager API and compare ergonomics.

## Self-check

- Why restrict the bug-fixer to `[Read, Edit, Glob]` instead of giving it `Bash`?
- Where does the dollar cost actually come from, given there's no budget option?
- Why must `Task` live only in the parent? What goes wrong if a subagent can delegate?
