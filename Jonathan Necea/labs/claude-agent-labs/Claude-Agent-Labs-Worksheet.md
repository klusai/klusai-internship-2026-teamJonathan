# Claude Agent Labs — Worksheet

Fill in as you work through the five exercises. (Converted from the printable `.docx`.)

**Name:** ________________   **Date:** ____________

Model ids used in this pack: `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`.

---

## Exercise 1 — Build an agent with the Claude Agent SDK

**task1:** Which four bugs did the agent fix, and what did each fix change?
>

**task2:** There is no `max_budget_usd`. What did you use to bound work and to enforce a dollar ceiling?
>

**task3:** Paste the `session_id` you captured. Did the resumed session recall the fact?
>

**task4:** Summarize the stitched report. Which tools did each subagent use?
>

### Self-check
- [ ] Agent fixed all four bugs via Edit (not me), trajectory streamed
- [ ] Failure collapsed to one structured log line; cost ceiling enforced via `total_cost_usd`
- [ ] Session captured and resumed; rename/tag/list works or is documented
- [ ] Two subagents, correct tool sets, Task only in the parent

### Reflection
Why restrict the bug-fixer to `[Read, Edit, Glob]` instead of giving it Bash?
>

---

## Exercise 2 — Configure Claude Code

**Write the precedence order** (enterprise / project / user / path rules):
> enterprise > project / path-rules > user

**Tabs vs. 4 spaces** — which wins in this project, and why?
> Tabs win because Claude.md (project) takes precedence over user rules

**What did the frontend rule flag? What did the backend rule flag?**
> Front-end: console.log
> Back-end: type hints, naming, indentation

**Skill frontmatter:** what values did you set for `context` and `allowed-tools`?
> context: fork
> allowed-tools: [Read, Write]
> disallowed-tools: [Bash]

### Self-check
- [ ] Precedence order written; tabs-vs-spaces resolved with a reason
- [ ] `console.log` flagged in `frontend/`; missing type hint flagged in `backend/`
- [ ] `SKILL.md` has `context: fork` and `allowed-tools: [Read, Write]`; Bash blocked
- [ ] One MCP server wired with captured evidence

### Reflection
If you moved `console.log` into `backend/`, would the frontend rule still fire? Why?
>

---

## Exercise 3 — Design and test MCP tools

**Baseline accuracy** (vague descriptions): ____ / 10.   **After rewriting:** ____ / 10.
>

**Write your final one-line description for `search_orders`:**
>

**`make_error`:** which category is retryable, and why only that one?
>

**Cases 8 and 10 are ambiguous** — what did you decide for each, and why?
>

### Self-check
- [ ] Both descriptions rewritten (when-to-use, the argument, example, what it's not for)
- [ ] Accuracy improved from baseline; both numbers recorded
- [ ] `retryable` is True only for `rate_limit`; one extra category added
- [ ] Defensible stance on the two ambiguous cases

### Reflection
If you swapped the two descriptions, would accuracy collapse? What would that prove?
>

---

## Exercise 4 — Build a data-extraction pipeline

**Which invoices returned `tax_id: null`?** (expected two)
>

**`extract.py`:** what did you put in the `tool_result` you fed back on a validation error?
>

**`batch.py`:** sum of all totals = __________.   Succeeded: ____ / 6.
>

**Cost / throughput:** how much cheaper is the batch, and when would you NOT use it?
>

### Self-check
- [ ] `extract.py` validates and retries with the error fed back
- [ ] `inv_03` and `inv_05` -> `tax_id` null; the other four -> real ids; all six validate
- [ ] `batch.py` submits, polls to ended, validates, aggregates
- [ ] `comparison.md` states cost delta, latency trade-off, and when to pick each

### Reflection
Why is `tax_id` nullable rather than just optional? What breaks if it's required?
>

---

## Exercise 5 — Prompt engineering

**task1:** zero-shot accuracy ____ / 17.   few-shot accuracy ____ / 17.
>

**task2:** list the criteria you added (beyond the seeded SQL one):
>

**task3:** did multi-pass catch anything single-pass missed? What?
>

**Name the three planted issues in `big_diff.txt` and their file/line:**
>

### Self-check
- [ ] Zero-shot and few-shot accuracies recorded; few-shot >= zero-shot
- [ ] CRITERIA covers SQL injection, bare except, and weak hashing; explicit runs consistent
- [ ] Chunk split + synthesis implemented; single-pass vs multi-pass compared
- [ ] All three planted issues named with file/line

### Reflection
Why are tickets 8, 13, and 19 ambiguous, and what extra info would settle each?
>

---

## Wrap-up

**Which technique surprised you most, and why?**
>

**One thing you'd verify against the live Anthropic docs before using in production:**
>
