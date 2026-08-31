"""Additive MCP resources and prompts for discovery-first clients."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver.exceptions import ResourceNotFoundError
from mcp.types import Annotations, Icon

from nsforge_mcp.composition import get_services
from nsforge_mcp.introspection import health_payload, load_manifest
from nsforge_mcp.tool_contract import MCP_PROTOCOL_REVISION, NSFORGE_ICON_URL

NORTH_STAR = (
    "Every symbol, equation, value, and line of code in a final result must have "
    'a tool call as its "birth certificate" (provenance). The AI hand-derives nothing.'
)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def _icons() -> list[Icon]:
    return [Icon(src=NSFORGE_ICON_URL, mime_type="image/svg+xml")]


def _meta(kind: str) -> dict[str, str]:
    return {
        "org.nsforge/kind": kind,
        "org.nsforge/protocolRevision": MCP_PROTOCOL_REVISION,
    }


def register_primitives(
    mcp: Any,
    *,
    health_factory: Callable[[], dict[str, Any]] = health_payload,
) -> None:
    """Register read-only resources and a provenance-first workflow prompt."""

    @mcp.resource(
        "nsforge://manifest",
        name="nsforge_manifest_resource",
        title="NSForge Capability Manifest",
        description="Machine-readable tools, modules, verification gates, and MCP contract.",
        mime_type="application/json",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=1.0),
        meta=_meta("manifest"),
    )
    def nsforge_manifest_resource() -> str:
        manifest = load_manifest()
        if manifest is None:
            raise ResourceNotFoundError("NSForge capability manifest is unavailable")
        return _json(manifest)

    @mcp.resource(
        "nsforge://health",
        name="nsforge_health_resource",
        title="NSForge Runtime Health",
        description="Live server, SDK, protocol, engine, and active-tool inventory.",
        mime_type="application/json",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=0.9),
        meta=_meta("health"),
    )
    def nsforge_health_resource() -> str:
        return _json(health_factory())

    @mcp.resource(
        "nsforge://north-star",
        name="nsforge_north_star",
        title="NSForge Provenance North Star",
        description="The invariant every NSForge derivation must preserve.",
        mime_type="text/plain",
        icons=_icons(),
        annotations=Annotations(audience=["user", "assistant"], priority=1.0),
        meta=_meta("north-star"),
    )
    def nsforge_north_star() -> str:
        return NORTH_STAR

    @mcp.resource(
        "nsforge://derivations/{result_id}",
        name="nsforge_saved_derivation",
        title="Saved NSForge Derivation",
        description="Stored derivation metadata and lineage summary, addressed by result ID.",
        mime_type="application/json",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=0.8),
        meta=_meta("saved-derivation"),
    )
    def nsforge_saved_derivation(result_id: str) -> str:
        snapshot = get_services().repository.snapshot(result_id)
        if snapshot is None:
            raise ResourceNotFoundError(f"Saved derivation {result_id!r} was not found")
        return _json(snapshot)

    @mcp.prompt(
        name="forge_verified_derivation",
        title="Forge a Verified Derivation",
        description="Plan and execute a provenance-complete derivation with NSForge tools.",
        icons=_icons(),
    )
    def forge_verified_derivation(goal: str, domain: str = "general") -> str:
        """Create a provenance-first NSForge workflow for a stated goal."""
        return (
            f"Use NSForge to derive and verify this {domain} goal: {goal}\n\n"
            "Start with nsforge_health and nsforge_manifest. Reify a task spec with "
            "task_plan, then use deterministic NSForge tools for every symbol, equation, "
            "value, transformation, verification, and generated line of code. Record all "
            "derivation steps and provenance. Do not hand-derive missing steps. Treat a "
            "negative verification as a branch to correct or explain, and finish only when "
            "the provenance ledger is complete."
        )
