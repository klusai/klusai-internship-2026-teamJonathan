# Model Context Protocol (MCP) Overview

The Model Context Protocol allows applications to provide context for LLMs in a standardized way, separating the concerns of providing context from the actual LLM interaction.

---

## Architecture

MCP follows a **client-server architecture** with three roles:

| **Role** | **Description** |
| --- | --- |
| **Host** | The application the user interacts with (e.g. Claude Desktop, an IDE) |
| **Client** | Lives inside the host; manages one connection to one MCP server |
| **Server** | Exposes primitives (tools, resources, prompts) to the client |

Each server is a separate process. A host can connect to multiple servers simultaneously.

---

## MCP Primitives

The three core primitives that servers can implement:

| **Primitive** | **Control** | **Description** | **Example Use** |
| --- | --- | --- | --- |
| **Tools** | Model-controlled | Functions exposed to the LLM to take actions | API calls, data updates |
| **Resources** | Application-controlled | Contextual data managed by the client application | File contents, API responses |
| **Prompts** | User-controlled | Interactive templates invoked by user choice | Slash commands, menu options |

### Tools

Tools are functions the LLM can call. The model decides when and how to use them.

```python
@mcp.tool(name="read_document", description="Read the contents of a document")
def read_document(doc_id: str) -> str:
    return docs[doc_id]
```

### Resources

Resources expose data to the client application. They are identified by URIs and the host/client decides when to load them.

```python
@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    return list(docs.keys())

@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_doc(doc_id: str) -> str:
    return docs[doc_id]
```

### Prompts

Prompts are reusable message templates that users can explicitly invoke (e.g. via a slash command).

```python
@mcp.prompt(name="summarize", description="Summarize a document")
def summarize_document(doc_id: str) -> list[base.Message]:
    return [base.UserMessage(f"Please summarize the document with id: {doc_id}")]
```

---

## Transports

Transports define how the client and server communicate. MCP supports two standard transports:

| **Transport** | **Use Case** |
| --- | --- |
| **stdio** | Local servers launched as subprocesses (most common for local tools) |
| **SSE (Server-Sent Events)** | Remote servers over HTTP; server pushes events to the client |

```python
# Run with stdio (default for local use)
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Server Lifecycle

```text
1. Initialization  →  Client sends initialize request with capabilities
2. Capability exchange  →  Server responds with its supported primitives
3. Operation  →  Client calls tools / reads resources / gets prompts
4. Shutdown  →  Client sends shutdown, server cleans up
```

---

## Key SDK Features (Python)

* Build MCP **clients** that can connect to any MCP server
* Create MCP **servers** that expose resources, prompts, and tools
* Use standard transports: **stdio** and **SSE**
* Handle all MCP protocol messages and lifecycle events
* `FastMCP` class provides decorator-based API for rapid server development

---

## FastMCP Quick Reference

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MyServer")

@mcp.tool()           # Expose a callable function to the LLM
@mcp.resource("uri") # Expose data at a URI
@mcp.prompt()        # Expose a reusable prompt template

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Debugging: MCP Inspector

The MCP Inspector is a browser-based tool for testing your server interactively.

```bash
mcp dev mcp_server.py
```

Opens at `http://localhost:6274` — lets you browse and call tools, resources, and prompts without writing a client.
