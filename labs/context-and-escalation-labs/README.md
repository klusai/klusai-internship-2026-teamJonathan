# Claude Agent Labs — Exercises 6 & 7

Two more hands-on exercises for the **Claude Code Architect Foundations** exam prep,
picking up where the first five leave off. Same shape as that pack: one folder per exercise,
each with its own `README.md` (goal, tasks, acceptance criteria, stretch goals),
starter code with `TODO` markers, and fixture data. `instructor/` holds the answer key, rubric, and gold labels.

## The two exercises

| # | Folder | Topic |
|---|--------|-------|
| 6 | `ex6_context_management/` | Context management — extract facts from verbose output, use a scratchpad file as external memory, delegate discovery to a subagent so raw tokens never hit the parent's context. |
| 7 | `ex7_escalation_hitl/` | Escalation & human-in-the-loop — when to escalate (policy gap, explicit user request, no progress), confidence-based routing, and a tool-permission approval gate. |

Each builds on the vocabulary from ex1–ex5 (tool descriptions, structured `tool_use`,
gold labels + accuracy, subagents with `AgentDefinition`), so do those first if you
haven't.

## Prerequisites

- **Python 3.11+** (the code uses 3.10+ syntax such as `X | None` and `match`).
- An **Anthropic API key**: `export ANTHROPIC_API_KEY=sk-ant-...`
- For ex6 task3 and ex7 task3, the **Claude Code CLI** on your `PATH` (the Agent SDK
  drives it) — same as ex1.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate

pip install anthropic            # ex6 task1/task2, ex7 task1/task2/task3
pip install claude-agent-sdk     # ex6 task3 (subagents)

export ANTHROPIC_API_KEY=sk-ant-...
```

Each exercise README lists exactly what it needs at the top.

## Model ids used in this pack

`claude-opus-4-8` (default), `claude-sonnet-4-6`, `claude-haiku-4-5` — the same ids
the ex1–ex5 pack uses. Each harness picks a sensible default and tells you where to
swap models to compare.

## The two big ideas

- **Context is a budget you spend, not a free buffer.** ex6 is three ways to keep the
  working context small: distill verbose output to its load-bearing facts, push
  intermediate state into a file, and let a subagent absorb the high-token reading so
  only its summary returns. Every task measures the saving — *record the numbers*.
- **An agent should know the edge of its authority.** ex7 is about routing: recognise
  when a request is outside policy, when the user has asked for a human, or when you've
  stopped making progress — and gate irreversible actions behind a human even when the
  model is confident.

## A note on API specifics

Token counting (`client.messages.count_tokens(...).input_tokens`) and the Message /
tool-use shapes were verified against current Anthropic docs when this pack was built.
The Agent SDK surface (subagents in ex6 task3, the `can_use_tool` permission callback
in ex7 task3) is flagged inline with `⚠️ FLAG` exactly as the ex1 pack does — the SDK
moves fast, so verify against your installed version. ex7 task3 ships a plain-API
fallback that does not depend on any unverified SDK surface.

## Suggested order & timing (~2 hours)

| Order | Exercise | Time | Why here |
|------:|----------|------|----------|
| 1 | **ex6 — Context management** | ~60 min | The mechanics (distill / offload / delegate) that everything long-running leans on. |
| 2 | **ex7 — Escalation & HITL** | ~60 min | Routing and guardrails — builds on ex3's structured errors and ex5's gold-label grading. |
