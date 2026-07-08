"""Runtime self-description — the MCP side of the agent harness.

Let an agent that just connected introspect the live server: what it is, which
version, how many tools, and the full capability manifest. This is the runtime
mirror of ``docs/agent/capabilities.json`` (the repo-side self-description) and
closes the loop: the repo self-describes via a file, the server via a tool.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import sympy

from nsforge import __version__

# docs/agent/capabilities.json relative to this file:
# tools -> nsforge_mcp -> src -> <repo root>
_MANIFEST_PATH = Path(__file__).resolve().parents[3] / "docs" / "agent" / "capabilities.json"


def _load_manifest() -> dict[str, Any] | None:
    """Load the on-disk capability manifest, or None if it is unavailable."""
    try:
        text = _MANIFEST_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def register_meta_tools(mcp: Any) -> None:
    """Register runtime self-description tools with the MCP server."""

    @mcp.tool()
    def nsforge_health() -> dict[str, Any]:
        """Liveness + inventory: server name, version, tool count, engine versions.

        A connected agent calls this first to confirm the server is up and learn
        what it is talking to — no repo access required.
        """
        manifest = _load_manifest()
        return {
            "status": "ok",
            "name": "nsforge",
            "version": __version__,
            "tool_count": manifest.get("tool_count") if manifest else None,
            "modules": manifest.get("modules") if manifest else None,
            "sympy_version": sympy.__version__,
            "python_version": sys.version.split()[0],
        }

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
