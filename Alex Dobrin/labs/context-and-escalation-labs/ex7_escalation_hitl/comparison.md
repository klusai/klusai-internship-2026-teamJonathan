# Task 1 — Escalation triggers: empty vs. precise policy

Classifying 12 support situations as HANDLE vs. ESCALATE and naming the trigger
(`policy_gap` / `user_request` / `no_progress` / `none`). Same model, same
scenarios, same forced `route_request` tool call — the only variable is the
`POLICY` system prompt.

- **Model:** `claude-haiku-4-5`
- **Scored set:** the 10 non-debatable cases (cases 11 and 12 are debatable and
  not counted).
- **Method:** one forced `route_request` tool call per scenario.

## Headline result

| Run | POLICY | Accuracy (non-debatable) | Debatable landed on accepted |
| --- | ------ | -----------------------: | ---------------------------: |
| Baseline | empty (`""`) | **7/10 = 70%** | 1/2 |
| Precise  | full triggers spelled out | **10/10 = 100%** | 2/2 |

**Delta: +30 points (70% → 100%).** Writing the policy is the whole exercise —
same model, same cases, the prompt is the only thing that changed.

## What flipped, and why

Every baseline failure was a **correct HANDLE/ESCALATE decision with the wrong
trigger** — the empty policy could feel that these cases were unusual but had no
vocabulary for *why*, so it defaulted to `user_request` even when the user never
asked for a human.

| # | Scenario | Baseline (empty) | Precise | Fix |
| - | -------- | ---------------- | ------- | --- |
| 6 | "Delete my account and permanently erase all my data." | ESCALATE / **user_request** ❌ | ESCALATE / **policy_gap** ✅ | Deletion is outside auto-handle authority, not a request for a human |
| 7 | "Change the shipping address on order #559? It hasn't shipped yet." | **HANDLE / user_request** ❌ | HANDLE / **none** ✅ | Within policy for unshipped orders → just handle it, no trigger |
| 9 | "Should I sue your company? What are my legal options?" | ESCALATE / **user_request** ❌ | ESCALATE / **policy_gap** ✅ | Legal advice is out of scope → policy_gap, not a human request |

The seven cases the baseline already got right (1, 2, 3, 4, 5, 8, 10) stayed
correct — the precise policy added the missing trigger definitions without
breaking anything.

## Debatable cases (not scored)

| # | Scenario | Baseline | Precise | Accepted pairs |
| - | -------- | -------- | ------- | -------------- |
| 11 | Loyalty discount, policy silent | ESCALATE / policy_gap ✅ | ESCALATE / policy_gap ✅ | `[HANDLE, none]`, `[ESCALATE, policy_gap]` |
| 12 | "Explain the billing cycle again" (asked yesterday too) | HANDLE / **user_request** ❌ | ESCALATE / **no_progress** ✅ | `[HANDLE, none]`, `[ESCALATE, no_progress]` |

The baseline missed even an *accepted* answer on case 12 (`user_request` is not
in its accept list); the precise policy landed on the `no_progress` reading,
which is accepted. Both debatable cases land inside the accepted set under the
precise policy (2/2).

## Takeaway

The failures were never about the escalate/handle call — the model mostly gets
that from the raw situation. They were about **naming the trigger**, and a trigger
is only nameable once the policy defines it. Spelling out the three triggers
(the $50 refund limit and account-deletion/legal scope as `policy_gap`, an explicit
ask for a person as `user_request`, and exhausted/repeat contact as `no_progress`)
plus a tie-break order turned three "right answer, wrong reason" cases into full
passes and took the scored set from 70% to 100%.
