#!/usr/bin/env python3
"""MCP 2.x compatibility gate for NSForge's complete public surface.

This is deliberately an end-to-end protocol check.  It connects an official
MCP client to fresh default and music-enabled in-memory server instances and to
a real stdio subprocess, then
guards the tool catalog, wire schemas, metadata, structured result payloads,
resources, prompts, and legacy-client interoperability.

Exit code 0 means the MCP upgrade kept the v0.2.4 tool contract intact while
successfully advertising the additive MCP 2.x features.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import traceback
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters

from nsforge_mcp.tool_contract import (
    MCP_PROTOCOL_REVISION,
    PROMPT_NAMES,
    RESOURCE_URIS,
    TOOL_PROFILES,
    contract_for,
    profile_tool_names,
    spec_for,
    tool_meta,
)

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "docs" / "agent" / "capabilities.json"
MUSIC_ENV = "NSFORGE_ENABLE_MUSIC"
PROFILE_ENV = "NSFORGE_TOOL_PROFILE"
RUN_DB_ENV = "NSFORGE_RUN_DB"
EXPECTED_MCP_SDK = "2.1.1"
EXPECTED_DEFAULT_COUNT = 82
EXPECTED_FULL_COUNT = 91
EXPECTED_CONTRACT_HASHES = {
    "default": "c30e84c32d81c2f1656416233e943f54e26d2d825bea14af6788f372b66438f3",
    "full": "33dd0c4ef7f05808273eb10e5dd88c4d32a5a15c6b990c0a62b1b319a377b9b3",
}
EXPECTED_PAYLOAD_HASHES = {
    "limit_success": (
        "97c8e4d4f85ec91e3f5d867d2254bad4b4e230dac83337a3ed946d6fc2a8cb94",
        "f8013a47eca5cb3d6eeb49cfd99d45bf5c481712ec5f3e311b33e76b5896988f",
    ),
    "parse_success": (
        "02f5217a0e49dce02646d127a13327ed41ba260603d686706288fae119cb7861",
        "3dffbd675d7f05c3e660870a652eb12a04eee1c719ad686c12dbe3622d4d641d",
    ),
    "limit_handled_error": (
        "1b65e21f2f623211703501fa2417de9d5c3ed05088479485de91fe132ffacbd5",
        "0282ee8d05ec27ac16dc90aff3637144b1a35713a36154665b65ce55a2f55184",
    ),
}


def _contract_hash(tools: list[Any]) -> str:
    """Hash only the v0.2.4 wire contract, excluding additive MCP 2 metadata."""
    payload = [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema,
            "outputSchema": tool.output_schema,
        }
        for tool in sorted(tools, key=lambda item: item.name)
    ]
    wire = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(wire).hexdigest()


def _require(condition: bool, message: str, problems: list[str]) -> None:
    if not condition:
        problems.append(message)


def _validate_cache_hint(result: Any, label: str, problems: list[str]) -> None:
    _require(result.ttl_ms == 300_000, f"{label}: cache TTL is not 300000 ms", problems)
    _require(result.cache_scope == "public", f"{label}: cache scope is not public", problems)


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _tool_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(tool["name"]): tool for tool in manifest["tools"]}


@contextmanager
def _music_setting(enabled: bool) -> Any:
    """Temporarily force a deterministic optional-tool configuration."""
    previous = os.environ.get(MUSIC_ENV)
    if enabled:
        os.environ[MUSIC_ENV] = "1"
    else:
        os.environ.pop(MUSIC_ENV, None)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(MUSIC_ENV, None)
        else:
            os.environ[MUSIC_ENV] = previous


def _create_server(*, music: bool, profile: str | None = None) -> Any:
    # Import lazily while the deterministic environment override is active: the
    # module also constructs its backwards-compatible global ``mcp`` instance.
    previous_profile = os.environ.get(PROFILE_ENV)
    previous_run_db = os.environ.get(RUN_DB_ENV)
    if profile is None:
        os.environ.pop(PROFILE_ENV, None)
    else:
        os.environ[PROFILE_ENV] = profile
    # Contract probes must never leave a runtime database in the checkout.
    os.environ[RUN_DB_ENV] = ":memory:"
    try:
        with _music_setting(music):
            from nsforge_mcp.server import create_server

            return create_server()
    finally:
        if previous_profile is None:
            os.environ.pop(PROFILE_ENV, None)
        else:
            os.environ[PROFILE_ENV] = previous_profile
        if previous_run_db is None:
            os.environ.pop(RUN_DB_ENV, None)
        else:
            os.environ[RUN_DB_ENV] = previous_run_db


def _expected_names(
    manifest: dict[str, Any],
    *,
    music: bool,
) -> set[str]:
    optional = set(manifest["optional_modules"])
    return {
        str(tool["name"]) for tool in manifest["tools"] if music or tool["module"] not in optional
    }


def _validate_tools(
    tools: list[Any],
    manifest: dict[str, Any],
    *,
    surface: str,
    music: bool,
    expected_count: int,
    problems: list[str],
) -> None:
    by_name = _tool_manifest(manifest)
    actual_names = {str(tool.name) for tool in tools}
    expected_names = _expected_names(manifest, music=music)
    _require(
        len(tools) == expected_count,
        f"{surface}: expected {expected_count} tools, got {len(tools)}",
        problems,
    )
    _require(
        actual_names == expected_names,
        f"{surface}: tool names differ (missing={sorted(expected_names - actual_names)}, "
        f"extra={sorted(actual_names - expected_names)})",
        problems,
    )

    actual_hash = _contract_hash(tools)
    expected_hash = EXPECTED_CONTRACT_HASHES[surface]
    _require(
        actual_hash == expected_hash,
        f"{surface}: v0.2.4 schema contract changed ({actual_hash} != {expected_hash})",
        problems,
    )

    for tool in tools:
        static = by_name.get(tool.name)
        if static is None:
            continue
        contract = contract_for(tool.name, str(static["module"]))
        prefix = f"{surface}/{tool.name}"
        _require(tool.title == contract.title, f"{prefix}: title mismatch", problems)
        _require(tool.title == static.get("title"), f"{prefix}: manifest title mismatch", problems)
        _require(bool(tool.output_schema), f"{prefix}: missing outputSchema", problems)
        _require(bool(tool.icons), f"{prefix}: missing icon", problems)
        _require(tool.meta == tool_meta(contract.module), f"{prefix}: _meta mismatch", problems)
        _require(tool.meta == static.get("meta"), f"{prefix}: manifest _meta mismatch", problems)

        annotation = tool.annotations
        _require(annotation is not None, f"{prefix}: missing annotations", problems)
        if annotation is not None:
            annotation_wire = annotation.model_dump(by_alias=True, exclude_none=True)
            _require(
                annotation_wire == static.get("annotations"),
                f"{prefix}: manifest annotations mismatch",
                problems,
            )
            _require(
                annotation.title == contract.title,
                f"{prefix}: annotation title mismatch",
                problems,
            )
            for field in (
                "read_only_hint",
                "destructive_hint",
                "idempotent_hint",
                "open_world_hint",
            ):
                _require(
                    getattr(annotation, field) == getattr(contract, field),
                    f"{prefix}: {field} mismatch",
                    problems,
                )

        actual_inputs = set(tool.input_schema.get("properties", {}))
        manifest_inputs = {str(param["name"]) for param in static["params"]}
        _require(
            actual_inputs == manifest_inputs,
            f"{prefix}: input properties differ from manifest "
            f"({sorted(actual_inputs)} != {sorted(manifest_inputs)})",
            problems,
        )
        _require(
            static.get("structured_output") is True, f"{prefix}: manifest flag false", problems
        )


def _text_payload(result: Any) -> Any:
    texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
    if not texts:
        return None
    try:
        return json.loads(texts[0])
    except json.JSONDecodeError:
        return texts[0]


def _payload_hashes(result: Any) -> tuple[str, str]:
    text = next(item.text for item in result.content if getattr(item, "type", None) == "text")
    structured = json.dumps(
        result.structured_content,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return (
        hashlib.sha256(text.encode("utf-8")).hexdigest(),
        hashlib.sha256(structured.encode("utf-8")).hexdigest(),
    )


async def _validate_result_payloads(client: Client[Any], problems: list[str]) -> None:
    limit = await client.call_tool(
        "calculate_limit",
        {"expression": "sin(x)/x", "variable": "x", "point": "0"},
    )
    _require(limit.is_error is False, "successful limit was marked isError", problems)
    _require(
        _payload_hashes(limit) == EXPECTED_PAYLOAD_HASHES["limit_success"],
        "successful limit payload changed from v0.2.4",
        problems,
    )

    parsed = await client.call_tool(
        "parse_expression",
        {"expression": "x^2 + 2*x + 1"},
    )
    _require(parsed.is_error is False, "successful parse was marked isError", problems)
    _require(
        isinstance(parsed.structured_content, dict)
        and parsed.structured_content.get("success") is True,
        "success call lost its legacy structured payload",
        problems,
    )
    _require(
        _text_payload(parsed) == parsed.structured_content,
        "success call text and structured payloads differ",
        problems,
    )
    _require(
        _payload_hashes(parsed) == EXPECTED_PAYLOAD_HASHES["parse_success"],
        "successful parse payload changed from v0.2.4",
        problems,
    )

    handled = await client.call_tool(
        "calculate_limit",
        {"expression": "(", "variable": "x", "point": "0"},
    )
    _require(handled.is_error is True, "handled tool failure was not marked isError", problems)
    _require(
        isinstance(handled.structured_content, dict)
        and handled.structured_content.get("success") is False
        and "error" in handled.structured_content,
        "handled failure lost its legacy structured payload",
        problems,
    )
    _require(
        _text_payload(handled) == handled.structured_content,
        "handled failure text and structured payloads differ",
        problems,
    )
    _require(
        _payload_hashes(handled) == EXPECTED_PAYLOAD_HASHES["limit_handled_error"],
        "handled limit-error payload changed from v0.2.4",
        problems,
    )

    unequal = await client.call_tool(
        "verify_equality",
        {"expression1": "x", "expression2": "x + 1"},
    )
    _require(
        unequal.is_error is False,
        "valid negative verification was incorrectly marked isError",
        problems,
    )
    _require(
        isinstance(unequal.structured_content, dict)
        and unequal.structured_content.get("verified") is False
        and "error" not in unequal.structured_content,
        "negative verification lost its normal-result semantics",
        problems,
    )

    progress_events: list[tuple[float, float | None, str | None]] = []

    async def record_progress(
        progress: float,
        total: float | None,
        message: str | None,
    ) -> None:
        progress_events.append((progress, total, message))

    task = await client.call_tool(
        "task_run",
        {
            "spec": {
                "name": "mcp_contract_progress",
                "goal": "reify an identity expression",
                "unknowns": ["y"],
                "base_formulas": ["y = x"],
            }
        },
        progress_callback=record_progress,
    )
    _require(task.is_error is False, "task progress smoke call failed", problems)
    _require(
        isinstance(task.structured_content, dict)
        and task.structured_content.get("success") is True,
        "task progress smoke call lost its structured result",
        problems,
    )
    _require(
        len(progress_events) >= 2
        and progress_events[0][:2] == (0.0, 1.0)
        and progress_events[-1][:2] == (1.0, 1.0),
        f"task progress notifications missing or malformed: {progress_events}",
        problems,
    )
    task_links = [item for item in task.content if getattr(item, "type", None) == "resource_link"]
    _require(bool(task_links), "task result omitted additive MCP ResourceLinks", problems)
    _require(
        "_resource_links" not in (task.structured_content or {}),
        "task result leaked its internal ResourceLink sentinel",
        problems,
    )


async def _validate_primitives(client: Client[Any], problems: list[str]) -> None:
    resources = await client.list_resources()
    templates = await client.list_resource_templates()
    prompts = await client.list_prompts()
    _validate_cache_hint(resources, "resources/list", problems)
    _validate_cache_hint(templates, "resources/templates/list", problems)
    _validate_cache_hint(prompts, "prompts/list", problems)

    advertised_resources = {str(item.uri) for item in resources.resources}
    advertised_resources.update(str(item.uri_template) for item in templates.resource_templates)
    _require(
        advertised_resources == set(RESOURCE_URIS),
        f"resource discovery differs ({sorted(advertised_resources)} != {sorted(RESOURCE_URIS)})",
        problems,
    )
    advertised_prompts = {item.name for item in prompts.prompts}
    _require(
        advertised_prompts == set(PROMPT_NAMES),
        f"prompt discovery differs ({sorted(advertised_prompts)} != {sorted(PROMPT_NAMES)})",
        problems,
    )
    for item in [*resources.resources, *templates.resource_templates]:
        prefix = f"resource/{getattr(item, 'name', '?')}"
        _require(bool(item.title), f"{prefix}: missing title", problems)
        _require(bool(item.description), f"{prefix}: missing description", problems)
        _require(bool(item.icons), f"{prefix}: missing icons", problems)
        _require(item.annotations is not None, f"{prefix}: missing annotations", problems)
        _require(bool(item.meta), f"{prefix}: missing _meta", problems)
    for item in prompts.prompts:
        prefix = f"prompt/{item.name}"
        _require(bool(item.title), f"{prefix}: missing title", problems)
        _require(bool(item.description), f"{prefix}: missing description", problems)
        _require(bool(item.icons), f"{prefix}: missing icons", problems)

    for uri in ("nsforge://manifest", "nsforge://health", "nsforge://north-star"):
        result = await client.read_resource(uri)
        _require(bool(result.contents), f"resource {uri} returned no content", problems)

    manifest_result = await client.read_resource("nsforge://manifest")
    manifest_text = getattr(manifest_result.contents[0], "text", "")
    try:
        resource_manifest = json.loads(manifest_text)
    except json.JSONDecodeError:
        resource_manifest = {}
    _require(
        resource_manifest.get("schema") == "nsforge.capabilities/v4",
        "manifest resource is not capability schema v4",
        problems,
    )

    prompt = next((item for item in prompts.prompts if item.name == PROMPT_NAMES[0]), None)
    if prompt is not None:
        arguments = {
            argument.name: "contract-check"
            for argument in (prompt.arguments or [])
            if argument.required
        }
        rendered = await client.get_prompt(prompt.name, arguments)
        _require(bool(rendered.messages), f"prompt {prompt.name} rendered no messages", problems)


async def _verify_modern_server(
    server: Any,
    manifest: dict[str, Any],
    *,
    surface: str,
    music: bool,
    profile: str,
    expected_count: int,
    check_primitives: bool,
    problems: list[str],
) -> None:
    async with Client(server, mode=MCP_PROTOCOL_REVISION, raise_exceptions=True) as client:
        _require(
            client.protocol_version == MCP_PROTOCOL_REVISION,
            f"{surface}: negotiated {client.protocol_version}, expected {MCP_PROTOCOL_REVISION}",
            problems,
        )
        listed = await client.list_tools()
        _validate_cache_hint(listed, f"{surface}/tools/list", problems)
        server_info = (listed.meta or {}).get("io.modelcontextprotocol/serverInfo", {})
        _require(server_info.get("name") == "nsforge", f"{surface}: server name mismatch", problems)
        _require(
            server_info.get("title") == "Neurosymbolic Forge",
            f"{surface}: server title mismatch",
            problems,
        )
        _require(
            server_info.get("version") == manifest["version"],
            f"{surface}: server version mismatch",
            problems,
        )
        _require(bool(server_info.get("icons")), f"{surface}: server icons missing", problems)
        _validate_tools(
            listed.tools,
            manifest,
            surface=surface,
            music=music,
            expected_count=expected_count,
            problems=problems,
        )
        health_result = await client.read_resource("nsforge://health")
        health_text = getattr(health_result.contents[0], "text", "")
        try:
            health = json.loads(health_text)
        except json.JSONDecodeError:
            health = {}
        _require(
            health.get("active_tool_count") == len(listed.tools),
            f"{surface}: health active-tool count differs from tools/list",
            problems,
        )
        _require(
            health.get("tool_profile") == profile,
            f"{surface}: health profile {health.get('tool_profile')!r} != {profile!r}",
            problems,
        )
        _require(
            health.get("active_tool_names") == sorted(tool.name for tool in listed.tools),
            f"{surface}: health active names differ from tools/list",
            problems,
        )
        _require(
            health.get("optional_modules", {}).get("music") is music,
            f"{surface}: health music state differs from registered surface",
            problems,
        )
        if check_primitives:
            await _validate_result_payloads(client, problems)
            await _validate_primitives(client, problems)


async def _verify_legacy_client(server: Any, problems: list[str]) -> None:
    async with Client(server, mode="legacy", raise_exceptions=True) as client:
        listed = await client.list_tools()
        _require(
            len(listed.tools) == EXPECTED_DEFAULT_COUNT,
            f"legacy client saw {len(listed.tools)} tools, expected {EXPECTED_DEFAULT_COUNT}",
            problems,
        )
        called = await client.call_tool("parse_expression", {"expression": "x + 1"})
        _require(called.is_error is False, "legacy client success call failed", problems)
        _require(
            isinstance(called.structured_content, dict)
            and called.structured_content.get("success") is True,
            "legacy client lost structured payload compatibility",
            problems,
        )
        legacy_task = await client.call_tool(
            "task_run",
            {
                "spec": {
                    "name": "legacy_progress_compatibility",
                    "goal": "reify an identity expression",
                    "unknowns": ["y"],
                    "base_formulas": ["y = x"],
                }
            },
        )
        _require(
            legacy_task.is_error is False
            and isinstance(legacy_task.structured_content, dict)
            and legacy_task.structured_content.get("success") is True,
            "legacy client could not call an async Context/progress tool",
            problems,
        )


async def _verify_profile_surfaces(problems: list[str]) -> None:
    """Verify exact compact discovery and strict input behavior."""
    for profile in TOOL_PROFILES:
        if profile in {"legacy", "full"}:
            continue
        server = _create_server(music=False, profile=profile)
        async with Client(server, mode=MCP_PROTOCOL_REVISION, raise_exceptions=True) as client:
            listed = await client.list_tools()
            actual = {tool.name for tool in listed.tools}
            expected = set(profile_tool_names(profile))
            _require(
                actual == expected,
                f"profile/{profile}: exact names differ "
                f"(missing={sorted(expected - actual)}, extra={sorted(actual - expected)})",
                problems,
            )
            _require(
                all(
                    tool.input_schema.get("additionalProperties") is False for tool in listed.tools
                ),
                f"profile/{profile}: strict schemas do not forbid unknown fields",
                problems,
            )
            _require(
                all(tool.description == spec_for(tool.name).description for tool in listed.tools),
                f"profile/{profile}: concise ToolSpec descriptions differ",
                problems,
            )
            _require(
                all(
                    isinstance(schema.get("description"), str)
                    and bool(schema["description"].strip())
                    for tool in listed.tools
                    for schema in tool.input_schema.get("properties", {}).values()
                ),
                f"profile/{profile}: input property description missing",
                problems,
            )
            common_outcomes = {
                "success",
                "execution_status",
                "verification_status",
                "run_id",
                "correlation_id",
                "resources",
                "error",
            }
            _require(
                all(
                    tool.output_schema is not None
                    and tool.output_schema.get("additionalProperties") is True
                    and common_outcomes <= set(tool.output_schema.get("properties", {}))
                    for tool in listed.tools
                ),
                f"profile/{profile}: common outcome schema missing",
                problems,
            )
            _require(
                all(
                    (tool.meta or {}).get("org.nsforge/profile") == profile for tool in listed.tools
                ),
                f"profile/{profile}: runtime profile metadata differs",
                problems,
            )
            _require(
                not {"nsforge_health", "nsforge_manifest", "derivation_get_saved"} & actual,
                f"profile/{profile}: compact surface duplicated resource-first read aliases",
                problems,
            )
            health_result = await client.read_resource("nsforge://health")
            health_text = getattr(health_result.contents[0], "text", "")
            try:
                health = json.loads(health_text)
            except json.JSONDecodeError:
                health = {}
            _require(
                health.get("tool_profile") == profile,
                f"profile/{profile}: health profile differs",
                problems,
            )
            _require(
                health.get("active_tool_names") == sorted(expected),
                f"profile/{profile}: health names differ",
                problems,
            )
            _require(
                health.get("tenant_scope_mode") == "local"
                and "tenant_id" not in health
                and "tenant" not in health,
                f"profile/{profile}: health leaked tenant identity or omitted scope mode",
                problems,
            )

            if profile == "workflow":
                task_run = next(tool for tool in listed.tools if tool.name == "task_run")
                spec_schema = task_run.input_schema.get("properties", {}).get("spec", {})
                nested = spec_schema.get("properties", {})
                _require(
                    spec_schema.get("additionalProperties") is False
                    and {
                        "name",
                        "goal",
                        "unknowns",
                        "base_formulas",
                        "modifications",
                        "alternatives",
                        "acceptance",
                    }
                    <= set(nested),
                    "profile/workflow: strict nested DTS schema missing",
                    problems,
                )
                unknown = await client.call_tool(
                    "calculate_limit",
                    {
                        "expression": "x",
                        "variable": "x",
                        "point": "0",
                        "unexpected": True,
                    },
                )
                _require(
                    unknown.is_error is True
                    and isinstance(unknown.structured_content, dict)
                    and unknown.structured_content.get("error_code") == "validation",
                    "profile/workflow: unknown input field was not rejected",
                    problems,
                )
                invalid_enum = await client.call_tool(
                    "calculate_limit",
                    {
                        "expression": "x",
                        "variable": "x",
                        "point": "0",
                        "direction": "sideways",
                    },
                )
                _require(
                    invalid_enum.is_error is True
                    and isinstance(invalid_enum.structured_content, dict)
                    and invalid_enum.structured_content.get("error_code") == "validation",
                    "profile/workflow: invalid enum was not rejected",
                    problems,
                )
                invalid_numeric = await client.call_tool(
                    "task_run",
                    {
                        "spec": {
                            "name": "invalid-timeout",
                            "goal": "derive an identity",
                            "unknowns": ["y"],
                            "base_formulas": ["y = x"],
                        },
                        "timeout_s": 0,
                    },
                )
                _require(
                    invalid_numeric.is_error is True
                    and isinstance(invalid_numeric.structured_content, dict)
                    and invalid_numeric.structured_content.get("error_code") == "validation",
                    "profile/workflow: invalid numeric range was not rejected",
                    problems,
                )
                invalid_nested = await client.call_tool(
                    "task_plan",
                    {
                        "spec": {
                            "name": "invalid-nested",
                            "goal": "derive an identity",
                            "unknowns": ["y"],
                            "base_formulas": ["y = x"],
                            "modifications": [{"id": "m1", "unexpected": True}],
                        }
                    },
                )
                _require(
                    invalid_nested.is_error is True
                    and isinstance(invalid_nested.structured_content, dict)
                    and invalid_nested.structured_content.get("error_code") == "validation",
                    "profile/workflow: unknown nested DTS field was not rejected",
                    problems,
                )


async def _verify_stdio_subprocess(problems: list[str]) -> None:
    """Exercise real JSON-RPC framing and prove stdout stays protocol-clean."""
    stdio_env = dict(os.environ)
    stdio_env.pop(MUSIC_ENV, None)
    stdio_env.pop(PROFILE_ENV, None)
    stdio_env["NSFORGE_MCP_TRANSPORT"] = "stdio"
    stdio_env[RUN_DB_ENV] = ":memory:"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "nsforge_mcp.server"],
        cwd=str(REPO),
        env=stdio_env,
    )
    async with Client(
        params,
        mode=MCP_PROTOCOL_REVISION,
        read_timeout_seconds=10,
        raise_exceptions=True,
    ) as client:
        _require(
            client.protocol_version == MCP_PROTOCOL_REVISION,
            f"stdio: negotiated {client.protocol_version}, expected {MCP_PROTOCOL_REVISION}",
            problems,
        )
        listed = await client.list_tools()
        _require(
            len(listed.tools) == EXPECTED_DEFAULT_COUNT,
            f"stdio: saw {len(listed.tools)} tools, expected {EXPECTED_DEFAULT_COUNT}",
            problems,
        )
        parsed = await client.call_tool("parse_expression", {"expression": "x + 1"})
        _require(
            parsed.is_error is False
            and isinstance(parsed.structured_content, dict)
            and parsed.structured_content.get("success") is True,
            "stdio: parse_expression failed or lost structured content",
            problems,
        )


async def verify_contract() -> list[str]:
    problems: list[str] = []
    manifest = _manifest()
    _require(
        version("mcp") == EXPECTED_MCP_SDK,
        f"mcp SDK {version('mcp')} != {EXPECTED_MCP_SDK}",
        problems,
    )
    _require(
        manifest.get("schema") == "nsforge.capabilities/v4",
        f"manifest schema {manifest.get('schema')!r} != nsforge.capabilities/v4",
        problems,
    )

    default_server = _create_server(music=False)
    await _verify_modern_server(
        default_server,
        manifest,
        surface="default",
        music=False,
        profile="legacy",
        expected_count=EXPECTED_DEFAULT_COUNT,
        check_primitives=True,
        problems=problems,
    )
    await _verify_legacy_client(default_server, problems)
    await _verify_stdio_subprocess(problems)

    full_server = _create_server(music=False, profile="full")
    await _verify_modern_server(
        full_server,
        manifest,
        surface="full",
        music=True,
        profile="full",
        expected_count=EXPECTED_FULL_COUNT,
        check_primitives=False,
        problems=problems,
    )
    legacy_music = _create_server(music=True)
    async with Client(legacy_music, mode=MCP_PROTOCOL_REVISION, raise_exceptions=True) as client:
        listed = await client.list_tools()
        _require(
            len(listed.tools) == EXPECTED_FULL_COUNT
            and _contract_hash(listed.tools) == EXPECTED_CONTRACT_HASHES["full"],
            "legacy + NSFORGE_ENABLE_MUSIC=1 no longer preserves the 91-tool full contract",
            problems,
        )
    await _verify_profile_surfaces(problems)
    return problems


def main() -> int:
    try:
        problems = asyncio.run(verify_contract())
    except Exception:
        print("FAIL MCP 2.x contract: unexpected exception")
        traceback.print_exc()
        return 1

    if problems:
        print("FAIL MCP 2.x contract:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        "MCP contract ok: SDK 2.1.1 / protocol 2026-07-28, "
        "82 legacy + 91 full contracts preserved; strict profiles, structured "
        "payloads, progress, resources, prompts, and legacy mode verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
