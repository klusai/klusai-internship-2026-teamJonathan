---
name: test-driven-development
description: Guides a TDD workflow — writes failing tests from a spec first, then implements code to pass them, following the red-green-refactor cycle. Use when the user wants to implement a feature test-first, is starting a new module, asks to "write tests before the code", or mentions TDD, red-green-refactor, or BDD.
---

# Test-Driven Development

Drive implementation through tests. Every line of production code must be
justified by a failing test that demanded it. Read `references/test-patterns.md`
(relative to this skill) before writing the first test in a session.

The cycle is always: **RED → GREEN → REFACTOR → repeat**.
Never skip ahead. Never write implementation before the test that requires it.

---

## Step 1 — Orient: understand the spec and the environment

Before writing a single line, answer four questions.

**1a. What is the unit under test?**
Read `$ARGS` for a spec, user story, or function signature. If `$ARGS` is
empty, ask: "What do you want to implement? Describe the behaviour, not the
implementation."

Identify:
- The public surface (function name, class API, HTTP endpoint, CLI command).
- The inputs and their types.
- The expected outputs or side-effects.
- Any explicit constraints or error cases mentioned.

If the spec is ambiguous, resolve it with the user before proceeding — a test
written against the wrong assumption wastes both cycles.

**1b. What test framework and runner are in use?**
Run the detection script from the repo root:

```
python <skill-path>/scripts/detect_test_env.py
```

If Python is unavailable or the script errors, infer the framework manually:
- `pytest.ini`, `conftest.py`, or `[tool.pytest.ini_options]` in
  `pyproject.toml` → **pytest** (preferred; use pytest conventions throughout).
- `import unittest` in existing test files → **unittest**.
- No evidence → default to **pytest**.

Note the `run_command` and `run_single` from the script output — you will
use them in every RED and GREEN step.

**1c. Where do new tests go?**
Check `test_dirs` and `test_files` from the script. Mirror the source tree:
if the code will live in `myapp/orders/cart.py`, the test goes in
`tests/orders/test_cart.py`. If no `tests/` directory exists, create it with
an empty `__init__.py` (pytest does not require it, but it avoids import
ambiguity on some setups).

**1d. Does a stub or module need to exist first?**
If the module or class the test will import does not exist yet, create a
minimal stub file with empty classes / functions that `raise NotImplementedError`.
The test must be able to *import* before it can *fail meaningfully*.

---

## Step 2 — RED: write one failing test

Write the smallest test that captures one behaviour from the spec.
Consult `references/test-patterns.md` for naming, AAA structure, and the
right test double to use.

**Rules for this step:**
- One test only. Resist the urge to write the whole suite up front.
- Test behaviour, not implementation. The test should read like a statement
  of the requirement, not a description of how the code works.
- Use the Arrange-Act-Assert structure. One blank line between each section.
- Name the test `test_<unit>_<scenario>_<expected>` so the failure output
  is self-documenting.
- Do not import implementation that doesn't exist yet without first creating
  a stub (Step 1d).

Show the test to the user before running it.

**Run the test:**

```
<run_single> with {file} and {test} filled in
```

The test **must** fail. If it passes immediately, either:
- the implementation already existed (check — maybe a similar function covers
  this case), or
- the test is not actually exercising the right thing (wrong assertion,
  wrong input, wrong import).

**Verify the failure is meaningful:**
The failure message must describe a business rule violation
(`AssertionError`, `NotImplementedError`), not an environment problem
(`ImportError`, `SyntaxError`, `AttributeError` on a method that doesn't exist).

If the failure is an environment error: fix the stub and re-run. Do not
proceed to GREEN until the failure is on the assertion, not the plumbing.

Report the exact failure line to the user: `"Test is RED: <failure message>"`.

---

## Step 3 — GREEN: write the minimum implementation

Write the **simplest code that makes the failing test pass**. Nothing more.

**Rules for this step:**
- Only introduce what the failing test requires. Avoid implementing
  edge cases not yet tested — those get their own RED step later.
- It is fine to write obviously non-general code if that is all the test
  demands right now. The next test will force generalisation.
- Do not refactor yet. GREEN means passing, not clean.

Run the full file's tests (not just the one):

```
<run_command> <test_file>
```

All tests in the file must be green. If a previous test broke, fix the
regression before continuing. Do not move to REFACTOR with a broken suite.

Report: `"Test is GREEN."` and show the implementation written.

---

## Step 4 — REFACTOR: clean up without changing behaviour

With all tests green, improve the code. Refactoring changes structure, not
behaviour — the tests must stay green throughout.

**What to look for:**
- Duplication in production code (extract a helper, a method, a constant).
- Duplication in tests (a shared fixture, a parametrize, a factory helper).
- Naming that no longer reflects what the code does.
- A function doing more than one thing.
- Magic literals that should be named constants.
- Missed early returns or guard clauses that simplify nesting.

**What NOT to do in refactor:**
- Do not add new functionality. New behaviour needs a new RED test.
- Do not delete a test "because the code is cleaner now." The tests are the
  specification — they are not optional.

Run the full suite after every refactoring change:

```
<run_command>
```

If any test breaks: revert the last change, not the tests.

When done, report: `"Refactor complete. Suite still green."` and summarise
what was cleaned up.

---

## Step 5 — Repeat: next behaviour

Look at the spec. What behaviour is not yet covered by a passing test?
Pick the next simplest uncovered case and return to Step 2.

Prioritise in this order:
1. The happy path (one end-to-end flow of the most common input).
2. Edge cases that are explicit in the spec (empty input, zero, None, max
   value).
3. Error cases (invalid input, missing dependencies, network failure).
4. Edge cases inferred from the implementation (boundary conditions that
   became visible during GREEN).

Keep iterating until every behaviour in the spec has at least one test.

---

## When the spec is a user story

If the input is a user story ("As a user I can…"), decompose it into
testable behaviours before writing any test:

```
Story: As a user, I can apply a promo code to my cart to receive a discount.

Behaviours:
  1. A valid 10%-off code reduces the cart total by 10%.
  2. An expired code raises an error with the message "code expired".
  3. An unknown code raises an error with the message "invalid code".
  4. A code can only be applied once; a second application raises an error.
  5. A 0-item cart with a valid code returns a total of 0.
```

Walk through each behaviour as a separate RED → GREEN → REFACTOR cycle.
Show the decomposed list to the user and let them add, remove, or reorder
before starting.

---

## Invariants to maintain at all times

- **Never write production code without a failing test that requires it.**
  If you catch yourself adding "just in case" logic, stop. Write the test
  that would fail without it first.
- **Never let the suite stay red longer than one step.**
  A red suite means the implementation is unfinished. Only one test should
  be failing at a time: the one you just wrote.
- **Never delete or weaken a test to make it pass.**
  If a test is wrong, discuss it with the user and rewrite the *test* to
  reflect the correct expectation. Do not lower the bar to meet the code.
- **Run the full suite after every non-trivial change.**
  Regressions caught immediately cost seconds. Regressions caught at PR
  review cost hours.

---

## Edge cases

- **Spec describes I/O-heavy code (HTTP, DB, filesystem):** write the test
  against an interface, use a fake or stub for the external dependency, and
  note that integration tests covering the real dependency are a separate
  concern. Don't let "we can't test that without a database" become a reason
  to skip the unit test.
- **Existing code with no tests (legacy):** do not refactor first. Write a
  characterisation test that documents current behaviour, then add the new
  behaviour TDD-style. The refactor only happens once the characterisation
  test is in place.
- **The test is hard to write:** this is design feedback. A test that is
  painful to set up usually means the unit under test has too many
  dependencies or too wide a responsibility. Discuss redesigning the
  interface before proceeding.
- **Multiple files / packages involved:** still one failing test at a time.
  Test the top-level integration behaviour first; let it pull in lower-level
  pieces as needed. If a lower-level piece is complex, give it its own TDD
  cycle before integrating.
- **Framework is not Python:** the cycle is identical. Adjust the run
  command (`go test ./...`, `npm test`, `cargo test`, `dotnet test`) and
  the test syntax. The principles — one failing test, minimum implementation,
  refactor when green — do not change.
