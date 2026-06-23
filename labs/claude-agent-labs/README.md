# Claude Agent Labs

A hands-on lab pack covering the first five Claude exam-prep topics, one folder per
exercise. Each exercise has its own `README.md` (goal, tasks, acceptance criteria,
stretch goals), starter code with `TODO` markers, and fixture data. Work through them
in order; check yourself against the printable worksheet as you go.

## The five exercises

| # | Folder | Topic |
|---|--------|-------|
| 1 | `ex1_agent_sdk/` | Build an agent with the Claude Agent SDK — tool calling, error handling, sessions, subagents. |
| 2 | `ex2_claude_code_config/` | Configure Claude Code — CLAUDE.md hierarchy, `.claude/rules/`, skills with `context: fork` + `allowed-tools`, MCP. |
| 3 | `ex3_mcp_tools/` | Design and test MCP tools — disambiguating descriptions, structured errors, ambiguity testing. |
| 4 | `ex4_extraction_pipeline/` | Extraction with `tool_use` — JSON schemas, validation/retry, nullable fields, Message Batches API. |
| 5 | `ex5_prompt_engineering/` | Prompt engineering — few-shot, explicit review criteria, multi-pass review. |

`instructor/` holds the answer key, rubric, and gold labels — for whoever is grading,
not for the student doing the labs.

## Prerequisites

- **Python 3.11+** (the code uses 3.10+ syntax such as `X | None` and `match`).
- An **Anthropic API key**: `export ANTHROPIC_API_KEY=sk-ant-...`
- For exercise 1, the **Claude Code CLI** on your `PATH` (the Agent SDK drives it).
- For exercise 2, **Claude Code** itself (that's the thing you're configuring).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate

# Install per-exercise as you go (or all at once):
pip install anthropic jsonschema      # ex3, ex4, ex5
pip install mcp                        # ex3 (FastMCP server)
pip install claude-agent-sdk           # ex1 (the agent SDK)

export ANTHROPIC_API_KEY=sk-ant-...
```

Each exercise README lists exactly what it needs at the top.

## Model ids used in this pack

`claude-opus-4-8` (default), `claude-sonnet-4-6`, `claude-haiku-4-5`. The harnesses
pick a sensible default per task and tell you where to swap models to compare.

## Suggested order & timing (~4–5 hours total)

| Order | Exercise | Time | Why here |
|------:|----------|------|----------|
| 1 | **ex2 — Claude Code config** | ~30 min | Lightest; no API spend; warms you up on the mental model. |
| 2 | **ex3 — MCP tools** | ~45 min | Tool descriptions & structured errors — the vocabulary the rest builds on. |
| 3 | **ex4 — Extraction pipeline** | ~60 min | `tool_use` + schemas + batch; the workhorse pattern. |
| 4 | **ex5 — Prompt engineering** | ~60 min | Few-shot, criteria, multi-pass — pure prompting leverage. |
| 5 | **ex1 — Agent SDK** | ~75 min | The capstone: pulls tools, errors, sessions, and subagents together. |

(If you prefer to start with the headline topic, do ex1 first — it's self-contained.)

## A note on API specifics

The Agent SDK and API details in this pack (model strings, the `query()` loop,
subagent rules, session functions, the Message Batches API) were verified against
current Anthropic docs when the pack was built. A few Agent SDK details could **not**
be fully confirmed and are flagged inline with `⚠️ FLAG` — most importantly that
**`max_budget_usd` does not exist** (use `max_turns` + `ResultMessage.total_cost_usd`)
and that the `rename_session`/`tag_session`/`list_sessions` helpers must be verified
against your installed SDK version. See `ex1_agent_sdk/README.md`.

## Worksheet

`Claude-Agent-Labs-Worksheet.docx` is a printable companion — one section per
exercise with answer lines, reflection prompts, and checkbox self-checks. Print it
and fill it in as you work.
