"""Regression tests for the runtime self-description (meta) tools."""

from collections.abc import Callable
from typing import Any

from nsforge import __version__
from nsforge_mcp.tools.meta import register_meta_tools


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _tools() -> dict[str, Callable[..., Any]]:
    mcp = _FakeMCP()
    register_meta_tools(mcp)
    return mcp.tools


def test_health_reports_version_and_status() -> None:
    health = _tools()["nsforge_health"]()
    assert health["status"] == "ok"
    assert health["name"] == "nsforge"
    assert health["version"] == __version__
    assert health["mcp_sdk_version"].startswith("2.")
    assert health["mcp_protocol_revision"] == "2026-07-28"
    assert health["tool_count"] and health["tool_count"] >= 89


def test_manifest_returns_full_contract() -> None:
    manifest = _tools()["nsforge_manifest"]()
    assert manifest["schema"].startswith("nsforge.capabilities/")
    assert manifest["tool_count"] == len(manifest["tools"])
    assert manifest["harness"]  # the gate list is advertised
    assert any(t["name"] == "nsforge_health" for t in manifest["tools"])
