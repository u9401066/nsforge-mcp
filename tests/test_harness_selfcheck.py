"""Focused tests for the capability manifest and 12-gate harness contract."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check  # noqa: E402
import gen_capabilities  # noqa: E402
import harness_selfcheck  # noqa: E402


def test_collector_supports_async_tools_and_omits_injected_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tool_source = '''
class Registry:
    def tool(self): ...

mcp = Registry()

@mcp.tool()
async def task_run(spec: dict[str, object], ctx: Context, timeout: float = 1.0) -> dict:
    """Run an asynchronous MCP task."""
'''
    (tmp_path / "task.py").write_text(tool_source, encoding="utf-8")
    monkeypatch.setattr(gen_capabilities, "TOOLS_DIR", tmp_path)

    tools = gen_capabilities.collect()

    assert [tool["name"] for tool in tools] == ["task_run"]
    assert tools[0]["params"] == [
        {"name": "spec", "type": "dict[str, object]"},
        {"name": "timeout", "type": "float"},
    ]
    assert tools[0]["structured_output"] is True
    assert tools[0]["annotations"]["title"] == "Task Run"


def test_capability_v3_advertises_the_live_mcp_and_harness_contract() -> None:
    manifest = gen_capabilities.build()

    assert manifest["schema"] == "nsforge.capabilities/v3"
    assert manifest["mcp"]["protocol_revision"] == "2026-07-28"
    assert manifest["mcp"]["sdk_requirement"] == ">=2.1.1,<3"
    assert manifest["mcp"]["transports"] == ["stdio", "streamable-http"]
    assert manifest["mcp"]["resources"]
    assert manifest["mcp"]["prompts"]
    assert [gate["gate"] for gate in manifest["harness"]] == check.DEFAULT_ORDER
    assert len(check.DEFAULT_ORDER) == 12
    assert all(tool["title"] for tool in manifest["tools"])
    assert all(tool["annotations"] for tool in manifest["tools"])
    assert all(tool["structured_output"] is True for tool in manifest["tools"])
    assert all(tool["meta"] for tool in manifest["tools"])
    assert manifest["mcp"]["sdk_requirement"] == harness_selfcheck._pyproject_mcp_requirement()
