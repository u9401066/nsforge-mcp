"""Application kernel for immutable, tenant-scoped strict workflow runs."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from nsforge.application.explorer import ExploreCandidate, Explorer, ExploreResult
from nsforge.application.run_store import RunStore
from nsforge.application.task_orchestrator import TaskOrchestrator, TaskRunResult
from nsforge.domain.services import SymbolicEngine, Verifier
from nsforge.domain.strict_provenance import (
    Artifact,
    ArtifactPayload,
    EvidenceOrigin,
    EvidenceOutcome,
    PhaseEvent,
    ProvenanceNode,
    Run,
    RunBundle,
    RunStatus,
    VerificationEvidence,
    canonical_sha256,
    content_sha256,
    evaluate_codegen_eligibility,
    phase_event_digest,
    provenance_node_digest,
    verification_evidence_digest,
)
from nsforge.domain.task_spec import DerivationTaskSpec

VERIFICATION_POLICY = "nsforge.acceptance/v1"
STRICT_VERIFICATION_PROFILES = frozenset({"workflow", "scientific", "interactive"})

type Clock = Callable[[], str]
type IdFactory = Callable[[], str]
type PhaseEventSink = Callable[[PhaseEvent], None]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _current_span() -> Any:
    try:
        from opentelemetry import trace
    except ImportError:  # pragma: no cover - MCP 2 installs OTel, library use need not
        return None
    return trace.get_current_span()


def _observe_run(run: Run) -> None:
    span = _current_span()
    if span is None or not span.is_recording():
        return
    span.set_attribute("nsforge.run_id", run.run_id)
    span.set_attribute("nsforge.tenant_id", run.tenant_id)
    span.set_attribute("nsforge.correlation_id", run.correlation_id)
    span.set_attribute("nsforge.profile", run.profile)


def _observe_event(event: PhaseEvent) -> None:
    span = _current_span()
    if span is None or not span.is_recording():
        return
    span.add_event(
        "nsforge.phase",
        {
            "nsforge.run_id": event.run_id,
            "nsforge.tenant_id": event.tenant_id,
            "nsforge.phase": event.phase,
            "nsforge.phase_status": event.status,
            "nsforge.tool": event.tool,
            "nsforge.sequence": event.sequence,
        },
    )


@dataclass(frozen=True, slots=True)
class ResourceReference:
    uri: str
    name: str
    mime_type: str
    description: str
    size: int | None = None

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "uri": self.uri,
            "name": self.name,
            "mime_type": self.mime_type,
            "description": self.description,
        }
        if self.size is not None:
            value["size"] = self.size
        return value


@dataclass(frozen=True, slots=True)
class StrictTaskExecution:
    result: TaskRunResult
    bundle: RunBundle
    resources: tuple[ResourceReference, ...]
    verification_status: str


@dataclass(frozen=True, slots=True)
class StrictExploreExecution:
    result: ExploreResult
    bundle: RunBundle
    resources: tuple[ResourceReference, ...]
    verification_status: str


class _RunRecorder:
    def __init__(
        self,
        run: Run,
        *,
        clock: Clock,
        event_sink: PhaseEventSink | None,
    ) -> None:
        self.run = run
        self.clock = clock
        self.event_sink = event_sink
        self.events: list[PhaseEvent] = []
        # Persisted events contain the canonical digest.  This trusted sidecar
        # retains the originating payload long enough to build provenance from
        # actual execution, rather than reconstructing it from descriptions.
        self.records: list[tuple[PhaseEvent, dict[str, object]]] = []

    def emit(
        self,
        phase: str,
        status: str,
        tool: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        sequence = len(self.events) + 1
        parent = self.events[-1].event_digest if self.events else self.run.input_digest
        event_payload = dict(payload or {})
        payload_digest = canonical_sha256(event_payload)
        timestamp = self.clock()
        digest = phase_event_digest(
            run_id=self.run.run_id,
            tenant_id=self.run.tenant_id,
            sequence=sequence,
            phase=phase,
            status=status,
            tool=tool,
            parent_digest=parent,
            payload_digest=payload_digest,
            timestamp=timestamp,
        )
        event = PhaseEvent(
            run_id=self.run.run_id,
            tenant_id=self.run.tenant_id,
            sequence=sequence,
            phase=phase,
            status=status,
            tool=tool,
            parent_digest=parent,
            payload_digest=payload_digest,
            timestamp=timestamp,
            event_digest=digest,
        )
        self.events.append(event)
        self.records.append((event, event_payload))
        _observe_event(event)
        if self.event_sink is not None:
            self.event_sink(event)


def _entity_digest(kind: str, value: str) -> str:
    return canonical_sha256({"kind": kind, "value": value})


def _node(
    *,
    run: Run,
    entity_digest: str,
    producer: str,
    input_digest: str,
    output_digest: str | None = None,
    parent_digests: tuple[str, ...],
    trusted: bool,
) -> ProvenanceNode:
    resolved_output_digest = output_digest or entity_digest
    digest = provenance_node_digest(
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        entity_digest=entity_digest,
        producer=producer,
        input_digest=input_digest,
        output_digest=resolved_output_digest,
        parent_digests=parent_digests,
        trusted=trusted,
    )
    return ProvenanceNode(
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        entity_digest=entity_digest,
        producer=producer,
        input_digest=input_digest,
        output_digest=resolved_output_digest,
        parent_digests=parent_digests,
        trusted=trusted,
        node_digest=digest,
    )


def _build_provenance(
    run: Run,
    spec: DerivationTaskSpec,
    records: tuple[tuple[PhaseEvent, dict[str, object]], ...],
) -> tuple[dict[str, ProvenanceNode], tuple[str, ...]]:
    """Build a birth-certificate chain from actual canonical phase events."""

    nodes: dict[str, ProvenanceNode] = {}
    roots: list[str] = []
    for formula in spec.base_formulas:
        entity = _entity_digest("input-expression/v1", formula)
        roots.append(entity)
        nodes.setdefault(
            entity,
            _node(
                run=run,
                entity_digest=entity,
                producer="input:task-spec",
                input_digest=run.input_digest,
                parent_digests=(),
                trusted=False,
            ),
        )

    parents: tuple[str, ...] = tuple(roots)
    for event, _payload in records:
        entity = canonical_sha256(
            {
                "kind": "phase-event-output/v1",
                "event_digest": event.event_digest,
            }
        )
        node = _node(
            run=run,
            entity_digest=entity,
            producer=event.tool,
            input_digest=event.parent_digest,
            output_digest=event.payload_digest,
            parent_digests=parents,
            trusted=True,
        )
        nodes[entity] = node
        parents = (entity,)
    return nodes, parents


def _bind_final_subject(
    *,
    run: Run,
    nodes: dict[str, ProvenanceNode],
    parents: tuple[str, ...],
    derived_expression: str,
) -> str:
    subject = _entity_digest("expression/v1", derived_expression)
    nodes[subject] = _node(
        run=run,
        entity_digest=subject,
        producer="engine.simplify",
        input_digest=canonical_sha256(
            {"parents": list(parents), "derived_expression": derived_expression}
        ),
        parent_digests=parents,
        trusted=True,
    )
    return subject


def _evidence_outcome(result: TaskRunResult) -> EvidenceOutcome:
    if not result.acceptance:
        return EvidenceOutcome.INCONCLUSIVE
    statuses = {outcome.status for outcome in result.acceptance}
    if statuses == {"verified"}:
        return EvidenceOutcome.PASS
    if "error" in statuses:
        return EvidenceOutcome.ERROR
    if "failed" in statuses:
        return EvidenceOutcome.FAIL
    return EvidenceOutcome.INCONCLUSIVE


def _explore_evidence_outcome(candidate: ExploreCandidate) -> EvidenceOutcome:
    if not candidate.acceptance:
        return EvidenceOutcome.INCONCLUSIVE
    statuses = {outcome.status for outcome in candidate.acceptance}
    if statuses == {"verified"}:
        return EvidenceOutcome.PASS
    if "error" in statuses:
        return EvidenceOutcome.ERROR
    if "failed" in statuses:
        return EvidenceOutcome.FAIL
    return EvidenceOutcome.INCONCLUSIVE


def _make_evidence(
    *,
    run: Run,
    subject_digest: str,
    outcome: EvidenceOutcome,
    details: object,
    clock: Clock,
    id_factory: IdFactory,
) -> VerificationEvidence:
    evidence_id = id_factory()
    created_at = clock()
    details_digest = canonical_sha256(details)
    digest = verification_evidence_digest(
        evidence_id=evidence_id,
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        verifier="nsforge.acceptance-orchestrator",
        subject_digest=subject_digest,
        policy=VERIFICATION_POLICY,
        outcome=outcome,
        details_digest=details_digest,
        created_revision=1,
        created_at=created_at,
        origin=EvidenceOrigin.KERNEL,
        trusted=True,
    )
    return VerificationEvidence(
        evidence_id=evidence_id,
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        verifier="nsforge.acceptance-orchestrator",
        subject_digest=subject_digest,
        policy=VERIFICATION_POLICY,
        outcome=outcome,
        details_digest=details_digest,
        created_revision=1,
        created_at=created_at,
        origin=EvidenceOrigin.KERNEL,
        trusted=True,
        evidence_digest=digest,
    )


def make_caller_assertion_evidence(
    *,
    run: Run,
    subject_digest: str,
    assertion: object,
    clock: Clock = _utc_now,
    id_factory: IdFactory = _new_id,
) -> VerificationEvidence:
    """Record a caller claim without ever upgrading it to trusted evidence."""

    evidence_id = id_factory()
    created_at = clock()
    details_digest = canonical_sha256(assertion)
    digest = verification_evidence_digest(
        evidence_id=evidence_id,
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        verifier="caller-assertion",
        subject_digest=subject_digest,
        policy=VERIFICATION_POLICY,
        outcome=EvidenceOutcome.ASSERTED,
        details_digest=details_digest,
        created_revision=run.revision,
        created_at=created_at,
        origin=EvidenceOrigin.CALLER_ASSERTION,
        trusted=False,
    )
    return VerificationEvidence(
        evidence_id=evidence_id,
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        verifier="caller-assertion",
        subject_digest=subject_digest,
        policy=VERIFICATION_POLICY,
        outcome=EvidenceOutcome.ASSERTED,
        details_digest=details_digest,
        created_revision=run.revision,
        created_at=created_at,
        origin=EvidenceOrigin.CALLER_ASSERTION,
        trusted=False,
        evidence_digest=digest,
    )


def _render_pseudocode(spec: DerivationTaskSpec, derived: str) -> str:
    lhs, _, rhs = derived.partition("=")
    inputs = ", ".join(sorted(spec.given)) or "none"
    return "\n".join(
        (
            f"ALGORITHM {spec.name}",
            f"INPUTS {inputs}",
            f"COMPUTE {lhs.strip()} <- {rhs.strip()}",
            f"RETURN {lhs.strip()}",
        )
    )


def _artifact_payload(
    *,
    run: Run,
    evidence: VerificationEvidence,
    content: bytes,
    media_type: str,
    clock: Clock,
) -> ArtifactPayload:
    sha256 = content_sha256(content)
    artifact = Artifact(
        sha256=sha256,
        tenant_id=run.tenant_id,
        media_type=media_type,
        size=len(content),
        producer_run_id=run.run_id,
        verification_evidence_id=evidence.evidence_id,
        storage_locator=f"nsforge://artifacts/{sha256}",
        created_revision=1,
        created_at=clock(),
    )
    return ArtifactPayload(artifact=artifact, content=content)


def _resources(run: Run, artifacts: tuple[ArtifactPayload, ...]) -> tuple[ResourceReference, ...]:
    refs = [
        ResourceReference(
            uri=f"nsforge://runs/{run.run_id}",
            name=f"run-{run.run_id}",
            mime_type="application/json",
            description="Immutable strict-run snapshot and provenance lineage.",
        ),
        ResourceReference(
            uri=f"nsforge://runs/{run.run_id}/events",
            name=f"run-{run.run_id}-events",
            mime_type="application/json",
            description="Ordered, digest-linked phase events for this run.",
        ),
    ]
    refs.extend(
        ResourceReference(
            uri=payload.artifact.storage_locator,
            name=f"artifact-{payload.artifact.sha256[:12]}",
            mime_type=payload.artifact.media_type,
            description="Immutable, verification-bound NSForge artifact.",
            size=payload.artifact.size,
        )
        for payload in artifacts
    )
    return tuple(refs)


class StrictRunService:
    """Create and atomically persist trusted task/explore executions."""

    def __init__(
        self,
        store: RunStore,
        *,
        tenant_id: str,
        profile: str = "workflow",
        correlation_seed: str | None = None,
        clock: Clock = _utc_now,
        id_factory: IdFactory = _new_id,
    ) -> None:
        if not tenant_id:
            raise ValueError("tenant_id must be captured from a trusted server boundary")
        self.store = store
        self.tenant_id = tenant_id
        self.profile = profile
        self.correlation_seed = correlation_seed
        self.clock = clock
        self.id_factory = id_factory

    @property
    def requires_trusted_verification(self) -> bool:
        """Whether the frozen server profile uses the fail-closed v0.4 gate."""

        return self.profile in STRICT_VERIFICATION_PROFILES

    def _start(self, spec_payload: object, event_sink: PhaseEventSink | None) -> _RunRecorder:
        correlation_nonce = self.id_factory()
        run = Run(
            run_id=self.id_factory(),
            tenant_id=self.tenant_id,
            correlation_id=(
                canonical_sha256({"seed": self.correlation_seed, "nonce": correlation_nonce})
                if self.correlation_seed is not None
                else correlation_nonce
            ),
            profile=self.profile,
            status=RunStatus.RUNNING,
            input_digest=canonical_sha256(spec_payload),
            revision=1,
            started_at=self.clock(),
        )
        _observe_run(run)
        recorder = _RunRecorder(run, clock=self.clock, event_sink=event_sink)
        recorder.emit("run", "running", "strict-run-kernel")
        return recorder

    def execute_task(
        self,
        spec: DerivationTaskSpec,
        *,
        spec_payload: object,
        engine: SymbolicEngine,
        verifier: Verifier | None,
        event_sink: PhaseEventSink | None = None,
    ) -> StrictTaskExecution:
        recorder = self._start(spec_payload, event_sink)
        result = TaskOrchestrator(
            spec,
            engine=engine,
            verifier=verifier,
            event_sink=recorder.emit,
            require_verification=self.requires_trusted_verification,
        ).run()
        provenance_by_entity, parents = _build_provenance(
            recorder.run,
            spec,
            tuple(recorder.records),
        )
        subject = (
            _bind_final_subject(
                run=recorder.run,
                nodes=provenance_by_entity,
                parents=parents,
                derived_expression=result.derived_expression,
            )
            if result.derived_expression
            else canonical_sha256({"kind": "missing-result", "run_id": recorder.run.run_id})
        )
        provenance = tuple(provenance_by_entity.values())
        evidence = _make_evidence(
            run=recorder.run,
            subject_digest=subject,
            outcome=_evidence_outcome(result),
            details=[
                {"kind": item.kind, "status": item.status, "detail": item.detail}
                for item in result.acceptance
            ],
            clock=self.clock,
            id_factory=self.id_factory,
        )
        provisional_status = (
            RunStatus.VERIFIED
            if evidence.outcome is EvidenceOutcome.PASS and result.derived_expression
            else RunStatus.REJECTED
            if result.derived_expression
            else RunStatus.FAILED
        )
        provisional = replace(
            recorder.run,
            status=provisional_status,
            final_subject_digest=subject if result.derived_expression else None,
            verification_evidence_id=evidence.evidence_id,
        )
        eligibility = evaluate_codegen_eligibility(
            run=provisional,
            provenance=provenance,
            evidence=evidence,
            tenant_id=self.tenant_id,
            subject_digest=subject,
            active_revision=1,
            required_policy=VERIFICATION_POLICY,
        )

        artifacts: tuple[ArtifactPayload, ...] = ()
        if eligibility.eligible and result.generated_code:
            pseudocode = _render_pseudocode(spec, result.derived_expression).encode("utf-8")
            code = result.generated_code.encode("utf-8")
            artifacts = (
                _artifact_payload(
                    run=provisional,
                    evidence=evidence,
                    content=pseudocode,
                    media_type="text/x-pseudocode; charset=utf-8",
                    clock=self.clock,
                ),
                _artifact_payload(
                    run=provisional,
                    evidence=evidence,
                    content=code,
                    media_type="text/x-python; charset=utf-8",
                    clock=self.clock,
                ),
            )
            for payload, producer in zip(
                artifacts,
                ("internal:render_pseudocode", "internal:generate_python_function"),
                strict=True,
            ):
                recorder.emit(
                    "artifact",
                    "materialized",
                    producer,
                    {"media_type": payload.artifact.media_type, "size": payload.artifact.size},
                )
            final_status = RunStatus.COMPLETED
            verification_status = "verified"
        else:
            # Failed verification never leaves this boundary with code.  The
            # historical legacy/full no-acceptance payload stays available, but
            # it is not promoted to a verification-bound immutable artifact.
            if result.generated_code and self.requires_trusted_verification:
                result = replace(result, generated_code="")
            legacy_unverified_codegen = (
                not self.requires_trusted_verification
                and not result.acceptance
                and bool(result.generated_code)
                and result.verified
            )
            final_status = RunStatus.COMPLETED if legacy_unverified_codegen else provisional_status
            verification_status = (
                "failed"
                if evidence.outcome is EvidenceOutcome.FAIL
                else "error"
                if evidence.outcome is EvidenceOutcome.ERROR
                else "not_checked"
                if evidence.outcome is EvidenceOutcome.INCONCLUSIVE
                else "blocked"
            )
        recorder.emit("run", final_status.value, "strict-run-kernel")
        # Rebuild once after materialization so persisted provenance also covers
        # artifact/final lifecycle events.  Eligibility above used the complete
        # pre-codegen chain; this only adds immutable descendants.
        final_nodes, final_parents = _build_provenance(
            recorder.run,
            spec,
            tuple(recorder.records),
        )
        if result.derived_expression:
            _bind_final_subject(
                run=recorder.run,
                nodes=final_nodes,
                parents=final_parents,
                derived_expression=result.derived_expression,
            )
        provenance = tuple(final_nodes.values())
        run = replace(
            provisional,
            status=final_status,
            completed_at=self.clock(),
            artifact_ids=tuple(payload.artifact.sha256 for payload in artifacts),
        )
        bundle = RunBundle(
            run=run,
            events=tuple(recorder.events),
            provenance=provenance,
            evidence=(evidence,),
            artifacts=artifacts,
        )
        stored_run = self.store.save_bundle(bundle)
        bundle = replace(bundle, run=stored_run)
        return StrictTaskExecution(
            result=result,
            bundle=bundle,
            resources=_resources(stored_run, artifacts),
            verification_status=verification_status,
        )

    def execute_explore(
        self,
        spec: DerivationTaskSpec,
        *,
        spec_payload: object,
        engine: SymbolicEngine,
        verifier: Verifier | None,
        event_sink: PhaseEventSink | None = None,
    ) -> StrictExploreExecution:
        recorder = self._start(spec_payload, event_sink)
        result = Explorer(
            spec,
            engine=engine,
            verifier=verifier,
            event_sink=recorder.emit,
            require_verification=self.requires_trusted_verification,
        ).explore()
        provenance, execution_parents = _build_provenance(
            recorder.run,
            spec,
            tuple(recorder.records),
        )
        evidence_items: list[VerificationEvidence] = []
        artifacts_by_sha: dict[str, ArtifactPayload] = {}
        best_evidence: VerificationEvidence | None = None
        for candidate in result.candidates:
            if not candidate.derived:
                continue
            subject = _bind_final_subject(
                run=recorder.run,
                nodes=provenance,
                parents=execution_parents,
                derived_expression=candidate.derived,
            )
            outcome = _explore_evidence_outcome(candidate)
            evidence = _make_evidence(
                run=recorder.run,
                subject_digest=subject,
                outcome=outcome,
                details={
                    "candidate": candidate.label,
                    "oracles_passed": candidate.oracles_passed,
                    "oracles_total": candidate.oracles_total,
                    "outcomes": [
                        {"kind": item.kind, "status": item.status, "detail": item.detail}
                        for item in candidate.acceptance
                    ],
                },
                clock=self.clock,
                id_factory=self.id_factory,
            )
            evidence_items.append(evidence)
            candidate_run = replace(
                recorder.run,
                status=RunStatus.VERIFIED
                if outcome is EvidenceOutcome.PASS
                else RunStatus.REJECTED,
                final_subject_digest=subject,
                verification_evidence_id=evidence.evidence_id,
            )
            eligibility = evaluate_codegen_eligibility(
                run=candidate_run,
                provenance=tuple(provenance.values()),
                evidence=evidence,
                tenant_id=self.tenant_id,
                subject_digest=subject,
                active_revision=1,
                required_policy=VERIFICATION_POLICY,
            )
            if eligibility.eligible and candidate.generated_code:
                for content, media_type in (
                    (
                        _render_pseudocode(spec, candidate.derived),
                        "text/x-pseudocode; charset=utf-8",
                    ),
                    (candidate.generated_code, "text/x-python; charset=utf-8"),
                ):
                    payload = _artifact_payload(
                        run=candidate_run,
                        evidence=evidence,
                        content=content.encode("utf-8"),
                        media_type=media_type,
                        clock=self.clock,
                    )
                    if payload.artifact.sha256 not in artifacts_by_sha:
                        artifacts_by_sha[payload.artifact.sha256] = payload
                        recorder.emit(
                            "artifact",
                            "materialized",
                            (
                                "internal:render_pseudocode"
                                if media_type.startswith("text/x-pseudocode")
                                else "internal:generate_python_function"
                            ),
                            {
                                "branch": candidate.label,
                                "media_type": payload.artifact.media_type,
                                "size": payload.artifact.size,
                            },
                        )
            if result.best is candidate:
                best_evidence = evidence

        best = result.best
        best_subject = (
            _entity_digest("expression/v1", best.derived)
            if best is not None and best.derived
            else None
        )
        verified = best_evidence is not None and best_evidence.outcome is EvidenceOutcome.PASS
        legacy_unverified = (
            not self.requires_trusted_verification
            and best_evidence is not None
            and best_evidence.outcome is EvidenceOutcome.INCONCLUSIVE
            and best is not None
            and bool(best.generated_code)
        )
        final_status = RunStatus.COMPLETED if verified or legacy_unverified else RunStatus.REJECTED
        recorder.emit("run", final_status.value, "strict-run-kernel")
        final_provenance, final_parents = _build_provenance(
            recorder.run,
            spec,
            tuple(recorder.records),
        )
        for candidate in result.candidates:
            if not candidate.derived:
                continue
            _bind_final_subject(
                run=recorder.run,
                nodes=final_provenance,
                parents=final_parents,
                derived_expression=candidate.derived,
            )
        provenance = final_provenance
        artifacts = tuple(artifacts_by_sha.values())
        run = replace(
            recorder.run,
            status=final_status,
            completed_at=self.clock(),
            final_subject_digest=best_subject,
            verification_evidence_id=best_evidence.evidence_id if best_evidence else None,
            artifact_ids=tuple(artifacts_by_sha),
        )
        bundle = RunBundle(
            run=run,
            events=tuple(recorder.events),
            provenance=tuple(provenance.values()),
            evidence=tuple(evidence_items),
            artifacts=artifacts,
        )
        stored_run = self.store.save_bundle(bundle)
        bundle = replace(bundle, run=stored_run)
        return StrictExploreExecution(
            result=result,
            bundle=bundle,
            resources=_resources(stored_run, artifacts),
            verification_status=(
                "verified" if verified else "not_checked" if legacy_unverified else "failed"
            ),
        )
