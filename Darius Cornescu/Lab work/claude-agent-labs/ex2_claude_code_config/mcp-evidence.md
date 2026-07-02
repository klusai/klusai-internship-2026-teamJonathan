# MCP evidence — ex2 (task 5)

One MCP server (`ex2-fs`, the official filesystem server scoped to this project) was
wired via `.mcp.json` and enabled in `.claude/settings.local.json`
(`enabledMcpjsonServers: ["ex2-fs"]`).

Evidence it loaded — `claude mcp list` run from the `ex2_claude_code_config/` directory:

```
Checking MCP server health…

plugin:context7:context7: npx -y @upstash/context7-mcp - ✔ Connected
ex2-fs: npx -y @modelcontextprotocol/server-filesystem . - ✔ Connected
documents: ...python.exe main.py - ✘ Failed to connect
playwright: npx @playwright/mcp@latest - ✔ Connected
```

`ex2-fs` shows **✔ Connected**, confirming the project-scoped server was discovered from
`.mcp.json`, enabled by `settings.local.json`, and started successfully. (The unrelated
`documents` server failing is a pre-existing, separate issue in another folder.)

## How it was wired
- `.mcp.json` (project root): defines `ex2-fs` -> `npx -y @modelcontextprotocol/server-filesystem .`
- `.claude/settings.local.json`: `enableAllProjectMcpServers: true` + `enabledMcpjsonServers: ["ex2-fs"]`
