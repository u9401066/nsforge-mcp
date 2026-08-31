"""Exact, startup-frozen MCP tool-profile contracts."""

from __future__ import annotations

import json

import pytest
from mcp import Client

from nsforge_mcp.server import create_server
from nsforge_mcp.tool_contract import (
    STRICT_TOOL_PROFILES,
    TOOL_PROFILES,
    ToolProfile,
    profile_tool_names,
    spec_for,
)

PROFILE_COUNTS = {
    "legacy": 82,
    "workflow": 17,
    "scientific": 35,
    "interactive": 35,
    "full": 91,
}


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", TOOL_PROFILES)
async def test_profile_registers_exact_frozen_names(
    profile: ToolProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", profile)
    monkeypatch.delenv("NSFORGE_ENABLE_MUSIC", raising=False)
    server = create_server()

    async with Client(server) as client:
        tools = (await client.list_tools()).tools

    actual = {tool.name for tool in tools}
    assert actual == set(profile_tool_names(profile))
    assert len(actual) == PROFILE_COUNTS[profile]


@pytest.mark.asyncio
async def test_legacy_music_env_and_full_profile_both_retain_91_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "legacy")
    monkeypatch.setenv("NSFORGE_ENABLE_MUSIC", "1")
    legacy_music = create_server()
    async with Client(legacy_music) as client:
        assert len((await client.list_tools()).tools) == 91

    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "full")
    monkeypatch.delenv("NSFORGE_ENABLE_MUSIC", raising=False)
    full = create_server()
    async with Client(full) as client:
        assert len((await client.list_tools()).tools) == 91


def test_unknown_profile_fails_server_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "surprise")
    with pytest.raises(ValueError, match="NSFORGE_TOOL_PROFILE"):
        create_server()


@pytest.mark.asyncio
async def test_compact_profile_has_concise_descriptions_and_resource_first_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    server = create_server()
    async with Client(server) as client:
        tools = (await client.list_tools()).tools

    names = {tool.name for tool in tools}
    assert not {"nsforge_health", "nsforge_manifest", "derivation_get_saved"} & names
    assert all(tool.description == spec_for(tool.name).description for tool in tools)
    assert sum(len(tool.description or "") for tool in tools) < 4_000


@pytest.mark.asyncio
async def test_strict_profile_rejects_unknown_enum_and_numeric_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    server = create_server()
    async with Client(server) as client:
        listed = {tool.name: tool for tool in (await client.list_tools()).tools}
        limit_schema = listed["calculate_limit"].input_schema
        assert limit_schema["additionalProperties"] is False
        assert limit_schema["properties"]["direction"]["enum"] == ["+-", "", "+", "-"]
        timeout_schema = listed["task_run"].input_schema["properties"]["timeout_s"]
        numeric = next(item for item in timeout_schema["anyOf"] if item.get("type") == "number")
        assert numeric["exclusiveMinimum"] == 0

        unknown = await client.call_tool(
            "calculate_limit",
            {"expression": "x", "variable": "x", "point": "0", "typo": True},
        )
        invalid_enum = await client.call_tool(
            "calculate_limit",
            {"expression": "x", "variable": "x", "point": "0", "direction": "sideways"},
        )
        invalid_numeric = await client.call_tool(
            "task_run",
            {
                "spec": {
                    "name": "strict-timeout",
                    "goal": "identity",
                    "unknowns": ["y"],
                    "base_formulas": ["y = x"],
                },
                "timeout_s": 0,
            },
        )

    for result in (unknown, invalid_enum, invalid_numeric):
        assert result.is_error is True
        assert isinstance(result.structured_content, dict)
        assert result.structured_content["error_code"] == "validation"


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", sorted(STRICT_TOOL_PROFILES))
async def test_strict_discovery_describes_inputs_and_common_outcomes(
    profile: ToolProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", profile)
    async with Client(create_server()) as client:
        tools = (await client.list_tools()).tools

    common_outcomes = {
        "success",
        "execution_status",
        "verification_status",
        "run_id",
        "correlation_id",
        "resources",
        "error",
    }
    for tool in tools:
        properties = tool.input_schema.get("properties", {})
        assert all(
            isinstance(schema.get("description"), str) and schema["description"].strip()
            for schema in properties.values()
        ), tool.name
        assert tool.output_schema is not None
        assert tool.output_schema["additionalProperties"] is True
        assert common_outcomes <= set(tool.output_schema["properties"]), tool.name

    by_name = {tool.name: tool for tool in tools}
    if "task_run" in by_name:
        spec_schema = by_name["task_run"].input_schema["properties"]["spec"]
        assert spec_schema["additionalProperties"] is False
        assert set(spec_schema["required"]) == {"name", "goal", "unknowns", "base_formulas"}
        nested = spec_schema["properties"]
        assert nested["modifications"]["items"]["additionalProperties"] is False
        assert nested["alternatives"]["items"]["additionalProperties"] is False
        assert nested["acceptance"]["items"]["additionalProperties"] is False


@pytest.mark.asyncio
async def test_strict_task_spec_rejects_unknown_nested_fields_and_invalid_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    base_spec = {
        "name": "strict-dts",
        "goal": "derive an identity",
        "unknowns": ["y"],
        "base_formulas": ["y = x"],
    }
    async with Client(create_server()) as client:
        unknown = await client.call_tool(
            "task_plan",
            {
                "spec": {
                    **base_spec,
                    "modifications": [{"id": "m1", "unexpected": True}],
                }
            },
        )
        invalid_shape = await client.call_tool(
            "task_plan", {"spec": {**base_spec, "base_formulas": "y = x"}}
        )

    for result in (unknown, invalid_shape):
        assert result.is_error is True
        assert isinstance(result.structured_content, dict)
        assert result.structured_content["error_code"] == "validation"
        assert result.structured_content["details"]["issues"]


@pytest.mark.asyncio
async def test_profile_and_health_are_cached_at_server_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-secret")
    server = create_server()
    expected = sorted(profile_tool_names("workflow"))

    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "full")
    monkeypatch.setenv("NSFORGE_TENANT_ID", "different-secret")
    async with Client(server) as client:
        assert sorted(tool.name for tool in (await client.list_tools()).tools) == expected
        health_result = await client.read_resource("nsforge://health")

    health = json.loads(getattr(health_result.contents[0], "text", ""))
    assert health["tool_profile"] == "workflow"
    assert health["active_tool_names"] == expected
    assert health["active_tool_count"] == 17
    assert health["tenant_scope_mode"] == "configured"
    assert "tenant_id" not in health
    assert "tenant-secret" not in json.dumps(health)
