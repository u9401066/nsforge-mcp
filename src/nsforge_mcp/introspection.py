"""Shared runtime self-description for tools and MCP resources."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from importlib import metadata, resources
from pathlib import Path
from typing import Any

import sympy

from nsforge import __version__
from nsforge_mcp.config import OPTIONAL_MODULES, module_enabled
from nsforge_mcp.tool_contract import MCP_PROTOCOL_REVISION

# docs/agent/capabilities.json relative to this file:
# nsforge_mcp -> src -> <repo root>
_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "docs" / "agent" / "capabilities.json"


def manifest_text() -> str | None:
    """Return the development or wheel-bundled manifest as text."""
    for text in (_repo_manifest_text(), _packaged_manifest_text()):
        if text is not None:
            return text
    return None


def load_manifest() -> dict[str, Any] | None:
    """Load the capability manifest from a checkout or installed wheel."""
    text = manifest_text()
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def health_payload(*, module_state: Mapping[str, bool] | None = None) -> dict[str, Any]:
    """Build the shared liveness and runtime-inventory payload.

    ``module_state`` lets a server instance report the optional-tool surface it
    captured when it was created.  Reading the process environment again here
    would let a later env change make health disagree with that server's
    already-registered tools.
    """
    manifest = load_manifest()
    tools = manifest.get("tools", []) if manifest else []
    captured_state = (
        dict(module_state)
        if module_state is not None
        else {module: module_enabled(module) for module in OPTIONAL_MODULES}
    )
    active_tool_count = (
        sum(1 for tool in tools if captured_state.get(str(tool.get("module", "")), True)) or None
    )
    return {
        "status": "ok",
        "name": "nsforge",
        "version": __version__,
        "mcp_sdk_version": metadata.version("mcp"),
        "mcp_protocol_revision": MCP_PROTOCOL_REVISION,
        "tool_count": manifest.get("tool_count") if manifest else None,
        "active_tool_count": active_tool_count,
        "optional_modules": captured_state,
        "modules": manifest.get("modules") if manifest else None,
        "sympy_version": sympy.__version__,
        "python_version": sys.version.split()[0],
    }


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
