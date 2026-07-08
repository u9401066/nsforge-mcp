"""
NSForge MCP Server

FastMCP-based server providing symbolic reasoning tools to AI agents.
"""

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from nsforge import __version__
from nsforge_mcp.config import module_enabled
from nsforge_mcp.tools import register_all_tools

logger = logging.getLogger("nsforge")

# Create the FastMCP server instance
mcp = FastMCP(
    name="nsforge",
    instructions=(
        f"Neurosymbolic Forge v{__version__} — turn concepts into verifiable, "
        "traceable formulas via provenance-tracked symbolic derivation."
    ),
    website_url="https://github.com/u9401066/nsforge-mcp",
)

# Register all tools
register_all_tools(mcp)


def _configure_logging() -> None:
    """Send NSForge logs to stderr — stdout is reserved for the MCP stdio protocol."""
    logger.setLevel(os.environ.get("NSFORGE_LOG_LEVEL", "INFO").upper())
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False


def main() -> None:
    """Entry point for the MCP server."""
    _configure_logging()
    logger.info(
        "NSForge MCP v%s starting (stdio) — music %s",
        __version__,
        "enabled" if module_enabled("music") else "opt-in (disabled)",
    )
    mcp.run()


if __name__ == "__main__":
    main()
