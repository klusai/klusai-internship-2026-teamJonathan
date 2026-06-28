# Exercise 6 — Context management patterns

**Topic:** keeping an agent's working context small under real token pressure —
distilling verbose output to its load-bearing facts, using a scratchpad file as
external memory, and delegating high-token discovery to a subagent.

## Goal

Three techniques, each measured. Take a noisy CI log and extract only the facts
that matter (and prove the compression). Triage a batch of records through a
scratchpad file so per-step context stays flat instead of growing. Send a subagent
to read a small codebase and return one compact answer, so the parent's context
never holds the raw files.

## What's here

```
ex6_context_management/
  task1_extract_facts.py        distill a verbose CI log; measure raw vs summary tokens
  task2_scratchpad.py           triage 12 records via a scratchpad file; per-step tokens stay flat
  task3_delegate_discovery.py   parent delegates discovery to a `code-scout` subagent
  fixtures/verbose_log.txt      a noisy pytest run (2 failures buried in the noise)
  fixtures/triage_records.json  12 verbose incident reports to triage one at a time
  repo/                         small codebase for task3 (real retry limit + a decoy)
```

## Setup

```bash
pip install anthropic          # task1, task2
pip install claude-agent-sdk   # task3 (subagents; needs the Claude Code CLI on PATH)
export ANTHROPIC_API_KEY=sk-ant-...
```

## ✅ Verified vs. ⚠️ flagged (read before you run)

- ✅ Token counting: `client.messages.count_tokens(model=..., messages=...)` returns
  `.input_tokens`. It sends no generation request and is the right way to measure
  size — don't estimate with `tiktoken` (it's the wrong tokenizer for Claude).
- ✅ Structured extraction via `tool_use` + `tool_choice={"type":"tool",...}` — same
  pattern as ex3/ex4.
- ⚠️ **Subagents (task3)** use `AgentDefinition` + `agents={...}`, same as ex1 task4 —
  the exact field names and whether the delegation tool is `"Task"` or `"Agent"` in
  your installed SDK were not fully confirmed. The file flags this inline.

## Tasks

1. **Extract facts (task1).** Open `task1_extract_facts.py` and write the `SYSTEM`
   prompt so the model calls `report_log_facts` with only the load-bearing facts
   from `fixtures/verbose_log.txt` — outcome, counts, and the failing tests with
   their error types — and never invents a number. Run it and **record the raw-log
   token count and the summary token count.** The ratio is the point.

2. **Scratchpad as memory (task2).** In `task2_scratchpad.py`, implement
   `append_finding` (one markdown line per record) and `synthesize` (read the
   scratchpad *only*, not the raw records). Run it and **record the two totals**:
   per-step tokens for the scratchpad path (should be flat) vs. the naive path
   (should climb), and how many tokens the final synthesis reads vs. re-reading all
   12 records.

3. **Delegate discovery (task3).** In `task3_delegate_discovery.py`, write the
   `code-scout` prompt so it traces the *live* retry policy (config + client, not
   the legacy client) and returns one compact answer. Run it and confirm the parent
   reported `MAX_RETRIES = 5` from `config/settings.py` — not the legacy decoy `3` —
   while the parent itself never read the files.

## Acceptance criteria

- [ ] task1: summary captures the outcome, all four counts, and both real failures
      (`test_token_expiry`/KeyError, `test_charge_rejects_negative`/AssertionError)
      with nothing invented; raw and summary token counts both recorded.
- [ ] task2: 12 findings written to `scratchpad.md`; severities match the gold; the
      scratchpad per-step token counts are flat and the naive counts grow; both
      totals recorded.
- [ ] task3: parent reports the retry value `5` and `config/settings.py` as its
      source (not the legacy `3`); the parent delegated rather than reading files.

## Stretch goals

- task1: feed the *distilled* summary into a follow-up "what should I fix first?"
  call and compare its cost to feeding the whole raw log. That delta is the payoff.
- task2: add a "naive baseline" run that actually triages all 12 records in one
  growing conversation, and compare the real token bill to the scratchpad run.
- task3: add a second subagent (`doc-writer`) that turns the scout's answer into a
  one-paragraph note, and have the parent fan out to both — still without reading
  any file itself.

## Self-check

- In task1, why force the tool call instead of asking for prose? (What guarantees
  the summary stays small and parseable?)
- In task2, what exactly is the "memory" — the conversation, or the file? What
  breaks if you accidentally pass previous records into each per-record call?
- In task3, the parent has no Read/Grep/Glob. Why is *removing* tools the mechanism
  that keeps the raw files out of its context?
