"""Additive MCP resources and prompts for discovery-first clients."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from functools import partial
from typing import Any

from mcp.server.mcpserver.exceptions import ResourceNotFoundError
from mcp.types import Annotations, Icon

from nsforge.application.run_store import RunStore
from nsforge.infrastructure.sqlite_run_store import (
    default_run_store_path,
    default_tenant_id,
    get_run_store,
)
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
    run_store_factory: Callable[[], RunStore] = get_run_store,
    tenant_id: str | None = None,
) -> None:
    """Register read-only resources and a provenance-first workflow prompt."""

    surface = getattr(mcp, "surface", None)
    configured_tenant = getattr(surface, "tenant_id", None)
    configured_store_path = getattr(surface, "run_store_path", None)
    resource_tenant = tenant_id or configured_tenant or default_tenant_id()
    captured_store_factory = (
        partial(
            get_run_store,
            str(configured_store_path or default_run_store_path()),
        )
        if run_store_factory is get_run_store
        else run_store_factory
    )

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

    @mcp.resource(
        "nsforge://sessions/{session_id}",
        name="nsforge_derivation_session",
        title="NSForge Derivation Session",
        description="Detached status, current expression, and step history for a process session.",
        mime_type="application/json",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=0.9),
        meta=_meta("derivation-session"),
    )
    def nsforge_derivation_session(session_id: str) -> str:
        session = get_services().session_manager.get(session_id)
        if session is None:
            raise ResourceNotFoundError(f"Derivation session {session_id!r} was not found")
        # Capture only detached read fields under the session transaction.  Do
        # not serialize ``_persist_path`` or retain mutable step/list aliases.
        with session.transaction():
            current_expression = (
                str(session.current_expression) if session.current_expression is not None else None
            )
            snapshot: dict[str, Any] = copy.deepcopy(
                {
                    "session_id": session.session_id,
                    "name": session.name,
                    "description": session.description,
                    "status": session.status.value,
                    "current_expression": current_expression,
                    "current_formula_id": session.current_formula_id,
                    "formulas_loaded": list(session.formulas),
                    "steps": [step.to_dict() for step in session.steps],
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                }
            )
        return _json(
            {
                "session_id": snapshot["session_id"],
                "name": snapshot["name"],
                "description": snapshot["description"],
                "status": snapshot["status"],
                "step_count": len(snapshot["steps"]),
                "current_expression": snapshot["current_expression"],
                "current_formula_id": snapshot["current_formula_id"],
                "formulas_loaded": snapshot["formulas_loaded"],
                "steps": snapshot["steps"],
                "created_at": snapshot["created_at"],
                "updated_at": snapshot["updated_at"],
            }
        )

    @mcp.resource(
        "nsforge://runs/{run_id}",
        name="nsforge_strict_run",
        title="NSForge Strict Run",
        description="Immutable tenant-scoped run, provenance, evidence, and artifact metadata.",
        mime_type="application/json",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=1.0),
        meta=_meta("strict-run"),
    )
    def nsforge_strict_run(run_id: str) -> str:
        snapshot = captured_store_factory().snapshot(resource_tenant, run_id)
        if snapshot is None:
            raise ResourceNotFoundError(f"Strict run {run_id!r} was not found")
        return _json(snapshot)

    @mcp.resource(
        "nsforge://runs/{run_id}/events",
        name="nsforge_strict_run_events",
        title="NSForge Strict Run Events",
        description="Ordered, canonical-digest-linked phase events for one strict run.",
        mime_type="application/json",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=0.9),
        meta=_meta("strict-run-events"),
    )
    def nsforge_strict_run_events(run_id: str) -> str:
        store = captured_store_factory()
        if store.get_run(resource_tenant, run_id) is None:
            raise ResourceNotFoundError(f"Strict run {run_id!r} was not found")
        return _json(
            {
                "run_id": run_id,
                "events": [event.to_dict() for event in store.list_events(resource_tenant, run_id)],
            }
        )

    @mcp.resource(
        "nsforge://artifacts/{sha256}",
        name="nsforge_strict_artifact",
        title="NSForge Strict Artifact",
        description="Immutable content-addressed artifact bytes; MIME is carried by its ResourceLink.",
        mime_type="application/octet-stream",
        icons=_icons(),
        annotations=Annotations(audience=["assistant"], priority=0.9),
        meta=_meta("strict-artifact"),
    )
    def nsforge_strict_artifact(sha256: str) -> bytes:
        resolved = captured_store_factory().get_artifact(resource_tenant, sha256)
        if resolved is None:
            raise ResourceNotFoundError(f"Strict artifact {sha256!r} was not found")
        _, content = resolved
        return content

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
