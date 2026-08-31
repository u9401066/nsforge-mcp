"""Fail-closed run/evidence/artifact kernel regression tests."""

from __future__ import annotations

import ast
from collections.abc import Callable
from itertools import count

import pytest

from nsforge.application.strict_run import (
    VERIFICATION_POLICY,
    StrictRunService,
    StrictTaskExecution,
    make_caller_assertion_evidence,
)
from nsforge.domain.strict_provenance import (
    ArtifactPayload,
    EvidenceOrigin,
    EvidenceOutcome,
    PhaseEvent,
    ProvenanceNode,
    RunStatus,
    VerificationEvidence,
    canonical_sha256,
    evaluate_codegen_eligibility,
)
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sqlite_run_store import SqliteRunStore
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier


def _ids(prefix: str = "id") -> Callable[[], str]:
    values = count(1)
    return lambda: f"{prefix}-{next(values)}"


def _clock() -> str:
    return "2026-08-31T00:00:00+00:00"


def _spec(
    *,
    expected: str | None = "x + 1",
    goal: str = "derive y",
) -> tuple[DerivationTaskSpec, dict[str, object]]:
    payload: dict[str, object] = {
        "name": "strict_identity",
        "goal": goal,
        "given": {"x": "scalar"},
        "unknowns": ["y"],
        "base_formulas": ["y = x + 1"],
    }
    if expected is not None:
        payload["acceptance"] = [{"kind": "equivalence", "params": {"reference": expected}}]
    return DerivationTaskSpec.from_dict(payload), payload


def _execute(
    store: SqliteRunStore,
    *,
    profile: str = "workflow",
    expected: str | None = "x + 1",
) -> StrictTaskExecution:
    spec, payload = _spec(expected=expected)
    service = StrictRunService(
        store,
        tenant_id="tenant-a",
        profile=profile,
        clock=_clock,
        id_factory=_ids(profile),
    )
    return service.execute_task(
        spec,
        spec_payload=payload,
        engine=SymPyEngine(),
        verifier=BasicVerifier(),
    )


def _ancestor_entities(subject: str, nodes: tuple[ProvenanceNode, ...]) -> set[str]:
    by_entity = {node.entity_digest: node for node in nodes}
    found: set[str] = set()

    def visit(entity: str) -> None:
        if entity in found:
            return
        found.add(entity)
        for parent in by_entity[entity].parent_digests:
            visit(parent)

    visit(subject)
    return found


def test_verified_run_persists_canonical_events_evidence_and_artifacts() -> None:
    store = SqliteRunStore(":memory:")
    execution = _execute(store)

    assert execution.result.generated_code.startswith("def strict_identity(")
    assert execution.bundle.run.status is RunStatus.COMPLETED
    assert execution.verification_status == "verified"
    assert len(execution.bundle.artifacts) == 2
    assert [event.sequence for event in execution.bundle.events] == list(
        range(1, len(execution.bundle.events) + 1)
    )
    assert execution.bundle.events[0].parent_digest == execution.bundle.run.input_digest
    for previous, current in zip(
        execution.bundle.events,
        execution.bundle.events[1:],
        strict=False,
    ):
        assert current.parent_digest == previous.event_digest

    snapshot = store.snapshot("tenant-a", execution.bundle.run.run_id)
    assert snapshot is not None
    assert snapshot["run"]["artifact_ids"] == list(execution.bundle.run.artifact_ids)  # type: ignore[index]
    for payload in execution.bundle.artifacts:
        stored = store.get_artifact("tenant-a", payload.artifact.sha256)
        assert stored is not None
        assert stored[1] == payload.content


def test_failed_verification_never_codegen_or_artifact() -> None:
    execution = _execute(SqliteRunStore(":memory:"), expected="x + 2")

    assert execution.result.verified is False
    assert execution.result.generated_code == ""
    assert execution.bundle.artifacts == ()
    assert execution.bundle.run.status is RunStatus.REJECTED
    assert execution.verification_status == "failed"


def test_verified_codegen_renders_goal_and_step_prose_only_as_data() -> None:
    spec, payload = _spec(goal="derive safely\n    injected = 7")
    execution = StrictRunService(
        SqliteRunStore(":memory:"),
        tenant_id="tenant-a",
        profile="workflow",
        clock=_clock,
        id_factory=_ids("safe-code"),
    ).execute_task(
        spec,
        spec_payload=payload,
        engine=SymPyEngine(),
        verifier=BasicVerifier(),
    )

    tree = ast.parse(execution.result.generated_code)
    assigned_names = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "injected" not in assigned_names
    assert execution.bundle.run.status is RunStatus.COMPLETED
    assert len(execution.bundle.artifacts) == 2


def test_strict_no_acceptance_blocks_but_legacy_payload_remains_compatible() -> None:
    strict = _execute(SqliteRunStore(":memory:"), profile="workflow", expected=None)
    legacy = _execute(SqliteRunStore(":memory:"), profile="legacy", expected=None)

    assert strict.result.generated_code == ""
    assert strict.bundle.run.status is RunStatus.REJECTED
    assert strict.verification_status == "not_checked"

    assert legacy.result.generated_code.startswith("def strict_identity(")
    assert legacy.bundle.run.status is RunStatus.COMPLETED
    assert legacy.verification_status == "not_checked"
    assert legacy.bundle.artifacts == ()


def test_final_lineage_traverses_every_persisted_execution_event() -> None:
    execution = _execute(SqliteRunStore(":memory:"))
    subject = execution.bundle.run.final_subject_digest
    assert subject is not None
    ancestors = _ancestor_entities(subject, execution.bundle.provenance)

    event_entities = {
        canonical_sha256({"kind": "phase-event-output/v1", "event_digest": event.event_digest})
        for event in execution.bundle.events
    }
    assert event_entities <= ancestors
    producers = {
        node.producer for node in execution.bundle.provenance if node.entity_digest in ancestors
    }
    assert {
        "engine.parse",
        "engine.simplify",
        "verify_equality",
        "internal:generate_python_function",
    } <= producers


def test_caller_assertion_wrong_tenant_and_stale_revision_cannot_unlock_codegen() -> None:
    execution = _execute(SqliteRunStore(":memory:"))
    run = execution.bundle.run
    subject = run.final_subject_digest
    assert subject is not None
    assertion = make_caller_assertion_evidence(
        run=run,
        subject_digest=subject,
        assertion={"verified": True},
        clock=_clock,
        id_factory=_ids("caller"),
    )
    rejected = evaluate_codegen_eligibility(
        run=run,
        provenance=execution.bundle.provenance,
        evidence=assertion,
        tenant_id="tenant-a",
        subject_digest=subject,
        active_revision=run.revision,
        required_policy=VERIFICATION_POLICY,
    )
    assert not rejected.eligible
    assert "caller assertion" in rejected.reason

    trusted = execution.bundle.evidence[0]
    wrong_tenant = evaluate_codegen_eligibility(
        run=run,
        provenance=execution.bundle.provenance,
        evidence=trusted,
        tenant_id="tenant-b",
        subject_digest=subject,
        active_revision=run.revision,
        required_policy=VERIFICATION_POLICY,
    )
    stale = evaluate_codegen_eligibility(
        run=run,
        provenance=execution.bundle.provenance,
        evidence=trusted,
        tenant_id="tenant-a",
        subject_digest=subject,
        active_revision=run.revision + 1,
        required_policy=VERIFICATION_POLICY,
    )
    assert not wrong_tenant.eligible
    assert not stale.eligible


def test_canonical_record_digests_cannot_be_caller_forged() -> None:
    with pytest.raises(ValueError, match="phase event digest"):
        PhaseEvent(
            run_id="run",
            tenant_id="tenant-a",
            sequence=1,
            phase="concept",
            status="ok",
            tool="task.validate",
            parent_digest="parent",
            payload_digest="payload",
            timestamp=_clock(),
            event_digest="forged",
        )

    with pytest.raises(ValueError, match="provenance node digest"):
        ProvenanceNode(
            run_id="run",
            tenant_id="tenant-a",
            entity_digest="entity",
            producer="engine.simplify",
            input_digest="input",
            output_digest="output",
            parent_digests=(),
            trusted=True,
            node_digest="forged",
        )

    with pytest.raises(ValueError, match="verification evidence digest"):
        VerificationEvidence(
            evidence_id="evidence",
            run_id="run",
            tenant_id="tenant-a",
            verifier="caller",
            subject_digest="subject",
            policy=VERIFICATION_POLICY,
            outcome=EvidenceOutcome.PASS,
            details_digest="details",
            created_revision=1,
            created_at=_clock(),
            origin=EvidenceOrigin.KERNEL,
            trusted=True,
            evidence_digest="forged",
        )

    execution = _execute(SqliteRunStore(":memory:"))
    artifact = execution.bundle.artifacts[0].artifact
    with pytest.raises(ValueError, match="artifact sha256"):
        ArtifactPayload(artifact=artifact, content=b"forged")


def test_strict_explore_persists_branch_lineage_and_only_verified_artifacts() -> None:
    payload: dict[str, object] = {
        "name": "strict-explore",
        "goal": "find a calibrated gain",
        "given": {"x": "scalar"},
        "unknowns": ["y"],
        "base_formulas": ["y = k*x"],
        "acceptance": [
            {"kind": "boundary", "params": {"variable": "x", "at": "1", "expected": "5"}}
        ],
        "alternatives": [
            {"id": "gain-2", "target": "k", "expression": "2"},
            {"id": "gain-5", "target": "k", "expression": "5"},
        ],
    }
    store = SqliteRunStore(":memory:")
    service = StrictRunService(
        store,
        tenant_id="tenant-a",
        profile="workflow",
        clock=_clock,
        id_factory=_ids("explore"),
    )
    execution = service.execute_explore(
        DerivationTaskSpec.from_dict(payload),
        spec_payload=payload,
        engine=SymPyEngine(),
        verifier=BasicVerifier(),
    )

    assert execution.bundle.run.status is RunStatus.COMPLETED
    assert execution.result.best is not None
    assert execution.result.best.label == "alternative:gain-5"
    assert len(execution.bundle.artifacts) == 2
    subjects = {
        canonical_sha256({"kind": "expression/v1", "value": candidate.derived})
        for candidate in execution.result.candidates
        if candidate.derived
    }
    all_ancestors: set[str] = set()
    for subject in subjects:
        all_ancestors.update(_ancestor_entities(subject, execution.bundle.provenance))
    event_entities = {
        canonical_sha256({"kind": "phase-event-output/v1", "event_digest": event.event_digest})
        for event in execution.bundle.events
    }
    assert event_entities <= all_ancestors


def test_strict_explore_failed_branches_never_emit_code() -> None:
    spec, payload = _spec(expected="x + 2")
    service = StrictRunService(
        SqliteRunStore(":memory:"),
        tenant_id="tenant-a",
        profile="workflow",
        clock=_clock,
        id_factory=_ids("failed-explore"),
    )
    execution = service.execute_explore(
        spec,
        spec_payload=payload,
        engine=SymPyEngine(),
        verifier=BasicVerifier(),
    )
    assert execution.bundle.run.status is RunStatus.REJECTED
    assert execution.bundle.artifacts == ()
    assert all(candidate.generated_code == "" for candidate in execution.result.candidates)
