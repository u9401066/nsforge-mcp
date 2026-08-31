"""SQLite UoW isolation, revision, rollback, and immutability tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from nsforge.domain.strict_provenance import (
    PhaseEvent,
    Run,
    RunBundle,
    RunStatus,
    canonical_sha256,
    phase_event_digest,
)
from nsforge.infrastructure.sqlite_run_store import (
    ImmutableStateError,
    RevisionConflict,
    SqliteRunStore,
)


def _draft(*, tenant: str = "tenant-a") -> Run:
    return Run(
        run_id="run-1",
        tenant_id=tenant,
        correlation_id="correlation-1",
        profile="workflow",
        status=RunStatus.RUNNING,
        input_digest=canonical_sha256({"input": 1}),
        revision=0,
        started_at="2026-08-31T00:00:00+00:00",
    )


def _event(run: Run, sequence: int, parent: str) -> PhaseEvent:
    payload = canonical_sha256({"sequence": sequence})
    timestamp = f"2026-08-31T00:00:0{sequence}+00:00"
    digest = phase_event_digest(
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        sequence=sequence,
        phase="run",
        status="running",
        tool="strict-run-kernel",
        parent_digest=parent,
        payload_digest=payload,
        timestamp=timestamp,
    )
    return PhaseEvent(
        run_id=run.run_id,
        tenant_id=run.tenant_id,
        sequence=sequence,
        phase="run",
        status="running",
        tool="strict-run-kernel",
        parent_digest=parent,
        payload_digest=payload,
        timestamp=timestamp,
        event_digest=digest,
    )


def test_unit_of_work_rolls_back_every_record_on_failure() -> None:
    store = SqliteRunStore(":memory:")
    with pytest.raises(RuntimeError, match="abort"), store.unit_of_work() as uow:
        uow.put_run(_draft(), expected_revision=0)
        raise RuntimeError("abort")
    assert store.get_run("tenant-a", "run-1") is None


def test_revision_conflict_and_immutable_identity_fail_closed() -> None:
    store = SqliteRunStore(":memory:")
    with store.unit_of_work() as uow:
        first = uow.put_run(_draft(), expected_revision=0)

    with pytest.raises(RevisionConflict), store.unit_of_work() as uow:
        uow.put_run(first, expected_revision=0)

    with pytest.raises(ImmutableStateError, match="identity"), store.unit_of_work() as uow:
        uow.put_run(replace(first, profile="legacy"), expected_revision=1)
    assert store.get_run("tenant-a", "run-1") == first


def test_terminal_bundle_replay_is_rejected_without_duplicate_rows() -> None:
    store = SqliteRunStore(":memory:")
    completed = replace(
        _draft(),
        status=RunStatus.COMPLETED,
        completed_at="2026-08-31T00:00:01+00:00",
    )
    stored = store.save_bundle(RunBundle(run=completed))
    with pytest.raises(ImmutableStateError, match="terminal run"):
        store.save_bundle(RunBundle(run=stored), expected_revision=1)
    assert store.get_run("tenant-a", "run-1") == stored


def test_nonterminal_revision_bundle_accepts_only_append_deltas() -> None:
    store = SqliteRunStore(":memory:")
    draft = _draft()
    first_event = _event(draft, 1, draft.input_digest)
    revision_one = store.save_bundle(RunBundle(run=draft, events=(first_event,)))
    second_event = _event(revision_one, 2, first_event.event_digest)
    revision_two = store.save_bundle(
        RunBundle(
            run=replace(revision_one, status=RunStatus.VERIFYING),
            events=(second_event,),
        ),
        expected_revision=1,
    )
    assert revision_two.revision == 2
    assert store.list_events("tenant-a", "run-1") == (first_event, second_event)

    with pytest.raises(ImmutableStateError, match="sequence"), store.unit_of_work() as uow:
        uow.put_run(replace(revision_two, status=RunStatus.VERIFIED), expected_revision=2)
        uow.add_event(first_event)
    assert store.get_run("tenant-a", "run-1") == revision_two
    assert store.list_events("tenant-a", "run-1") == (first_event, second_event)


def test_tenant_scope_never_falls_back_to_another_tenant() -> None:
    store = SqliteRunStore(":memory:")
    store.save_bundle(RunBundle(run=_draft()))
    assert store.get_run("tenant-b", "run-1") is None
    assert store.snapshot("tenant-b", "run-1") is None
