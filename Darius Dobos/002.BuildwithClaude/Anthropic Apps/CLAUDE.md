# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# Install package in development mode
uv pip install -e .

# Start the MCP server
uv run main.py

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown::test_binary_document_to_markdown_with_docx
```

## Architecture

This is an MCP (Model Context Protocol) server built with `FastMCP`. Tools are plain Python functions in the `tools/` package that get registered with the MCP server instance in `main.py`.

**Flow:** `main.py` creates a `FastMCP` instance, imports tool functions from `tools/`, and registers each with `mcp.tool()(fn)`. Running `main.py` starts the MCP server.

**Adding a new tool:**
1. Define it as a function in `tools/` (or a new module there)
2. Import it in `main.py` and register it with `mcp.tool()(your_function)`

## Code Style

- Always annotate function argument types and return types.

## Defining MCP Tools

Tools are plain Python functions. Use `pydantic.Field` for parameter descriptions — FastMCP reads these to expose parameter metadata to the AI client.

```python
from pydantic import Field

def my_tool(
    param1: str = Field(description="Detailed description of this parameter"),
    param2: int = Field(description="Explain what this parameter does")
) -> ReturnType:
    """One-line summary.

    Detailed explanation of functionality.

    When to use:
    - Specific use case
    - Another use case

    Examples:
    >>> my_tool("foo", 42)
    expected_output
    """
```

Docstring conventions:
- First line: one-line summary
- Body: detailed explanation of functionality
- "When to use" section: include when *not* to use if relevant
- "Examples" section: show expected input/output
