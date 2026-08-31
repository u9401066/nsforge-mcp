"""
Task orchestration tools (L2 DTS + L3 orchestrator) — the MCP surface.

Turns a declarative Derivation Task Spec (DTS) into a provenance-tagged plan of
tool calls, and runs the deterministic phases of the reification ladder. This is
how a general agent runs a large derivation task from a single declarative spec.

See docs/reification-ladder-direction.md.
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Annotated, Any

from mcp.server.mcpserver import Context, Resolve

from nsforge.application.strict_run import PhaseEventSink, StrictRunService
from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.strict_provenance import PhaseEvent
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sqlite_run_store import get_run_store
from nsforge.infrastructure.timeout import ComputationTimeout, run_with_timeout
from nsforge_mcp.composition import get_services


@dataclass(frozen=True, slots=True)
class ExecutionScope:
    """Pickle-safe server trust scope injected outside the public tool schema."""

    profile: str
    tenant_id: str
    run_store_path: str
    correlation_seed: str


def _resolve_execution_scope(ctx: Context[Any, Any]) -> ExecutionScope:
    """Resolve immutable startup state; no caller field or live env is consulted."""

    server = ctx.mcp_server
    surface = getattr(server, "surface", None)
    seed = getattr(server, "_nsforge_correlation_seed", None)
    if surface is None or not isinstance(seed, str):
        raise RuntimeError("NSForge execution scope was not initialized at server startup")
    return ExecutionScope(
        profile=str(surface.profile),
        tenant_id=str(surface.tenant_id),
        run_store_path=str(surface.run_store_path),
        correlation_seed=seed,
    )


def _service_for_scope(scope: ExecutionScope) -> StrictRunService:
    return StrictRunService(
        get_run_store(scope.run_store_path),
        tenant_id=scope.tenant_id,
        profile=scope.profile,
        correlation_seed=scope.correlation_seed,
    )


def _resource_payload(
    resources: tuple[Any, ...],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    public = [resource.to_dict() for resource in resources]
    sentinel = [
        {
            "name": str(item["name"]),
            "uri": str(item["uri"]),
            "title": str(item["name"]),
            "description": str(item["description"]),
            "mime_type": str(item["mime_type"]),
            **({"size": item["size"]} if "size" in item else {}),
        }
        for item in public
    ]
    return public, sentinel


def _execute_task_run(
    spec: dict[str, Any],
    event_sink: PhaseEventSink | None = None,
    *,
    strict_service: StrictRunService | None = None,
    execution_scope: ExecutionScope | None = None,
) -> dict[str, Any]:
    """Reify + run a DTS through the reification ladder (see ``task_run``).

    Module-level (not a closure) so :func:`run_with_timeout` can ship it to a
    worker process under ``spawn``.
    """
    try:
        dts = DerivationTaskSpec.from_dict(spec)
    except (KeyError, ValueError) as exc:
        return {"success": False, "error": f"invalid spec: {exc}"}

    services = get_services()
    if strict_service is None:
        if execution_scope is None:
            raise RuntimeError("task execution requires an injected server scope")
        strict_service = _service_for_scope(execution_scope)
    execution = strict_service.execute_task(
        dts,
        spec_payload=spec,
        engine=services.engine,
        verifier=services.verifier,
        event_sink=event_sink,
    )
    result = execution.result
    resources, resource_links = _resource_payload(execution.resources)
    return {
        "success": result.ok,
        "spec": result.spec_name,
        "derived_expression": result.derived_expression,
        "generated_code": result.generated_code,
        "verified": result.verified,
        "attempts": [
            {"label": a.label, "derived": a.derived, "verified": a.verified}
            for a in result.attempts
        ],
        "provenance": {
            "complete": result.provenance.is_complete,
            "entries": [
                {"entity": e.entity, "tool": e.tool, "source": e.source}
                for e in result.provenance.entries
            ],
        },
        "acceptance": [
            {"kind": o.kind, "status": o.status, "detail": o.detail} for o in result.acceptance
        ],
        "phases": [
            {
                "phase": phase.phase.value,
                "status": phase.status.value,
                "detail": phase.detail,
                "steps": [
                    {
                        "phase": s.phase.value,
                        "tool": s.tool,
                        "purpose": s.purpose,
                        "executor": s.executor,
                    }
                    for s in phase.steps
                ],
            }
            for phase in result.phases
        ],
        "execution_status": execution.bundle.run.status.value,
        "verification_status": execution.verification_status,
        "run_id": execution.bundle.run.run_id,
        "correlation_id": execution.bundle.run.correlation_id,
        "revision": execution.bundle.run.revision,
        "resources": resources,
        "_resource_links": resource_links,
        "_phase_events": [event.to_dict() for event in execution.bundle.events],
    }


def _execute_task_explore(
    spec: dict[str, Any],
    event_sink: PhaseEventSink | None = None,
    *,
    strict_service: StrictRunService | None = None,
    execution_scope: ExecutionScope | None = None,
) -> dict[str, Any]:
    """Reify + explore a branching DTS (see ``task_explore``).

    Module-level for the same worker-process reason as :func:`_execute_task_run`.
    """
    try:
        dts = DerivationTaskSpec.from_dict(spec)
    except (KeyError, ValueError) as exc:
        return {"success": False, "error": f"invalid spec: {exc}"}

    services = get_services()
    if strict_service is None:
        if execution_scope is None:
            raise RuntimeError("task execution requires an injected server scope")
        strict_service = _service_for_scope(execution_scope)
    execution = strict_service.execute_explore(
        dts,
        spec_payload=spec,
        engine=services.engine,
        verifier=services.verifier,
        event_sink=event_sink,
    )
    result = execution.result
    resources, resource_links = _resource_payload(execution.resources)
    return {
        "success": True,
        "concept": result.concept,
        "candidates": [
            {
                "label": c.label,
                "derived_expression": c.derived,
                "verified": c.verified,
                "provenance_complete": c.provenance_complete,
                "oracles": f"{c.oracles_passed}/{c.oracles_total}",
                "generated_code": c.generated_code,
            }
            for c in result.candidates
        ],
        "execution_status": execution.bundle.run.status.value,
        "verification_status": execution.verification_status,
        "run_id": execution.bundle.run.run_id,
        "correlation_id": execution.bundle.run.correlation_id,
        "revision": execution.bundle.run.revision,
        "resources": resources,
        "_resource_links": resource_links,
        "_phase_events": [event.to_dict() for event in execution.bundle.events],
    }


def _supports_event_sink(operation: Callable[..., dict[str, Any]]) -> bool:
    return "event_sink" in inspect.signature(operation).parameters


def _call_operation(
    operation: Callable[..., dict[str, Any]],
    spec: dict[str, Any],
    event_sink: PhaseEventSink,
) -> dict[str, Any]:
    if _supports_event_sink(operation):
        return operation(spec, event_sink=event_sink)
    return operation(spec)


async def _run_with_progress(
    ctx: Context[Any, Any],
    operation: Callable[..., dict[str, Any]],
    spec: dict[str, Any],
    timeout_s: float | None,
    label: str,
) -> dict[str, Any]:
    """Run orchestration off-loop; immutable phase events drive progress."""
    await ctx.report_progress(0.0, 1.0, f"Starting {label}")
    reported_sequences: set[int] = set()

    async def report_event(event: PhaseEvent) -> None:
        if event.sequence in reported_sequences:
            return
        reported_sequences.add(event.sequence)
        # This monotonic transform conveys event ordering without inventing a
        # phase count.  The factual completion boundary remains exactly 1.0.
        progress = event.sequence / (event.sequence + 1.0)
        await ctx.report_progress(
            progress,
            1.0,
            f"{event.phase}: {event.status} ({event.tool})",
        )

    if timeout_s is None:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[PhaseEvent] = asyncio.Queue()

        def receive_event(event: PhaseEvent) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, event)

        worker = asyncio.create_task(
            asyncio.to_thread(_call_operation, operation, spec, receive_event)
        )
        while not worker.done():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.05)
            except TimeoutError:
                continue
            await report_event(event)
        result = await worker
        while not queue.empty():
            await report_event(queue.get_nowait())
    else:
        try:
            result = await asyncio.to_thread(run_with_timeout, operation, spec, timeout=timeout_s)
        except ComputationTimeout as exc:
            result = {"success": False, "error": str(exc), "timed_out": True}

    serialized_events = result.pop("_phase_events", [])
    for raw in serialized_events:
        await report_event(PhaseEvent(**raw))

    notify = getattr(ctx, "notify_resource_updated", None)
    if notify is not None:
        # Run/artifact resources are immutable.  Exact notifications mainly
        # serve clients that learned the URI from this concurrent call.
        for resource in result.get("resources", []):
            await notify(str(resource["uri"]))
    notify_list_changed = getattr(ctx, "notify_resources_changed", None)
    if notify_list_changed is not None and result.get("resources"):
        # run_id is server-generated, so pre-call listeners discover newly
        # available immutable resources through the list-changed level trigger.
        await notify_list_changed()

    # Do not put this in ``finally``: cancelling an await on ``to_thread`` does
    # not stop the worker, so a "Finished" event there would be factually false.
    await ctx.report_progress(1.0, 1.0, f"Finished {label}")
    return result


def register_task_tools(mcp: Any) -> None:
    """Register the L2/L3 task orchestration tools with the MCP server."""

    # Resolve() reads this startup-generated seed plus the server's frozen
    # SurfaceConfig.  It is never accepted as a public task argument.
    server = getattr(mcp, "_mcp", mcp)
    if not hasattr(server, "_nsforge_correlation_seed"):
        server._nsforge_correlation_seed = uuid.uuid4().hex

    @mcp.tool()
    def task_plan(spec: dict[str, Any]) -> dict[str, Any]:
        """
        Reify a Derivation Task Spec (DTS) into an ordered plan of tool calls.

        Each planned step names the tool that would produce it (provenance),
        spanning the reification ladder: symbol -> derivation -> algorithm.

        Args:
            spec: A DTS dict with keys: name, goal, given, unknowns, assumptions,
                  base_formulas, modifications, acceptance, metadata.

        Returns:
            {"success": bool, "spec": str, "total": int, "steps": [...]}.
        """
        try:
            dts = DerivationTaskSpec.from_dict(spec)
        except (KeyError, ValueError) as exc:
            return {"success": False, "error": f"invalid spec: {exc}"}

        plan = TaskOrchestrator(dts).plan()
        return {
            "success": True,
            "spec": dts.name,
            "total": len(plan),
            "steps": [
                {
                    "phase": step.phase.value,
                    "tool": step.tool,
                    "purpose": step.purpose,
                    "args": step.args,
                    "executor": step.executor,
                }
                for step in plan
            ],
        }

    @mcp.tool()
    async def task_run(
        spec: dict[str, Any],
        ctx: Context[Any, Any],
        scope: Annotated[ExecutionScope, Resolve(_resolve_execution_scope)],
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        """
        Run the DTS through the reification ladder.

        Concept (validation), symbol (registry), and derivation (composing base
        formulas via substitution + solving on the SymPy engine) rungs execute
        deterministically; when a derivation is produced, the algorithm rung
        reifies it into a Python function. The composed formula is returned in
        "derived_expression" and the code in "generated_code".

        Args:
            spec: A DTS dict (see task_plan).
            timeout_s: Optional hard wall-clock cap (seconds). When set, the
                derivation runs in a separate process and is killed if it
                overruns, returning {"success": False, "timed_out": True}.

        Returns:
            {"success", "spec", "derived_expression", "generated_code", "phases"}.
        """
        operation = partial(_execute_task_run, execution_scope=scope)
        return await _run_with_progress(ctx, operation, spec, timeout_s, "task run")

    @mcp.tool()
    async def task_explore(
        spec: dict[str, Any],
        ctx: Context[Any, Any],
        scope: Annotated[ExecutionScope, Resolve(_resolve_execution_scope)],
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        """
        Explore a branching derivation tree from a DTS.

        Runs the base derivation plus each ``alternatives`` candidate through the
        full loop and returns ALL candidates -- each with its acceptance result
        and provenance -- ranked best-first (verified > more oracles passed >
        simpler). Unlike task_run (which self-corrects to the first passing
        branch), this surfaces the whole space of verified answers.

        Args:
            spec: A DTS dict (see task_plan); ``alternatives`` are the branches.
            timeout_s: Optional hard wall-clock cap (seconds). When set, the
                exploration runs in a separate process and is killed if it
                overruns, returning {"success": False, "timed_out": True}.

        Returns:
            {"success", "concept", "candidates": [...]} ranked best-first.
        """
        operation = partial(_execute_task_explore, execution_scope=scope)
        return await _run_with_progress(ctx, operation, spec, timeout_s, "task exploration")
