"""Application ports for the strict run revision store."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager
from typing import Protocol

from nsforge.domain.strict_provenance import (
    Artifact,
    ArtifactPayload,
    PhaseEvent,
    ProvenanceNode,
    Run,
    RunBundle,
    VerificationEvidence,
)


class RunUnitOfWork(Protocol):
    """Mutation surface exposed inside one atomic store transaction."""

    def put_run(self, run: Run, *, expected_revision: int) -> Run: ...

    def add_event(self, event: PhaseEvent) -> None: ...

    def add_provenance(self, node: ProvenanceNode) -> None: ...

    def add_evidence(self, evidence: VerificationEvidence) -> None: ...

    def add_artifact(self, payload: ArtifactPayload) -> None: ...


class RunStore(Protocol):
    """Tenant-scoped persistence port used by the strict application kernel."""

    def unit_of_work(self) -> AbstractContextManager[RunUnitOfWork]: ...

    def save_bundle(self, bundle: RunBundle, *, expected_revision: int = 0) -> Run: ...

    def get_run(self, tenant_id: str, run_id: str) -> Run | None: ...

    def list_events(self, tenant_id: str, run_id: str) -> tuple[PhaseEvent, ...]: ...

    def list_provenance(self, tenant_id: str, run_id: str) -> tuple[ProvenanceNode, ...]: ...

    def list_evidence(self, tenant_id: str, run_id: str) -> tuple[VerificationEvidence, ...]: ...

    def get_artifact(self, tenant_id: str, sha256: str) -> tuple[Artifact, bytes] | None: ...

    def snapshot(self, tenant_id: str, run_id: str) -> dict[str, object] | None: ...


def iter_artifacts(bundle: RunBundle) -> Iterator[Artifact]:
    """Yield metadata without leaking artifact bytes to generic serializers."""

    for payload in bundle.artifacts:
        yield payload.artifact
