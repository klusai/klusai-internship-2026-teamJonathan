# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A standalone MCP server (`FastMCP("docs")`) that exposes document- and math-related tools
to AI assistants. It is exercise 8 of the "Building with Claude" curriculum and is fully
self-contained — it does **not** share code with the `7 - MCP` chat client; the parent
repo's root `CLAUDE.md` covers cross-project context.

## Commands

```bash
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e .       # editable install (package name is "app")

uv run main.py            # start the MCP server (stdio transport)
uv run pytest             # run all tests
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown::test_binary_document_to_markdown_with_pdf  # single test
```

Requires Python >= 3.10. No linter or type checker is configured.

## Conventions

- **Always apply appropriate type annotations to function arguments** (and return types).
  This matters doubly for MCP tools: `FastMCP` derives each tool's input schema from the
  signature, so a missing or wrong type yields a broken tool interface — but apply it to
  every function, not just tools.

## Structure & how tools get exposed

- `main.py` — the server entry point. Tools are registered **functionally**, not with a
  decorator: `mcp.tool()(add)`. To expose a new tool, import the function and add a
  `mcp.tool()(fn)` line here. Note the server runs `mcp.run()` with the default transport.
- `tools/` — plain Python functions, one concern per file (`math.py`, `document.py`).
  These are ordinary, independently testable functions; registration is decoupled and
  lives only in `main.py`.
- `tests/` — pytest. `tests/fixtures/` holds real `mcp_docs.docx` / `mcp_docs.pdf`
  binaries used by `test_document.py` to exercise conversion end-to-end.

Current state worth knowing: `tools/document.py`'s `binary_document_to_markdown` is
implemented and tested but **not yet registered** in `main.py` — only `add` is wired up.
Wire it via `mcp.tool()(...)` when it should be callable by the model. Document conversion
uses `markitdown` (`MarkItDown().convert(BytesIO(data), stream_info=StreamInfo(extension=...))`).

## Tool authoring conventions (from README.md — follow these)

Tools are designed to be model-facing, so the description and parameter docs *are* the
interface. When adding a tool:

- Annotate every parameter with `pydantic.Field(description=...)`; the type hint becomes
  the schema type.
- Write a thorough docstring that: opens with a one-line summary, explains functionality,
  states when to use **and when not to** use the tool, and includes input/output examples
  (see `tools/math.py::add` as the reference template).

```python
from pydantic import Field

def my_tool(
    param1: str = Field(description="What this parameter is"),
    param2: int = Field(description="What this parameter does"),
) -> ReturnType:
    """One-line summary.

    Longer explanation. When to use / when not to use. Examples with expected output.
    """
    ...
```

Then register it in `main.py`: `mcp.tool()(my_tool)`.
