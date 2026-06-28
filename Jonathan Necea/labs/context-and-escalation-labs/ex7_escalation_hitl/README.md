# Exercise 7 — Escalation & human-in-the-loop

**Topic:** knowing the edge of the agent's authority — when to escalate (policy
gap, explicit user request, no progress), routing actions by confidence, and gating
irreversible actions behind a human at the tool layer.

## Goal

Three routing decisions. Classify support situations as HANDLE vs ESCALATE and name
the trigger (and measure how a precise policy beats a vague one). Build a
confidence-based router with a hard guardrail so a confident model still can't
auto-execute an irreversible action. Wire an approval gate into a real agent loop so
high-risk tool calls wait for a human.

## What's here

```
ex7_escalation_hitl/
  task1_escalation_triggers.py   classify HANDLE/ESCALATE + trigger; measure vague vs precise policy
  task2_confidence_routing.py    route() by confidence band + a HIGH-RISK guardrail (graded truth table)
  task3_hitl_gate.py             approval gate in a manual agent loop; high-risk tools need a human
  scenarios.json                 12 situations with inline gold (2 debatable)
  routing_tasks.json             8 candidate actions to run the live router on
```

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## ✅ Verified vs. ⚠️ flagged (read before you run)

- ✅ Structured `tool_use` + forced `tool_choice`, the manual agentic loop, and
  `tool_result` with `is_error` — all the verified surface from ex3/ex4.
- ⚠️ **task3's Agent SDK mapping** (the `can_use_tool` permission callback) is flagged
  at the bottom of the file: the callback exists, but whether it returns a bool or a
  `PermissionResult*` object is version-dependent. The graded path is the plain-API
  loop, which uses no unverified surface.

## The three escalation triggers

An agent should escalate when one of these is true — otherwise HANDLE:

- **policy_gap** — the request is outside what the agent is authorized to do (over a
  refund limit, account deletion, legal advice).
- **user_request** — the user explicitly asked for a human.
- **no_progress** — standard steps are exhausted, or the issue keeps recurring.

## Tasks

1. **Escalation triggers (task1).** Write the `POLICY` system prompt in
   `task1_escalation_triggers.py` so the classifier matches the inline gold in
   `scenarios.json`. Run it with the empty policy first and **record the accuracy**,
   then write a real policy and run again — the delta is the point. Cases 11 and 12
   are debatable and are not scored against you.

2. **Confidence routing (task2).** Implement `route(confidence, action_type)` so it
   passes the `ROUTE_CASES` truth table: the confidence bands *and* the guardrail
   that floors every HIGH_RISK action at REVIEW (never AUTO). Then run Part B and
   watch the live model's confidences route through it — confirm no high-risk row
   shows AUTO even when the model is sure.

3. **HITL gate (task3).** Implement `requires_approval(tool_name)` so high-risk
   tools are gated and read-only tools run automatically. Run it (default denies
   high-risk; `HITL_AUTO=allow` to approve for a demo) and confirm from the audit
   that `issue_refund` and `delete_account` never ran without an approval record,
   while `lookup_order` ran on its own.

## Acceptance criteria

- [ ] task1: precise `POLICY` scores higher than the empty one; both numbers
      recorded; the 10 non-debatable cases route correctly (decision + trigger).
- [ ] task2: `route()` passes all 12 `ROUTE_CASES`, including the guardrail rows
      where high confidence on a high-risk action is overridden to REVIEW.
- [ ] task3: `requires_approval` gates exactly the high-risk tools; the final audit
      shows no high-risk tool ran without approval, and read-only tools auto-ran.

## Stretch goals

- task1: compare models (`claude-haiku-4-5` -> `claude-sonnet-4-6` -> `claude-opus-4-8`)
  and see whether a precise policy lets a smaller model match a larger one.
- task2: have the model also output its *own* recommended route and measure how
  often it disagrees with `route()` — the cases it would have auto-run are exactly
  why the guardrail exists.
- task3: port the gate to the Agent SDK `can_use_tool` callback (see the flagged note
  in the file) and confirm the same tools get gated.

## Self-check

- Why is "the user asked for a human" its own trigger, separate from policy_gap?
- In task2, why can't confidence alone be allowed to reach AUTO for a refund? What
  failure does the guardrail prevent?
- In task3, the prompt also tells the agent to ask before risky actions. Why is the
  tool-layer gate still necessary if the prompt already says that?
