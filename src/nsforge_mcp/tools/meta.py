"""Runtime self-description — the MCP side of the agent harness.

Let an agent that just connected introspect the live server: what it is, which
version, how many tools, and the full capability manifest. This is the runtime
mirror of ``docs/agent/capabilities.json`` (the repo-side self-description) and
closes the loop: the repo self-describes via a file, the server via a tool.
"""

from __future__ import annotations

import json
import sys
from importlib import resources
from pathlib import Path
from typing import Any

import sympy

from nsforge import __version__
from nsforge_mcp.config import OPTIONAL_MODULES, module_enabled

# docs/agent/capabilities.json relative to this file:
# tools -> nsforge_mcp -> src -> <repo root>
_MANIFEST_PATH = Path(__file__).resolve().parents[3] / "docs" / "agent" / "capabilities.json"


def _load_manifest() -> dict[str, Any] | None:
    """Load the capability manifest — the repo copy (dev) or the packaged copy."""
    for text in (_repo_manifest_text(), _packaged_manifest_text()):
        if text is None:
            continue
        try:
            data = json.loads(text)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return None


def _repo_manifest_text() -> str | None:
    try:
        return _MANIFEST_PATH.read_text(encoding="utf-8")
    except OSError:
        return None


def _packaged_manifest_text() -> str | None:
    try:
        resource = resources.files("nsforge_mcp") / "capabilities.json"
        return resource.read_text(encoding="utf-8") if resource.is_file() else None
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return None


def register_meta_tools(mcp: Any) -> None:
    """Register runtime self-description tools with the MCP server."""

    @mcp.tool()
    def nsforge_health() -> dict[str, Any]:
        """Liveness + inventory: server name, version, tool count, engine versions.

        A connected agent calls this first to confirm the server is up and learn
        what it is talking to — no repo access required.
        """
        manifest = _load_manifest()
        tools = manifest.get("tools", []) if manifest else []
        active_tool_count = sum(1 for t in tools if module_enabled(t.get("module", ""))) or None
        return {
            "status": "ok",
            "name": "nsforge",
            "version": __version__,
            "tool_count": manifest.get("tool_count") if manifest else None,
            "active_tool_count": active_tool_count,
            "optional_modules": {m: module_enabled(m) for m in OPTIONAL_MODULES},
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
