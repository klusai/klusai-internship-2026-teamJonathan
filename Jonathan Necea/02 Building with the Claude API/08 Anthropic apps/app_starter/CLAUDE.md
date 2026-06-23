# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Python package exposing document-related tools (format conversion and processing) through an **MCP (Model Context Protocol) server** so AI assistants can call them. Built on `FastMCP` from the `mcp` SDK.

## Commands

```bash
# One-time setup: create venv, activate, install in editable mode
uv venv
source .venv/bin/activate
uv pip install -e .

# Start the MCP server (stdio transport)
uv run main.py

# Run all tests
uv run pytest

# Run a single test class or test
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown::test_binary_document_to_markdown_with_pdf
```

## Architecture

- **`main.py`** — server entry point. Instantiates a single `FastMCP("docs")` instance and registers tools against it. This is the wiring layer; it imports tool functions and registers each one.
- **`tools/`** — tool *implementations* as plain Python functions, decoupled from MCP. Each module (e.g. `math.py`, `document.py`) holds standalone functions with no MCP imports, which keeps them directly unit-testable.
- **`tests/`** — pytest suite that tests tool functions directly (not through the MCP layer). Document tests load real binary files from `tests/fixtures/` (`.docx`, `.pdf`).

### Registering a tool

Tools are defined as functions in `tools/` and registered in `main.py` by calling the function returned by `mcp.tool()`:

```python
from tools.math import add
mcp.tool()(add)
```

Note the two-call form `mcp.tool()(fn)` — `mcp.tool()` returns a decorator that is then applied to the function. Adding a new tool means: write the function in a `tools/` module, import it in `main.py`, and register it with the same pattern.

### Document conversion

`tools/document.py` wraps `markitdown` to convert in-memory binary document data to markdown. It takes raw `bytes` plus a `file_type` extension string (e.g. `"docx"`, `"pdf"`), wraps the bytes in a `BytesIO`, and passes a `StreamInfo(extension=...)` to `MarkItDown.convert()`. The `markitdown[docx,pdf]` extras pull in the docx/pdf parsers.

## Code conventions

- **Always apply appropriate type annotations to function arguments** (and return types). Tool signatures are the contract the LLM sees, so typed parameters matter for correctness and clarity.

## Tool definition conventions (from README)

Tool functions are the contract the LLM sees, so their signatures and docstrings matter as much as their behavior. Follow these conventions when authoring tools:

- Use `Field` from pydantic for **every** parameter, with a `description` (this is what the model reads to decide how to call the tool):
  ```python
  from pydantic import Field

  def my_tool(
      param1: str = Field(description="Detailed description of this parameter"),
      param2: int = Field(description="Explain what this parameter does"),
  ) -> ReturnType:
      """Comprehensive docstring here"""
  ```
- The docstring should: begin with a one-line summary; give a detailed explanation of functionality; explain **when to use (and when not to use)** the tool; and include usage examples with expected input/output. See `tools/math.py` (`add`) for the canonical example of this docstring shape.
