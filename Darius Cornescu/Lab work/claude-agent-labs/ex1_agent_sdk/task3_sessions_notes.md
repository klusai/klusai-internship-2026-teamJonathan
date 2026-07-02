# task3 — session management, verified against the installed SDK

SDK: `claude-agent-sdk 0.2.110` (Python 3.13).

## Capture + resume (the solid path)

- Capture: read `ResultMessage.session_id` from the first `query(...)` run.
- Resume: `ClaudeAgentOptions(resume=<session_id>)` on a follow-up `query(...)`.
- Result: the resumed turn recalled the fact — answered **"Your favorite number is 42."**
- Branch instead of continue: `ClaudeAgentOptions(fork_session=True)` (documented alternative).

## rename / tag / list — they DO exist in 0.2.110 (contrary to the README flag)

The README warned these helpers "were reported but not fully confirmed." In this version
they are importable from `claude_agent_sdk`, but their **signatures differ** from the
original brief. Verified via `inspect.signature`:

| Helper | Real signature | Notes |
|---|---|---|

| `rename_session` | `(session_id: str, title: str, directory=None) -> None` | appends a custom-title entry |
| `tag_session` | `(session_id: str, tag: str \| None, directory=None) -> None` | pass `None` to clear the tag |
| `list_sessions` | `(directory=None, limit=None, offset=0, include_worktrees=True) -> list[SDKSessionInfo]` | **no `tag=` filter** |

The original starter called `list_sessions(tag=TAG)`, which raises
`TypeError: list_sessions() got an unexpected keyword argument 'tag'`. The correct usage
is to call `list_sessions()` and filter on the returned objects' `.tag` field in Python.

`SDKSessionInfo` fields: `session_id, summary, last_modified, file_size, custom_title,
first_prompt, git_branch, cwd, tag, created_at`.

## What this proves

Sessions are persisted locally by the Claude Code CLI (session store on disk), and the SDK
exposes read/annotate helpers over that store — they are not a network API. Always verify a
helper's signature against your installed version; the surface moves between releases.
