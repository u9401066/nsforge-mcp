"""NSForge MCP 2.x server and transport entry point."""

from __future__ import annotations

import json
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from typing import Any

from mcp.server import CacheHint, MCPServer
from mcp.server.mcpserver import Context
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Icon, InputRequiredResult, TextContent, Tool

from nsforge import __version__
from nsforge_mcp.composition import Services, get_services
from nsforge_mcp.config import SurfaceConfig, TransportConfig, surface_config, transport_config
from nsforge_mcp.introspection import health_payload
from nsforge_mcp.primitives import register_primitives
from nsforge_mcp.tool_contract import (
    NSFORGE_ICON_URL,
    STRICT_TOOL_PROFILES,
    ToolProfile,
    common_outcome_schema,
    profile_tool_names,
    strict_enum_values,
    strict_input_description,
    strict_numeric_constraints,
    strict_task_spec_schema,
    validate_strict_task_spec,
)
from nsforge_mcp.tools import register_all_tools

logger = logging.getLogger("nsforge")

_CORRELATION_ATTRIBUTE_KEYS = {
    "run_id": "nsforge.run_id",
    "correlation_id": "nsforge.correlation_id",
}


def _current_recording_span() -> Any | None:
    """Return the SDK's active OTel span without making OTel a library requirement."""
    try:
        from opentelemetry import trace
    except ImportError:  # pragma: no cover - MCP 2 normally installs OTel
        return None
    span = trace.get_current_span()
    return span if span.is_recording() else None


def _safe_correlation_value(value: object) -> str | None:
    """Keep only short opaque identifiers out of arbitrary caller payloads."""
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        return None
    if not value.isascii() or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        for char in value
    ):
        return None
    return value


def _annotate_tool_span(
    span: Any | None,
    *,
    name: str,
    arguments: dict[str, Any],
    surface: SurfaceConfig,
) -> None:
    """Correlate a tool call without recording expressions, code, tokens, or bytes."""
    if span is None:
        return
    span.set_attribute("nsforge.tool.name", name)
    span.set_attribute("nsforge.profile", surface.profile)
    span.set_attribute("nsforge.tenant_id", surface.tenant_id)
    session_id = _safe_correlation_value(arguments.get("session_id"))
    if session_id is not None:
        span.set_attribute("nsforge.session_id", session_id)


def _annotate_result_span(span: Any | None, result: object) -> None:
    """Attach only kernel-issued result identifiers to the active tool span."""
    if span is None or not isinstance(result, CallToolResult):
        return
    payload = result.structured_content
    if not isinstance(payload, dict):
        return
    for field, attribute in _CORRELATION_ATTRIBUTE_KEYS.items():
        value = _safe_correlation_value(payload.get(field))
        if value is not None:
            span.set_attribute(attribute, value)


@asynccontextmanager
async def _lifespan(_: MCPServer[Services]) -> AsyncIterator[Services]:
    """Warm and expose the process-wide composition root to MCP contexts."""
    yield get_services()


def _strict_error(message: str, *, details: dict[str, Any]) -> CallToolResult:
    payload = {
        "success": False,
        "execution_status": "error",
        "error_code": "validation",
        "error": message,
        "details": details,
    }
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            )
        ],
        structured_content=payload,
        is_error=True,
    )


class ProfiledMCPServer(MCPServer[Services]):
    """MCPServer with a startup-frozen surface and compact-profile validation."""

    tool_profile: ToolProfile = "legacy"
    active_tool_names: frozenset[str] = frozenset()
    surface: SurfaceConfig

    async def list_tools(self) -> list[Tool]:
        tools = await super().list_tools()
        if self.tool_profile not in STRICT_TOOL_PROFILES:
            return tools

        strict_tools: list[Tool] = []
        for tool in tools:
            input_schema = dict(tool.input_schema)
            properties = {
                name: dict(schema) for name, schema in input_schema.get("properties", {}).items()
            }
            for field, values in strict_enum_values(tool.name).items():
                if field in properties:
                    properties[field]["enum"] = list(values)
            for rule in strict_numeric_constraints(tool.name):
                if rule.field not in properties:
                    continue
                candidates = properties[rule.field].get("anyOf")
                numeric_schemas = (
                    [item for item in candidates if item.get("type") in {"integer", "number"}]
                    if isinstance(candidates, list)
                    else [properties[rule.field]]
                )
                for schema in numeric_schemas:
                    if rule.minimum is not None:
                        key = "exclusiveMinimum" if rule.exclusive_minimum else "minimum"
                        schema[key] = rule.minimum
                    if rule.maximum is not None:
                        schema["maximum"] = rule.maximum
            if tool.name in {"task_plan", "task_run", "task_explore"} and "spec" in properties:
                properties["spec"] = strict_task_spec_schema()
            for field, schema in properties.items():
                schema.setdefault("description", strict_input_description(tool.name, field))
            input_schema["properties"] = properties
            input_schema["additionalProperties"] = False
            output_schema = common_outcome_schema()
            existing_output = tool.output_schema or {}
            existing_properties = existing_output.get("properties", {})
            if isinstance(existing_properties, dict):
                output_schema["properties"] = {
                    **existing_properties,
                    **output_schema["properties"],
                }
            strict_tools.append(
                tool.model_copy(
                    update={"input_schema": input_schema, "output_schema": output_schema}
                )
            )
        return strict_tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Context[Services, Any] | None = None,
    ) -> CallToolResult | InputRequiredResult:
        span = _current_recording_span()
        _annotate_tool_span(
            span,
            name=name,
            arguments=arguments,
            surface=self.surface,
        )
        if self.tool_profile in STRICT_TOOL_PROFILES:
            tool = next((item for item in await self.list_tools() if item.name == name), None)
            if tool is not None:
                allowed = set(tool.input_schema.get("properties", {}))
                unknown = sorted(set(arguments) - allowed)
                if unknown:
                    return _strict_error(
                        f"unknown input field(s) for {name}: {', '.join(unknown)}",
                        details={"tool": name, "unknown_fields": unknown},
                    )
                if name in {"task_plan", "task_run", "task_explore"}:
                    issues = validate_strict_task_spec(arguments.get("spec"))
                    if issues:
                        return _strict_error(
                            f"invalid strict Derivation Task Spec for {name}",
                            details={"tool": name, "field": "spec", "issues": issues},
                        )
                for field, values in strict_enum_values(name).items():
                    if field in arguments and arguments[field] not in values:
                        return _strict_error(
                            f"invalid value for {name}.{field}",
                            details={
                                "tool": name,
                                "field": field,
                                "allowed": list(values),
                            },
                        )
                for rule in strict_numeric_constraints(name):
                    value = arguments.get(rule.field)
                    if value is None:
                        continue
                    if isinstance(value, bool) or not isinstance(value, int | float):
                        return _strict_error(
                            f"invalid numeric value for {name}.{rule.field}",
                            details={"tool": name, "field": rule.field},
                        )
                    below = (
                        value <= rule.minimum
                        if rule.exclusive_minimum and rule.minimum is not None
                        else rule.minimum is not None and value < rule.minimum
                    )
                    above = rule.maximum is not None and value > rule.maximum
                    if below or above:
                        return _strict_error(
                            f"numeric value out of range for {name}.{rule.field}",
                            details={
                                "tool": name,
                                "field": rule.field,
                                **rule.manifest_dict(),
                            },
                        )
        result = await super().call_tool(name, arguments, context)
        _annotate_result_span(span, result)
        return result


def create_server() -> ProfiledMCPServer:
    """Build a fully registered server from the current module environment."""
    surface = surface_config()
    active_names = profile_tool_names(
        surface.profile,
        legacy_music=surface.legacy_music,
    )
    module_state = {"music": any(name.startswith("music_") for name in active_names)}
    instance_health = partial(
        health_payload,
        module_state=module_state,
        profile=surface.profile,
        active_tool_names=active_names,
        tenant_scope_mode=surface.tenant_scope_mode,
    )
    server = ProfiledMCPServer(
        name="nsforge",
        title="Neurosymbolic Forge",
        description=(
            "Turn concepts into verifiable, provenance-tracked symbols, derivations, "
            "algorithms, and generated code."
        ),
        version=__version__,
        instructions=(
            f"Neurosymbolic Forge v{__version__}. Use deterministic tools for every "
            "symbol, equation, value, verification, and generated line of code; each "
            "result must retain a complete tool-provenance birth certificate. Read "
            "nsforge://manifest or call nsforge_manifest for live capabilities."
        ),
        website_url="https://github.com/u9401066/nsforge-mcp",
        icons=[Icon(src=NSFORGE_ICON_URL, mime_type="image/svg+xml")],
        lifespan=_lifespan,
        cache_hints={
            "tools/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/templates/list": CacheHint(ttl_ms=300_000, scope="public"),
            "prompts/list": CacheHint(ttl_ms=300_000, scope="public"),
            "server/discover": CacheHint(ttl_ms=300_000, scope="public"),
        },
    )
    server.tool_profile = surface.profile
    server.active_tool_names = active_names
    server.surface = surface
    register_all_tools(
        server,
        profile=surface.profile,
        active_tool_names=active_names,
        module_state=module_state,
        health_factory=instance_health,
    )
    register_primitives(
        server,
        health_factory=instance_health,
        tenant_id=surface.tenant_id,
    )
    return server


# Import-time instance retained for existing Python integrations and the CLI.
mcp = create_server()


def _configure_logging() -> None:
    """Send logs to stderr; stdout is reserved for the stdio protocol."""
    logger.setLevel(os.environ.get("NSFORGE_LOG_LEVEL", "INFO").upper())
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False


def _transport_security(config: TransportConfig) -> TransportSecuritySettings:
    """Build mandatory Host/Origin validation for every HTTP bind."""
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(config.allowed_hosts),
        allowed_origins=list(config.allowed_origins),
    )


def main() -> None:
    """Run stdio by default or explicitly opted-in Streamable HTTP."""
    _configure_logging()
    config = transport_config()
    active_names: frozenset[str] = getattr(mcp, "active_tool_names", frozenset())
    profile = getattr(mcp, "tool_profile", "legacy")
    logger.info(
        "NSForge MCP v%s starting (%s, profile=%s, tools=%s) — music %s",
        __version__,
        config.transport,
        profile,
        len(active_names),
        "enabled" if "music_generate_wav" in active_names else "disabled",
    )
    if config.transport == "stdio":
        mcp.run("stdio")
        return
    logger.info("Streamable HTTP listening on %s:%s%s", config.host, config.port, config.path)
    mcp.run(
        "streamable-http",
        host=config.host,
        port=config.port,
        streamable_http_path=config.path,
        json_response=config.json_response,
        stateless_http=config.stateless_http,
        transport_security=_transport_security(config),
    )


if __name__ == "__main__":
    main()
