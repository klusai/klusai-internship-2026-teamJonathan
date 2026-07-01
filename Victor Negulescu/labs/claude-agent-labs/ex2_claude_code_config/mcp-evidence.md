# MCP Server Evidence

Server configured in `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

After opening this project in Claude Code and running `/mcp`, the filesystem server
appears in the list of connected servers with tools such as `read_file`,
`write_file`, `list_directory`, and `search_files` available.

The server is scoped to the current directory (`.`) so it can only access files
within `ex2_claude_code_config/` — it cannot reach outside the project root.
