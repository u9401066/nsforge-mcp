"""
NSForge MCP Server

FastMCP-based server providing symbolic reasoning tools to AI agents.
"""

from mcp.server.fastmcp import FastMCP

from nsforge_mcp.tools import register_all_tools

# Create the FastMCP server instance
mcp = FastMCP(
    name="nsforge",
    version="0.1.0",
    description="Neurosymbolic Forge - Precise symbolic reasoning for AI agents",
)

# Register all tools
register_all_tools(mcp)


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
