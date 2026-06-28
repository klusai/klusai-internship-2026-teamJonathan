# Answer Key — Claude Agent Labs

Instructor reference. Expected solution per task, plus the gotchas to watch for.
Model ids used throughout: `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`.

---

## Exercise 1 — Claude Agent SDK

**Buggy fixtures, the fixes the agent should make:**

- `buggy/utils.py`
  - `calculate_average([])` → `ZeroDivisionError`. Fix: return `0.0` (or raise a
    clear `ValueError`) when `numbers` is empty.
  - `get_user_name(user)` → `KeyError`/`TypeError`. Fix: guard `None` and missing
    `"name"`, e.g. `if not user or "name" not in user: return None` then
    `return user["name"].upper()`.
- `app/payments.py`
  - `make_token` uses unsalted MD5 → replace with a salted, slow KDF
    (`hashlib.pbkdf2_hmac` / bcrypt / argon2) or, for a non-secret token, at least a
    salted SHA-256. MD5 is the finding.
  - `charge` has no validation → add `if amount <= 0: raise ValueError(...)`.

**task1_bugfixer.py** — `ClaudeAgentOptions(allowed_tools=["Read","Edit","Glob"],
permission_mode="acceptEdits", cwd=...)`. The render loop should print reasoning
(TextBlock), tool calls (ToolUseBlock), and results (ToolResultBlock on a
UserMessage). With no `Bash`, the agent fixes by editing only.

**task2_errors.py** — The key teaching point: **`max_budget_usd` does not exist.**
Full credit requires the student to (a) recognize this, (b) use `max_turns` to bound
work, and (c) read `ResultMessage.total_cost_usd` and enforce a ceiling in code. The
failure on the missing path must collapse to **one** structured line (JSON), not a
stack trace.

**task3_sessions.py** — Capture `ResultMessage.session_id`; resume with
`ClaudeAgentOptions(resume=session_id)`; the resumed turn must recall "42". For
rename/tag/list: accept either a working implementation against the installed SDK
**or** a correct written explanation that these helpers aren't in their version and
what the real mechanism is (session store / CLI / `fork_session`). Do not penalize a
student for the SDK not exposing them — penalize not investigating.

**task4_subagents.py** — `agents={...}` with two `AgentDefinition`s; security-reviewer
= `[Read,Grep,Glob]`, test-writer = `[Read,Write,Bash]`; parent allow-list includes
`Task`. Subagents must NOT have `Task`. Output is one stitched report (Findings +
Tests + verdict). Watch for: a student giving a subagent `Task` (wrong), or doing the
review in the parent without delegating (misses the point).

---

## Exercise 2 — Claude Code configuration

1. **Precedence (top wins):** enterprise policy → project `CLAUDE.md` → user
   `~/.claude/CLAUDE.md`; path-specific `.claude/rules/*` add constraints on matched
   paths on top of all of the above.
2. **Tabs vs. 4 spaces:** **tabs win in this project.** Project-scoped memory beats
   the broader user-level note, and the project `CLAUDE.md` says so explicitly.
3. **Rules bite:** a `console.log` in `frontend/` is flagged by `frontend.md`; a
   missing type hint in `backend/` is flagged by `backend.md`; neither fires in the
   other subtree (proves `appliesTo` scoping).
4. **Skill frontmatter:** `context: fork` and `allowed-tools: [Read, Write]`. Because
   `Bash` is absent, a "now run the tests" request inside the skill is refused.
5. **MCP:** any one server added to `.claude/settings.local.json` with captured
   evidence (the `/mcp` listing, tool list, or a screenshot in `mcp-evidence.md`).

---

## Exercise 3 — MCP tools

- **Descriptions:** each rewritten docstring must (a) say when to use the tool, (b)
  name its one argument as an order id vs. a customer name, (c) give an example, (d)
  say what it's NOT for. Swapping the descriptions should swap the routing — that's
  the proof they carry the signal.
- **Accuracy:** with vague stubs, expect routing mistakes (often on cases 3, 6, 8,
  10). With good descriptions, the 8 non-ambiguous cases (1–7, 9, 11-style) route
  correctly; cases 8 and 10 are intentionally ambiguous.
  - Case 8: a perf complaint + an explicit "add X" → `feature` (accept `search_*`
    routing reasoning if justified; this case is about recognizing intent).
  - Case 10: "the order from Wayne Enterprises" → resolve the **customer** first
    (`search_customers`), because `search_orders` needs an id you don't have.
- **make_error:** `error_category`, `message`, `retryable`; `retryable is True` only
  for `rate_limit`. A `not_found` must be non-retryable.

---

## Exercise 4 — Extraction pipeline

- **Schema:** required `vendor`, `total`, `line_items`; `tax_id` nullable & optional.
- **extract.py:** validate the tool output with `jsonschema`; on `ValidationError`,
  append a `tool_result` with `is_error: True` and the message, then loop. Returns
  validated dict.
- **Nullable proof:** inv_03 (Sunrise Bakery) and inv_05 (Maria Lopez) → `tax_id:
  null`. inv_01 `US-84-2937561`, inv_02 `GB123456789`, inv_04 `13-7654321`, inv_06
  `95-1122334`. A fabricated tax id on 03/05 is a fail.
- **batch.py:** `client.messages.batches.create(requests=[Request(custom_id=...,
  params=MessageCreateParamsNonStreaming(...))])`; poll `retrieve(id)
  .processing_status == "ended"`; iterate `results(id)`, branch on
  `result.result.type`. Aggregate: sum of `total` ≈ 249+18.5+114+7999.99+1000+1340 =
  **10721.49**; no-tax-id set = `{inv_03, inv_05}`.
- **comparison.md:** Batches API = **50% token cost**; latency up to ~1h vs. 6 quick
  synchronous calls. Batch for bulk/overnight; synchronous for interactive single docs.

---

## Exercise 5 — Prompt engineering

- **Gold labels:** see `gold_labels.json`. Score only the 17 non-debatable tickets;
  tickets **8, 13, 19** are debatable (accept either listed label).
- **task1 (few-shot):** zero-shot baseline first; then a `FEWSHOT` block with ≥1 of
  each class should raise accuracy on the non-debatable set (and often stabilize the
  debatable ones toward the gold). Record both numbers.
- **task2 (criteria):** the completed `CRITERIA` must name SQL injection, bare
  `except`/`except: pass`, and unsalted MD5. Explicit-criteria runs should find all
  three every time; vague runs vary run-to-run.
- **task3 (multi-pass):** `split_into_chunks` splits per `diff --git`; synthesis
  merges + dedupes + ranks. Multi-pass should catch all three planted issues; often
  surfaces the second MD5 use (`api/utils.py` `api_key_fingerprint`) and the second
  bare `except` (`parse_int`) that a single pass may gloss over.
- **The three planted issues in `big_diff.txt`:**
  1. **SQL injection** — `api/auth.py` `verify_login` (string-concatenated `WHERE
     username = '...'`); also `api/orders.py` `search_orders` (f-string `WHERE`).
  2. **Bare `except`** — `api/orders.py` `cancel_order` (`except: pass`); also
     `api/utils.py` `parse_int`.
  3. **Unsalted MD5** — `api/auth.py` `hash_password`; also `api/utils.py`
     `api_key_fingerprint`.
