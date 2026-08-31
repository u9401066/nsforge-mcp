"""Runtime self-description — the MCP side of the agent harness.

Let an agent that just connected introspect the live server: what it is, which
version, how many tools, and the full capability manifest. This is the runtime
mirror of ``docs/agent/capabilities.json`` (the repo-side self-description) and
closes the loop: the repo self-describes via a file, the server via a tool.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nsforge_mcp.introspection import health_payload, load_manifest

# Compatibility for existing Python-side tests and integrations.  The shared
# implementation now also backs MCP resources.
_load_manifest = load_manifest


def register_meta_tools(
    mcp: Any,
    *,
    health_factory: Callable[[], dict[str, Any]] = health_payload,
) -> None:
    """Register runtime self-description tools with the MCP server."""

    @mcp.tool()
    def nsforge_health() -> dict[str, Any]:
        """Liveness + inventory: server name, version, tool count, engine versions.

        A connected agent calls this first to confirm the server is up and learn
        what it is talking to — no repo access required.
        """
        return health_factory()

    @mcp.tool()
    def nsforge_manifest() -> dict[str, Any]:
        """Return the full capability manifest (tools, gates, commands, north star).

        The runtime mirror of ``docs/agent/capabilities.json`` — how an agent
        discovers every tool and how to verify a change.
        """
        manifest = _load_manifest()
        if manifest is None:
            return {
                "available": False,
                "hint": "manifest ships with the source tree; run in a repo checkout "
                "or regenerate with: python scripts/gen_capabilities.py",
            }
        return manifest
