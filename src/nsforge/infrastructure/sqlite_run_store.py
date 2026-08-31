"""SQLite revision store for strict NSForge runs.

The adapter owns all I/O.  One :meth:`unit_of_work` commits a run revision,
events, provenance nodes, verification evidence, and artifact metadata/bytes as
one transaction.  WAL and foreign keys are enabled for file-backed stores.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import cast

from nsforge.application.run_store import RunUnitOfWork
from nsforge.domain.strict_provenance import (
    TERMINAL_RUN_STATUSES,
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
    content_sha256,
)


class RevisionConflict(RuntimeError):
    """The caller tried to update a stale run revision."""


class ImmutableStateError(RuntimeError):
    """An append-only or terminal record would have been changed."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    profile TEXT NOT NULL,
    status TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    revision INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    final_subject_digest TEXT,
    verification_evidence_id TEXT,
    artifact_ids_json TEXT NOT NULL,
    superseded_by TEXT,
    PRIMARY KEY (tenant_id, run_id)
);

CREATE TABLE IF NOT EXISTS phase_events (
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    tool TEXT NOT NULL,
    parent_digest TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_digest TEXT NOT NULL,
    PRIMARY KEY (tenant_id, run_id, sequence),
    UNIQUE (tenant_id, run_id, event_digest),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);

CREATE TABLE IF NOT EXISTS provenance_nodes (
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    entity_digest TEXT NOT NULL,
    producer TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    output_digest TEXT NOT NULL,
    parent_digests_json TEXT NOT NULL,
    trusted INTEGER NOT NULL,
    node_digest TEXT NOT NULL,
    PRIMARY KEY (tenant_id, run_id, entity_digest),
    UNIQUE (tenant_id, run_id, node_digest),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);

CREATE TABLE IF NOT EXISTS verification_evidence (
    tenant_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    verifier TEXT NOT NULL,
    subject_digest TEXT NOT NULL,
    policy TEXT NOT NULL,
    outcome TEXT NOT NULL,
    details_digest TEXT NOT NULL,
    created_revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    origin TEXT NOT NULL,
    trusted INTEGER NOT NULL,
    evidence_digest TEXT NOT NULL,
    PRIMARY KEY (tenant_id, evidence_id),
    UNIQUE (tenant_id, evidence_digest),
    FOREIGN KEY (tenant_id, run_id) REFERENCES runs(tenant_id, run_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    tenant_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    media_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    content BLOB NOT NULL,
    PRIMARY KEY (tenant_id, sha256)
);

CREATE TABLE IF NOT EXISTS artifact_links (
    tenant_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    producer_run_id TEXT NOT NULL,
    verification_evidence_id TEXT NOT NULL,
    storage_locator TEXT NOT NULL,
    created_revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, sha256, producer_run_id),
    FOREIGN KEY (tenant_id, sha256) REFERENCES artifacts(tenant_id, sha256),
    FOREIGN KEY (tenant_id, producer_run_id) REFERENCES runs(tenant_id, run_id),
    FOREIGN KEY (tenant_id, verification_evidence_id)
        REFERENCES verification_evidence(tenant_id, evidence_id)
);
"""


def _run_from_row(row: sqlite3.Row) -> Run:
    return Run(
        run_id=str(row["run_id"]),
        tenant_id=str(row["tenant_id"]),
        correlation_id=str(row["correlation_id"]),
        profile=str(row["profile"]),
        status=RunStatus(str(row["status"])),
        input_digest=str(row["input_digest"]),
        revision=int(row["revision"]),
        started_at=str(row["started_at"]),
        completed_at=cast("str | None", row["completed_at"]),
        final_subject_digest=cast("str | None", row["final_subject_digest"]),
        verification_evidence_id=cast("str | None", row["verification_evidence_id"]),
        artifact_ids=tuple(json.loads(str(row["artifact_ids_json"]))),
        superseded_by=cast("str | None", row["superseded_by"]),
    )


def _event_from_row(row: sqlite3.Row) -> PhaseEvent:
    return PhaseEvent(
        run_id=str(row["run_id"]),
        tenant_id=str(row["tenant_id"]),
        sequence=int(row["sequence"]),
        phase=str(row["phase"]),
        status=str(row["status"]),
        tool=str(row["tool"]),
        parent_digest=str(row["parent_digest"]),
        payload_digest=str(row["payload_digest"]),
        timestamp=str(row["timestamp"]),
        event_digest=str(row["event_digest"]),
    )


def _node_from_row(row: sqlite3.Row) -> ProvenanceNode:
    return ProvenanceNode(
        run_id=str(row["run_id"]),
        tenant_id=str(row["tenant_id"]),
        entity_digest=str(row["entity_digest"]),
        producer=str(row["producer"]),
        input_digest=str(row["input_digest"]),
        output_digest=str(row["output_digest"]),
        parent_digests=tuple(json.loads(str(row["parent_digests_json"]))),
        trusted=bool(row["trusted"]),
        node_digest=str(row["node_digest"]),
    )


def _evidence_from_row(row: sqlite3.Row) -> VerificationEvidence:
    return VerificationEvidence(
        evidence_id=str(row["evidence_id"]),
        run_id=str(row["run_id"]),
        tenant_id=str(row["tenant_id"]),
        verifier=str(row["verifier"]),
        subject_digest=str(row["subject_digest"]),
        policy=str(row["policy"]),
        outcome=EvidenceOutcome(str(row["outcome"])),
        details_digest=str(row["details_digest"]),
        created_revision=int(row["created_revision"]),
        created_at=str(row["created_at"]),
        origin=EvidenceOrigin(str(row["origin"])),
        trusted=bool(row["trusted"]),
        evidence_digest=str(row["evidence_digest"]),
    )


class SqliteRunUnitOfWork:
    """Concrete mutation object; construction is owned by :class:`SqliteRunStore`."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def _run_row(self, tenant_id: str, run_id: str) -> sqlite3.Row:
        row = self._connection.execute(
            "SELECT * FROM runs WHERE tenant_id = ? AND run_id = ?",
            (tenant_id, run_id),
        ).fetchone()
        if row is None:
            raise ImmutableStateError("record is outside a persisted run scope")
        return cast("sqlite3.Row", row)

    def put_run(self, run: Run, *, expected_revision: int) -> Run:
        row = self._connection.execute(
            "SELECT * FROM runs WHERE tenant_id = ? AND run_id = ?",
            (run.tenant_id, run.run_id),
        ).fetchone()
        revision = expected_revision + 1
        stored = replace(run, revision=revision)
        values = (
            stored.correlation_id,
            stored.profile,
            stored.status.value,
            stored.input_digest,
            stored.revision,
            stored.started_at,
            stored.completed_at,
            stored.final_subject_digest,
            stored.verification_evidence_id,
            json.dumps(list(stored.artifact_ids), separators=(",", ":")),
            stored.superseded_by,
            stored.tenant_id,
            stored.run_id,
        )
        if row is None:
            if expected_revision != 0:
                raise RevisionConflict(
                    f"run {run.run_id!r} does not exist at revision {expected_revision}"
                )
            self._connection.execute(
                """
                INSERT INTO runs (
                    correlation_id, profile, status, input_digest, revision,
                    started_at, completed_at, final_subject_digest,
                    verification_evidence_id, artifact_ids_json, superseded_by,
                    tenant_id, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            return stored

        current = _run_from_row(row)
        if current.revision != expected_revision:
            raise RevisionConflict(
                f"run {run.run_id!r} revision {current.revision} != expected {expected_revision}"
            )
        if current.status in TERMINAL_RUN_STATUSES:
            raise ImmutableStateError(
                f"terminal run {run.run_id!r} at revision {current.revision} is immutable"
            )
        if (
            run.correlation_id != current.correlation_id
            or run.profile != current.profile
            or run.input_digest != current.input_digest
            or run.started_at != current.started_at
        ):
            raise ImmutableStateError("immutable run identity fields cannot change")
        self._connection.execute(
            """
            UPDATE runs SET
                correlation_id = ?, profile = ?, status = ?, input_digest = ?, revision = ?,
                started_at = ?, completed_at = ?, final_subject_digest = ?,
                verification_evidence_id = ?, artifact_ids_json = ?, superseded_by = ?
            WHERE tenant_id = ? AND run_id = ?
            """,
            values,
        )
        return stored

    def add_event(self, event: PhaseEvent) -> None:
        self._run_row(event.tenant_id, event.run_id)
        previous = self._connection.execute(
            """
            SELECT event_digest FROM phase_events
            WHERE tenant_id = ? AND run_id = ?
            ORDER BY sequence DESC LIMIT 1
            """,
            (event.tenant_id, event.run_id),
        ).fetchone()
        if previous is None:
            run_row = self._connection.execute(
                "SELECT input_digest FROM runs WHERE tenant_id = ? AND run_id = ?",
                (event.tenant_id, event.run_id),
            ).fetchone()
            expected_sequence = 1
            expected_parent = str(run_row["input_digest"]) if run_row is not None else ""
        else:
            count_row = self._connection.execute(
                "SELECT MAX(sequence) AS last_sequence FROM phase_events WHERE tenant_id = ? AND run_id = ?",
                (event.tenant_id, event.run_id),
            ).fetchone()
            expected_sequence = int(count_row["last_sequence"]) + 1
            expected_parent = str(previous["event_digest"])
        if event.sequence != expected_sequence or event.parent_digest != expected_parent:
            raise ImmutableStateError("phase event sequence or digest lineage is not monotonic")
        self._connection.execute(
            """
            INSERT INTO phase_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.tenant_id,
                event.run_id,
                event.sequence,
                event.phase,
                event.status,
                event.tool,
                event.parent_digest,
                event.payload_digest,
                event.timestamp,
                event.event_digest,
            ),
        )

    def add_provenance(self, node: ProvenanceNode) -> None:
        self._run_row(node.tenant_id, node.run_id)
        for parent in node.parent_digests:
            parent_row = self._connection.execute(
                """
                SELECT 1 FROM provenance_nodes
                WHERE tenant_id = ? AND run_id = ? AND entity_digest = ?
                """,
                (node.tenant_id, node.run_id, parent),
            ).fetchone()
            if parent_row is None:
                raise ImmutableStateError("provenance parent is outside the persisted run DAG")
        self._connection.execute(
            """
            INSERT INTO provenance_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.tenant_id,
                node.run_id,
                node.entity_digest,
                node.producer,
                node.input_digest,
                node.output_digest,
                json.dumps(list(node.parent_digests), separators=(",", ":")),
                int(node.trusted),
                node.node_digest,
            ),
        )

    def add_evidence(self, evidence: VerificationEvidence) -> None:
        run = _run_from_row(self._run_row(evidence.tenant_id, evidence.run_id))
        if evidence.created_revision != run.revision:
            raise ImmutableStateError("verification evidence revision is outside the active run")
        self._connection.execute(
            """
            INSERT INTO verification_evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence.tenant_id,
                evidence.evidence_id,
                evidence.run_id,
                evidence.verifier,
                evidence.subject_digest,
                evidence.policy,
                evidence.outcome.value,
                evidence.details_digest,
                evidence.created_revision,
                evidence.created_at,
                evidence.origin.value,
                int(evidence.trusted),
                evidence.evidence_digest,
            ),
        )

    def add_artifact(self, payload: ArtifactPayload) -> None:
        artifact = payload.artifact
        run = _run_from_row(self._run_row(artifact.tenant_id, artifact.producer_run_id))
        if artifact.created_revision != run.revision or artifact.sha256 not in run.artifact_ids:
            raise ImmutableStateError("artifact is outside the active run revision")
        evidence = self._connection.execute(
            """
            SELECT run_id, created_revision FROM verification_evidence
            WHERE tenant_id = ? AND evidence_id = ?
            """,
            (artifact.tenant_id, artifact.verification_evidence_id),
        ).fetchone()
        if (
            evidence is None
            or str(evidence["run_id"]) != artifact.producer_run_id
            or int(evidence["created_revision"]) != artifact.created_revision
        ):
            raise ImmutableStateError("artifact lacks same-run, current verification evidence")
        if content_sha256(payload.content) != artifact.sha256:
            raise ImmutableStateError("artifact bytes do not match their content address")
        existing = self._connection.execute(
            "SELECT media_type, size, content FROM artifacts WHERE tenant_id = ? AND sha256 = ?",
            (artifact.tenant_id, artifact.sha256),
        ).fetchone()
        if existing is None:
            self._connection.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
                (
                    artifact.tenant_id,
                    artifact.sha256,
                    artifact.media_type,
                    artifact.size,
                    payload.content,
                ),
            )
        elif (
            str(existing["media_type"]) != artifact.media_type
            or int(existing["size"]) != artifact.size
            or bytes(existing["content"]) != payload.content
        ):
            raise ImmutableStateError("content-addressed artifact is immutable")
        self._connection.execute(
            """
            INSERT INTO artifact_links VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact.tenant_id,
                artifact.sha256,
                artifact.producer_run_id,
                artifact.verification_evidence_id,
                artifact.storage_locator,
                artifact.created_revision,
                artifact.created_at,
            ),
        )


class SqliteRunStore:
    """Thread-safe SQLite implementation of the strict run-store port."""

    def __init__(self, path: str | Path = "data/nsforge-strict.sqlite3") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.executescript(_SCHEMA)

    @contextmanager
    def unit_of_work(self) -> Iterator[RunUnitOfWork]:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                yield SqliteRunUnitOfWork(self._connection)
            except BaseException:
                self._connection.rollback()
                raise
            else:
                self._connection.commit()

    def save_bundle(self, bundle: RunBundle, *, expected_revision: int = 0) -> Run:
        """Atomically save an initial bundle or append-only revision delta.

        For ``expected_revision > 0``, collection fields are deltas: callers must
        provide only new events/nodes/evidence/artifacts.  Replaying an old row is
        rejected by immutable primary keys and the whole transaction rolls back.
        """

        with self.unit_of_work() as uow:
            stored = uow.put_run(bundle.run, expected_revision=expected_revision)
            for event in bundle.events:
                uow.add_event(event)
            for node in bundle.provenance:
                uow.add_provenance(node)
            for evidence in bundle.evidence:
                uow.add_evidence(evidence)
            for artifact in bundle.artifacts:
                uow.add_artifact(artifact)
        return stored

    def get_run(self, tenant_id: str, run_id: str) -> Run | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM runs WHERE tenant_id = ? AND run_id = ?",
                (tenant_id, run_id),
            ).fetchone()
            return _run_from_row(row) if row is not None else None

    def list_events(self, tenant_id: str, run_id: str) -> tuple[PhaseEvent, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT * FROM phase_events WHERE tenant_id = ? AND run_id = ?
                ORDER BY sequence
                """,
                (tenant_id, run_id),
            ).fetchall()
            return tuple(_event_from_row(row) for row in rows)

    def list_provenance(self, tenant_id: str, run_id: str) -> tuple[ProvenanceNode, ...]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM provenance_nodes WHERE tenant_id = ? AND run_id = ?",
                (tenant_id, run_id),
            ).fetchall()
            return tuple(_node_from_row(row) for row in rows)

    def list_evidence(self, tenant_id: str, run_id: str) -> tuple[VerificationEvidence, ...]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM verification_evidence WHERE tenant_id = ? AND run_id = ?",
                (tenant_id, run_id),
            ).fetchall()
            return tuple(_evidence_from_row(row) for row in rows)

    def _artifact_from_rows(self, base: sqlite3.Row, link: sqlite3.Row) -> Artifact:
        return Artifact(
            sha256=str(base["sha256"]),
            tenant_id=str(base["tenant_id"]),
            media_type=str(base["media_type"]),
            size=int(base["size"]),
            producer_run_id=str(link["producer_run_id"]),
            verification_evidence_id=str(link["verification_evidence_id"]),
            storage_locator=str(link["storage_locator"]),
            created_revision=int(link["created_revision"]),
            created_at=str(link["created_at"]),
        )

    def get_artifact(self, tenant_id: str, sha256: str) -> tuple[Artifact, bytes] | None:
        with self._lock:
            base = self._connection.execute(
                "SELECT * FROM artifacts WHERE tenant_id = ? AND sha256 = ?",
                (tenant_id, sha256),
            ).fetchone()
            if base is None:
                return None
            link = self._connection.execute(
                """
                SELECT * FROM artifact_links WHERE tenant_id = ? AND sha256 = ?
                ORDER BY created_at, producer_run_id LIMIT 1
                """,
                (tenant_id, sha256),
            ).fetchone()
            if link is None:  # pragma: no cover - forbidden by the unit of work
                return None
            return self._artifact_from_rows(base, link), bytes(base["content"])

    def _artifacts_for_run(self, tenant_id: str, run_id: str) -> tuple[Artifact, ...]:
        rows = self._connection.execute(
            """
            SELECT a.*, l.producer_run_id, l.verification_evidence_id,
                   l.storage_locator, l.created_revision, l.created_at
            FROM artifacts AS a
            JOIN artifact_links AS l
              ON l.tenant_id = a.tenant_id AND l.sha256 = a.sha256
            WHERE l.tenant_id = ? AND l.producer_run_id = ?
            ORDER BY a.sha256
            """,
            (tenant_id, run_id),
        ).fetchall()
        return tuple(self._artifact_from_rows(row, row) for row in rows)

    def snapshot(self, tenant_id: str, run_id: str) -> dict[str, object] | None:
        with self._lock:
            run = self.get_run(tenant_id, run_id)
            if run is None:
                return None
            return {
                "run": run.to_dict(),
                "provenance": [node.to_dict() for node in self.list_provenance(tenant_id, run_id)],
                "verification_evidence": [
                    item.to_dict() for item in self.list_evidence(tenant_id, run_id)
                ],
                "artifacts": [
                    artifact.to_dict() for artifact in self._artifacts_for_run(tenant_id, run_id)
                ],
                "resources": {
                    "run": f"nsforge://runs/{run_id}",
                    "events": f"nsforge://runs/{run_id}/events",
                },
            }

    def close(self) -> None:
        with self._lock:
            self._connection.close()


_default_stores: dict[str, SqliteRunStore] = {}
_default_lock = threading.Lock()


def default_tenant_id() -> str:
    """Resolve the instance trust boundary; never accept this from a tool argument."""

    return os.environ.get("NSFORGE_TENANT_ID", "local").strip() or "local"


def default_run_store_path() -> str:
    """Capture the configured database path at the server boundary."""

    return os.environ.get("NSFORGE_RUN_DB", "data/nsforge-strict.sqlite3").strip() or (
        "data/nsforge-strict.sqlite3"
    )


def get_run_store(path: str | Path | None = None) -> SqliteRunStore:
    """Return one store per configured database path in this process."""

    resolved = str(path) if path is not None else default_run_store_path()
    resolved = resolved or "data/nsforge-strict.sqlite3"
    store = _default_stores.get(resolved)
    if store is None:
        with _default_lock:
            store = _default_stores.get(resolved)
            if store is None:
                store = SqliteRunStore(resolved)
                _default_stores[resolved] = store
    return store
