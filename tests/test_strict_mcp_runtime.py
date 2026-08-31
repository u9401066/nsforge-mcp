"""Official MCP client coverage for strict scopes, resources, and subscriptions."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from mcp import Client
from mcp.shared.exceptions import MCPError
from mcp.shared.subscriptions import ResourcesListChanged
from mcp.types import ResourceLink

from nsforge.infrastructure.sqlite_run_store import get_run_store
from nsforge_mcp.composition import get_services
from nsforge_mcp.server import create_server


def _passing_spec() -> dict[str, object]:
    return {
        "name": "mcp-strict-identity",
        "goal": "derive y",
        "given": {"x": "scalar"},
        "unknowns": ["y"],
        "base_formulas": ["y = x + 1"],
        "acceptance": [{"kind": "equivalence", "params": {"reference": "x + 1"}}],
    }


def _no_acceptance_spec() -> dict[str, object]:
    value = _passing_spec()
    value.pop("acceptance")
    return value


@pytest.mark.asyncio
async def test_resolved_scope_is_not_in_schema_and_environment_cannot_drift_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    original_db = tmp_path / "tenant-a.sqlite3"
    drifted_db = tmp_path / "tenant-b.sqlite3"
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-a")
    monkeypatch.setenv("NSFORGE_RUN_DB", str(original_db))
    server = create_server()

    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "legacy")
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-b")
    monkeypatch.setenv("NSFORGE_RUN_DB", str(drifted_db))
    async with Client(server) as client:
        by_name = {tool.name: tool for tool in (await client.list_tools()).tools}
        assert "scope" not in by_name["task_run"].input_schema["properties"]
        result = await client.call_tool(
            "task_run",
            {"spec": _passing_spec(), "timeout_s": 10.0},
        )

    payload = result.structured_content
    assert isinstance(payload, dict)
    run_id = str(payload["run_id"])
    assert payload["execution_status"] == "completed"
    assert get_run_store(original_db).get_run("tenant-a", run_id) is not None
    assert get_run_store(original_db).get_run("tenant-b", run_id) is None
    assert not drifted_db.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("profile", "expects_code", "expected_status"),
    [("legacy", True, "completed"), ("workflow", False, "rejected")],
)
async def test_profile_freezes_legacy_vs_strict_no_acceptance_behavior(
    profile: str,
    expects_code: bool,
    expected_status: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", profile)
    monkeypatch.setenv("NSFORGE_TENANT_ID", f"tenant-{profile}")
    monkeypatch.setenv("NSFORGE_RUN_DB", str(tmp_path / f"{profile}.sqlite3"))
    async with Client(create_server()) as client:
        result = await client.call_tool("task_run", {"spec": _no_acceptance_spec()})

    payload = result.structured_content
    assert isinstance(payload, dict)
    assert bool(payload["generated_code"]) is expects_code
    assert payload["execution_status"] == expected_status
    assert payload["verification_status"] == "not_checked"


@pytest.mark.asyncio
async def test_task_result_links_resources_and_publishes_list_changed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-listener")
    monkeypatch.setenv("NSFORGE_RUN_DB", str(tmp_path / "listen.sqlite3"))
    async with (
        Client(create_server()) as client,
        client.listen(resources_list_changed=True) as subscription,
    ):
        call = asyncio.create_task(client.call_tool("task_run", {"spec": _passing_spec()}))
        event = await asyncio.wait_for(anext(subscription), timeout=10)
        result = await asyncio.wait_for(call, timeout=10)

    assert isinstance(event, ResourcesListChanged)
    payload = result.structured_content
    assert isinstance(payload, dict)
    assert "_resource_links" not in payload
    public_uris = {str(item["uri"]) for item in payload["resources"]}
    linked_uris = {str(item.uri) for item in result.content if isinstance(item, ResourceLink)}
    assert public_uris == linked_uris
    assert any(uri.startswith("nsforge://runs/") for uri in linked_uris)
    assert any(uri.startswith("nsforge://artifacts/") for uri in linked_uris)


@pytest.mark.asyncio
async def test_run_and_artifact_resources_enforce_tenant_acl_on_same_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shared_db = tmp_path / "shared.sqlite3"
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    monkeypatch.setenv("NSFORGE_RUN_DB", str(shared_db))
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-a")
    server_a = create_server()
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-b")
    server_b = create_server()

    async with Client(server_a) as client_a:
        result = await client_a.call_tool("task_run", {"spec": _passing_spec()})
        payload = result.structured_content
        assert isinstance(payload, dict)
        run_uri = next(
            str(item["uri"])
            for item in payload["resources"]
            if str(item["uri"]).startswith("nsforge://runs/")
            and not str(item["uri"]).endswith("/events")
        )
        artifact_uri = next(
            str(item["uri"])
            for item in payload["resources"]
            if str(item["uri"]).startswith("nsforge://artifacts/")
        )
        events_uri = f"{run_uri}/events"
        assert (await client_a.read_resource(run_uri)).contents
        assert (await client_a.read_resource(events_uri)).contents
        assert (await client_a.read_resource(artifact_uri)).contents

    async with Client(server_b) as client_b:
        with pytest.raises(MCPError):
            await client_b.read_resource(run_uri)
        with pytest.raises(MCPError):
            await client_b.read_resource(events_uri)
        with pytest.raises(MCPError):
            await client_b.read_resource(artifact_uri)


@pytest.mark.asyncio
async def test_session_resource_returns_detached_snapshot_and_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-session")
    monkeypatch.setenv("NSFORGE_RUN_DB", str(tmp_path / "sessions.sqlite3"))
    manager = get_services().session_manager
    session = manager.create("resource-session", auto_persist=False)
    try:
        session.load_formula("y = x + 1", formula_id="identity")
        async with Client(create_server()) as client:
            resource = await client.read_resource(f"nsforge://sessions/{session.session_id}")
            with pytest.raises(MCPError):
                await client.read_resource("nsforge://sessions/does-not-exist")

        snapshot = json.loads(getattr(resource.contents[0], "text", ""))
        assert snapshot["session_id"] == session.session_id
        assert snapshot["status"] == session.status.value
        assert snapshot["current_expression"] == str(session.current_expression)
        assert snapshot["step_count"] == len(snapshot["steps"])
        snapshot["steps"].append({"forged": True})
        assert len(session.steps) + 1 == len(snapshot["steps"])
    finally:
        manager.delete(session.session_id)
