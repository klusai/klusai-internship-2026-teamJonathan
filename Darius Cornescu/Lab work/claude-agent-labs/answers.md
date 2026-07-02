# Claude Agent Labs — Worksheet answers

Model ids used: `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`.
All runs executed on the company Anthropic API key. Numbers below are real run outputs.

---

## Exercise 1 — Claude Agent SDK

**task1 — the four bugs the agent fixed, and what each fix changed:**
1. `buggy/utils.py::calculate_average` — crashed with `ZeroDivisionError` on `[]`. Fix: return `0.0` for an empty list.
2. `buggy/utils.py::get_user_name` — `KeyError`/`TypeError` on missing `"name"` or `None` user. Fix: guard falsy `user`, use `user.get("name")`, return `""` when missing, else `name.upper()`.
3. `app/payments.py::charge` — accepted non-positive amounts. Fix: `if amount <= 0: raise ValueError("amount must be positive")`.
4. `app/payments.py::make_token` — unsalted MD5 (reversible). Fix: per-call `os.urandom(16)` salt + `pbkdf2_hmac("sha256", …, 100_000)`, returning `salt:hash`.
(The task1 run fixed 1–3 from its prompt; bug 4 was fixed by a second agent-driven pass so all four are agent fixes, not hand edits. Trajectory streamed reasoning → tool → result.)

**task2 — there is no `max_budget_usd`. What bounds work / enforces a ceiling:**
`max_turns` on `ClaudeAgentOptions` bounds how many turns run (the practical work cap), and `ResultMessage.total_cost_usd` is read after the run and compared to `COST_CEILING_USD = 0.50` to enforce the dollar ceiling in code. Any failure collapses to ONE structured JSON line; I also added a `fault_domain` (setup/transport/process/sdk/unknown) via typed `except` branches. Example line: `{"event": "agent_run", "ok": true, "fault_domain": null, "turns_seen": 4, "cost_usd": 0.223, "session_id": "…", "over_budget": false}`.

**task3 — session_id + did resume recall the fact:**
Captured `session_id = 5051a2dd-6acb-445f-8082-79e3f1a93cbc`. Resume (`ClaudeAgentOptions(resume=…)`) recalled it: **"Your favorite number is 42."** — yes. rename/tag/list DO exist in SDK 0.2.110 but signatures differ from the brief: `list_sessions()` has no `tag=` kwarg, so I call it and filter on `.tag` in Python (see `ex1_agent_sdk/task3_sessions_notes.md`).

**task4 — the stitched report + which tools each subagent used:**
Parent delegated to both subagents and stitched a Findings+Tests report. **security-reviewer** (tools: `Read`, `Grep`, `Glob`) returned 6 findings — the top one F1 = `make_token` unsalted MD5 (Critical), plus float-money, missing card validation, NaN/Inf guard bypass, empty-list-returns-0.0, non-string-name. **test-writer** (tools: `Read`, `Write`, `Bash`) wrote `tests/test_security_findings.py` (9 tests). `Task` was parent-only; subagents did not delegate. Running the tests on the host: **9 failed = all findings confirmed** (see `task4_report.md`).

**Reflection — why restrict the bug-fixer to `[Read, Edit, Glob]` not `Bash`:**
Least privilege. Fixing code needs only find/read/edit; `Bash` would let the agent run arbitrary commands (delete files, exfiltrate, install packages, hit the network) — a huge blast radius for zero benefit to the task. Narrow tools make the agent's behavior auditable and safe.

---

## Exercise 2 — Configure Claude Code

**Precedence order (top wins):**
Enterprise policy → project `CLAUDE.md` → user `~/.claude/CLAUDE.md` → path-specific `.claude/rules/*` (these add constraints on top, scoped to the paths they match via `appliesTo`).

**Tabs vs. 4 spaces — which wins and why:**
**Tabs win in this project.** The project-scoped `CLAUDE.md` ("use tabs, not spaces") beats the broader user-level note about 4 spaces — more-specific / project scope overrides the general / user scope.

**What each rule flagged:**
`frontend.md` (`appliesTo: frontend/**`) flagged the `console.log` in `frontend/app.js`. `backend.md` (`appliesTo: backend/**`) flagged the missing type hints on `compute_discount` in `backend/service.py`. Neither fired in the other subtree.

**Skill frontmatter values:**
`context: fork` and `allowed-tools: [Read, Write]`. Because `Bash` is absent from the allow-list, a "now run the tests" request inside the skill is refused.

**MCP:** wired `ex2-fs` (`@modelcontextprotocol/server-filesystem`) via `.mcp.json` + `settings.local.json`; `claude mcp list` shows `ex2-fs … ✔ Connected` (see `mcp-evidence.md`).

**Reflection — if you moved `console.log` into `backend/`, would the frontend rule still fire?**
No. The frontend rule is scoped `appliesTo: frontend/**`, so it only applies to files under `frontend/`. In `backend/` the backend rule applies instead — and it doesn't forbid `console.log` (it's a Python subtree), so the `console.log` would go unflagged by that rule. Rules bite by path.

---

## Exercise 3 — Design and test MCP tools

**Baseline accuracy (vague descriptions): 10 / 10.   After rewriting: 10 / 10.**
Honest result: on `claude-haiku-4-5` the model already routes every case correctly (including the two ambiguous ones) from the prompt intent + tool/arg names, so there was no baseline gap to close. I confirmed the descriptions carry no *extra* deciding signal here via two extra experiments: swapping the two descriptions stayed 10/10, and neutralizing names/args stayed 10/10.

**Final one-line description for `search_orders`:**
"Look up a single order by its order id — bare digits like `10432` or a prefixed code like `ORD-5567`. Not for customer-name lookups; if you only have a company/person, resolve the customer first."

**make_error — which category is retryable and why only that one:**
Only `rate_limit` is retryable (it's the sole member of `_RETRYABLE_CATEGORIES`). A rate limit is transient — the same request succeeds after a backoff. `not_found` and the added `invalid_input` are permanent for that request: retrying repeats the identical failure and just wastes calls, so they are non-retryable.

**Ambiguous cases 8 and 10:**
- Case 8 ("I need the record for 4521") → `search_orders`. A bare number reads as an order id; the description says unprefixed digits are order ids.
- Case 10 ("Find the order from Wayne Enterprises") → `search_customers` first. The user wants an order but supplied only a company name, and `search_orders` needs an id we don't have — resolve the customer first.

**Reflection — if you swapped the two descriptions, would accuracy collapse?**
Here it did NOT — it stayed 10/10 — because the tool names, argument names, and prompt semantics already disambiguate on this model. That proves the description isn't the *only* signal; the model reads intent from the whole tool definition + prompt. Descriptions become decisive only when names/args are neutral or the model is weaker — which is exactly when writing good descriptions pays off.

---

## Exercise 4 — Build a data-extraction pipeline

**Which invoices returned `tax_id: null` (expected two):**
`inv_03` (Sunrise Bakery) and `inv_05` (Maria Lopez). The other four carried real ids (`inv_01` US-84-2937561, `inv_02` GB123456789, `inv_04` 13-7654321, `inv_06` 95-1122334).

**extract.py — what went in the `tool_result` fed back on a validation error:**
A `tool_result` block referencing `tool_use.id` with `is_error: True` and content: *"Schema validation failed: {error message}. Fix the issue and call extract_invoice again."* — then the loop calls the API again (up to 3 attempts).

**batch.py — sum of all totals = 10721.49.   Succeeded: 6 / 6.**
No-tax-id set = `{inv_03, inv_05}`, matching the synchronous run exactly.

**Cost / throughput — how much cheaper, and when NOT to use batch:**
The Message Batches API is ~50% of the token cost. But results are asynchronous (minutes up to ~24h), so don't use it for interactive/single-document flows where a user is waiting, or when you need the per-item validate-and-retry self-correction loop that `extract.py` provides.

**Reflection — why is `tax_id` nullable rather than just optional? What breaks if required?**
Nullable lets the model state "this invoice explicitly has no tax id" (`null`) rather than silently omitting it (ambiguous — did extraction fail, or is there none?). If `tax_id` were **required**, the schema would force a value on `inv_03`/`inv_05`, so the model would fabricate a plausible-looking tax id to pass validation — corrupting the data. Nullable + the "don't invent one" instruction is what prevents hallucinated ids.

---

## Exercise 5 — Prompt engineering

**task1 — zero-shot accuracy 17 / 17.   few-shot accuracy 17 / 17.**
(Scored on the 17 non-debatable tickets; 8/13/19 excluded.) `claude-haiku-4-5` already classifies all 17 correctly zero-shot, so few-shot held at 17/17 (no regression; the lift few-shot gives a weaker model isn't needed here).

**task2 — criteria added beyond the seeded SQL one:**
(1) bare `except:` / `except: pass` that swallows errors; (2) unsalted/fast password hashing (MD5/SHA1) — require a salted slow KDF; (3) using a module (e.g. `hashlib`) without importing it; (4) resource safety (files/cursors without a context manager). Explicit-criteria runs flagged all three planted classes every time; the vague runs varied run-to-run (some caught the dashboard listener bug or missing import instead).

**task3 — did multi-pass catch anything single-pass missed?**
On `claude-opus-4-8`, the single pass already found all three classes including both instances of each. Multi-pass produced a deduplicated, severity-ranked report of the same issues — organization/dedup value, not net-new findings on this diff. Multi-pass would matter more on a larger diff or a weaker model.

**The three planted issues in `big_diff.txt` and their file/line:**
1. **SQL injection** — `api/auth.py::verify_login` (string-concatenated `WHERE username = '…'`) and `api/orders.py::search_orders` (f-string `WHERE` clause).
2. **Bare `except`** — `api/orders.py::cancel_order` (`except: pass`) and `api/utils.py::parse_int` (`except: pass`).
3. **Unsalted MD5** — `api/auth.py::hash_password` and `api/utils.py::api_key_fingerprint`.

**Reflection — why are tickets 8, 13, 19 ambiguous, and what extra info settles each?**
- **8**: frames a perf complaint (sounds like a bug) as a concrete request ("add Elasticsearch"). Settle: is current search *broken/regressed* (bug) or just *slow-but-working* (feature)? Ask for a repro / expected-vs-actual.
- **13**: UX feedback with no concrete defect. Settle: is something *not working* (bug), a *missing capability* (feature), or the user *asking how* (question)? Ask what they expected to happen.
- **19**: "totals look off after a coupon" — likely a calculation bug, but the user is unsure. Settle: reproduce with the exact cart/coupon — is the computed total actually wrong (bug) or a misread/expected behavior (question)?

---

## Wrap-up

**Which technique surprised me most, and why?**
How little few-shot / description tuning changed *accuracy* on current models — classification and tool-routing saturated at 100% from prompt semantics alone. The real payoff of explicit criteria, schemas, and typed errors isn't raw accuracy; it's **reliability and guardrails** (consistent coverage, no fabricated fields, safe retries) — which don't show up in a single happy-path score but matter enormously in production.

**One thing I'd verify against the live Anthropic docs before production:**
The Agent SDK surface that moves between versions — the session helpers' signatures (`rename_session`/`tag_session`/`list_sessions`) and the confirmed absence of `max_budget_usd` (use `max_turns` + `total_cost_usd`) — plus the Message Batches API pricing/SLA. Pin the SDK version and re-verify on upgrade.
