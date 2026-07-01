# Exercise 3 — Design and test MCP tools

**Topic:** writing tool descriptions that differentiate *similar* tools, returning
structured errors with categories and retry flags, and testing against ambiguous
user requests.

## Goal

You have two tools that are easy to confuse — `search_orders` (by id) and
`search_customers` (by name). Make the model route prompts to the right one using
**only the tool descriptions**, and make failures return structured, retry-aware
errors.

## What's here

```
ex3_mcp_tools/
  server.py               FastMCP server: search_orders, search_customers, make_error()
  ambiguity_cases.json    10 prompts with a gold expected_tool (2 are genuinely ambiguous)
  run_ambiguity_test.py   harness: records chosen tool vs expected and prints accuracy
```

## Setup

```bash
pip install mcp anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Tasks

1. **Disambiguate the descriptions.** Both tool docstrings in `server.py` start as
   vague TODO stubs. Rewrite them so each says precisely *when to use it*, *what its
   single argument is* (an order id vs. a customer name), gives an example, and says
   what it is **not** for. The harness reads these docstrings directly.

2. **Baseline, then improve.** Run `python run_ambiguity_test.py` *before* editing
   the descriptions and record the accuracy. Rewrite the descriptions, run again,
   and record the new accuracy. The delta is the point of the exercise.

3. **Structured errors.** Confirm `make_error()` returns `error_category`,
   `message`, and `retryable`, and that `retryable` is `True` **only** for
   `rate_limit`. Add one more category (e.g. `invalid_input`) and make
   `search_orders` return it when given an empty id.

4. **Reason about the ambiguous cases.** Cases 8 (`"the record for 4521"`) and 10
   (`"the order from Wayne Enterprises"`) are genuinely ambiguous. Decide what the
   *right* behavior is and make your descriptions encode that stance.

## Acceptance criteria

- [ ] Both descriptions rewritten; each names its argument and says what it's not for.
- [ ] Accuracy improves measurably from baseline to post-edit (record both numbers).
- [ ] `make_error("rate_limit", ...)["retryable"]` is `True`; every other category is
      `False`.
- [ ] You can explain your chosen answer for cases 8 and 10.

## Stretch goals

- Compare models: change `MODEL` in the harness (`claude-haiku-4-5` →
  `claude-sonnet-4-6` → `claude-opus-4-8`) and see how routing accuracy changes.
- Add a third tool (`search_by_email`) and three new cases that could collide with
  the existing two.
- Connect the server to an MCP client (or Claude Desktop) and route a prompt for real.

## Self-check

- If you swapped the two descriptions, would accuracy collapse? (It should — proof
  the descriptions are doing the work, not the tool names.)
- Why should a `not_found` error be non-retryable but a `rate_limit` retryable?
