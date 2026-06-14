from mcp.server.fastmcp import FastMCP
from tools.math import add
from tools.document import document_path_to_markdown, document_stats

mcp = FastMCP("docs")

mcp.tool()(add)
mcp.tool()(document_path_to_markdown)
mcp.tool()(document_stats)

if __name__ == "__main__":
    mcp.run()
