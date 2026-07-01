---
name: generate-endpoint
description: Scaffold a new REST endpoint (route + handler + types) from a short spec. Use when the user asks to add an API endpoint to the backend.
# TODO(task 4): this skill must run in an isolated, forked context so its work
# does not pollute the main conversation. Set the right value:
context: fork
allowed-tools: [Read, Write]
---

# generate-endpoint

Scaffold a new REST endpoint from a one-line spec.

## When to use

When the user says "add an endpoint", "scaffold a route", or describes a new API
operation for the backend.

## Steps

1. Read the existing routes file to match the project's style.
2. Write the new route, its handler, and request/response types.
3. Report the files you created.

## Constraints

- This skill **must not** run shell commands. It works purely by reading and
  writing files. (That is why `Bash` is excluded from `allowed-tools` above — once
  you fill the frontmatter in, a request like "now run the tests" should be
  refused by this skill, because it has no `Bash` permission.)
- Follow the backend type-hint rule in `.claude/rules/backend.md`.

## Verify Bash is blocked (task 4)

After filling in the frontmatter, invoke the skill and then ask it to run a shell
command. Record what happens — it should decline because `Bash` is not in its
`allowed-tools`.
