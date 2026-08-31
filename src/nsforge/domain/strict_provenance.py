"""Immutable trust records for the strict NSForge workflow.

This module is deliberately pure: it defines canonical hashes, the append-only
records written by the application kernel, and the code-generation policy.  It
does not know about SQLite, MCP, clocks, or process-global state.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _json_default(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    raise TypeError(f"{type(value).__name__} is not canonically serializable")


def canonical_json(value: object) -> str:
    """Serialize a JSON-compatible value in one stable, hashable form."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=_json_default,
    )


def canonical_sha256(value: object) -> str:
    """Return the SHA-256 digest of :func:`canonical_json`."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def content_sha256(content: bytes) -> str:
    """Return the content-addressed id of immutable artifact bytes."""

    return hashlib.sha256(content).hexdigest()


class RunStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MATERIALIZED = "materialized"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


TERMINAL_RUN_STATUSES = frozenset(
    {RunStatus.COMPLETED, RunStatus.CANCELLED, RunStatus.FAILED, RunStatus.REJECTED}
)


class EvidenceOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"
    ASSERTED = "asserted"


class EvidenceOrigin(str, Enum):
    KERNEL = "kernel"
    CALLER_ASSERTION = "caller-assertion"


@dataclass(frozen=True, slots=True)
class Run:
    run_id: str
    tenant_id: str
    correlation_id: str
    profile: str
    status: RunStatus
    input_digest: str
    revision: int
    started_at: str
    completed_at: str | None = None
    final_subject_digest: str | None = None
    verification_evidence_id: str | None = None
    artifact_ids: tuple[str, ...] = field(default_factory=tuple)
    superseded_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id,
            "profile": self.profile,
            "status": self.status.value,
            "input_digest": self.input_digest,
            "revision": self.revision,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "final_subject_digest": self.final_subject_digest,
            "verification_evidence_id": self.verification_evidence_id,
            "artifact_ids": list(self.artifact_ids),
            "superseded_by": self.superseded_by,
        }


@dataclass(frozen=True, slots=True)
class PhaseEvent:
    run_id: str
    tenant_id: str
    sequence: int
    phase: str
    status: str
    tool: str
    parent_digest: str
    payload_digest: str
    timestamp: str
    event_digest: str

    def __post_init__(self) -> None:
        if self.event_digest != phase_event_digest(
            run_id=self.run_id,
            tenant_id=self.tenant_id,
            sequence=self.sequence,
            phase=self.phase,
            status=self.status,
            tool=self.tool,
            parent_digest=self.parent_digest,
            payload_digest=self.payload_digest,
            timestamp=self.timestamp,
        ):
            raise ValueError("phase event digest is not canonical")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True, slots=True)
class ProvenanceNode:
    run_id: str
    tenant_id: str
    entity_digest: str
    producer: str
    input_digest: str
    output_digest: str
    parent_digests: tuple[str, ...]
    trusted: bool
    node_digest: str

    def __post_init__(self) -> None:
        if self.node_digest != provenance_node_digest(
            run_id=self.run_id,
            tenant_id=self.tenant_id,
            entity_digest=self.entity_digest,
            producer=self.producer,
            input_digest=self.input_digest,
            output_digest=self.output_digest,
            parent_digests=self.parent_digests,
            trusted=self.trusted,
        ):
            raise ValueError("provenance node digest is not canonical")

    def to_dict(self) -> dict[str, Any]:
        value = dataclasses.asdict(self)
        value["parent_digests"] = list(self.parent_digests)
        return value


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    evidence_id: str
    run_id: str
    tenant_id: str
    verifier: str
    subject_digest: str
    policy: str
    outcome: EvidenceOutcome
    details_digest: str
    created_revision: int
    created_at: str
    origin: EvidenceOrigin
    trusted: bool
    evidence_digest: str

    def __post_init__(self) -> None:
        if self.evidence_digest != verification_evidence_digest(
            evidence_id=self.evidence_id,
            run_id=self.run_id,
            tenant_id=self.tenant_id,
            verifier=self.verifier,
            subject_digest=self.subject_digest,
            policy=self.policy,
            outcome=self.outcome,
            details_digest=self.details_digest,
            created_revision=self.created_revision,
            created_at=self.created_at,
            origin=self.origin,
            trusted=self.trusted,
        ):
            raise ValueError("verification evidence digest is not canonical")

    def to_dict(self) -> dict[str, Any]:
        value = dataclasses.asdict(self)
        value["outcome"] = self.outcome.value
        value["origin"] = self.origin.value
        return value


@dataclass(frozen=True, slots=True)
class Artifact:
    sha256: str
    tenant_id: str
    media_type: str
    size: int
    producer_run_id: str
    verification_evidence_id: str
    storage_locator: str
    created_revision: int
    created_at: str

    def __post_init__(self) -> None:
        if len(self.sha256) != 64 or any(char not in "0123456789abcdef" for char in self.sha256):
            raise ValueError("artifact sha256 must be a lowercase SHA-256 digest")
        if self.storage_locator != f"nsforge://artifacts/{self.sha256}":
            raise ValueError("artifact storage locator must match its content address")
        if self.size < 0 or self.created_revision < 1:
            raise ValueError("artifact size/revision is invalid")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True, slots=True)
class ArtifactPayload:
    artifact: Artifact
    content: bytes

    def __post_init__(self) -> None:
        if content_sha256(self.content) != self.artifact.sha256:
            raise ValueError("artifact sha256 does not match its immutable bytes")
        if len(self.content) != self.artifact.size:
            raise ValueError("artifact size does not match its immutable bytes")


@dataclass(frozen=True, slots=True)
class RunBundle:
    run: Run
    events: tuple[PhaseEvent, ...] = field(default_factory=tuple)
    provenance: tuple[ProvenanceNode, ...] = field(default_factory=tuple)
    evidence: tuple[VerificationEvidence, ...] = field(default_factory=tuple)
    artifacts: tuple[ArtifactPayload, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CodegenEligibility:
    eligible: bool
    reason: str


def phase_event_digest(
    *,
    run_id: str,
    tenant_id: str,
    sequence: int,
    phase: str,
    status: str,
    tool: str,
    parent_digest: str,
    payload_digest: str,
    timestamp: str,
) -> str:
    return canonical_sha256(
        {
            "kind": "phase-event/v1",
            "run_id": run_id,
            "tenant_id": tenant_id,
            "sequence": sequence,
            "phase": phase,
            "status": status,
            "tool": tool,
            "parent_digest": parent_digest,
            "payload_digest": payload_digest,
            "timestamp": timestamp,
        }
    )


def provenance_node_digest(
    *,
    run_id: str,
    tenant_id: str,
    entity_digest: str,
    producer: str,
    input_digest: str,
    output_digest: str,
    parent_digests: tuple[str, ...],
    trusted: bool,
) -> str:
    return canonical_sha256(
        {
            "kind": "provenance-node/v1",
            "run_id": run_id,
            "tenant_id": tenant_id,
            "entity_digest": entity_digest,
            "producer": producer,
            "input_digest": input_digest,
            "output_digest": output_digest,
            "parent_digests": list(parent_digests),
            "trusted": trusted,
        }
    )


def verification_evidence_digest(
    *,
    evidence_id: str,
    run_id: str,
    tenant_id: str,
    verifier: str,
    subject_digest: str,
    policy: str,
    outcome: EvidenceOutcome,
    details_digest: str,
    created_revision: int,
    created_at: str,
    origin: EvidenceOrigin,
    trusted: bool,
) -> str:
    return canonical_sha256(
        {
            "kind": "verification-evidence/v1",
            "evidence_id": evidence_id,
            "run_id": run_id,
            "tenant_id": tenant_id,
            "verifier": verifier,
            "subject_digest": subject_digest,
            "policy": policy,
            "outcome": outcome.value,
            "details_digest": details_digest,
            "created_revision": created_revision,
            "created_at": created_at,
            "origin": origin.value,
            "trusted": trusted,
        }
    )


def _has_complete_provenance(
    subject_digest: str,
    nodes: tuple[ProvenanceNode, ...],
) -> bool:
    by_entity = {node.entity_digest: node for node in nodes}
    visiting: set[str] = set()
    complete: set[str] = set()

    def visit(digest: str) -> bool:
        if digest in complete:
            return True
        if digest in visiting:
            return False
        node = by_entity.get(digest)
        if node is None:
            return False
        visiting.add(digest)
        if not node.parent_digests:
            valid = node.producer.startswith("input:") and not node.trusted
        else:
            valid = (
                node.trusted
                and not node.producer.startswith("caller:")
                and all(visit(parent) for parent in node.parent_digests)
            )
        visiting.remove(digest)
        if valid:
            complete.add(digest)
        return valid

    return visit(subject_digest)


def evaluate_codegen_eligibility(
    *,
    run: Run,
    provenance: tuple[ProvenanceNode, ...],
    evidence: VerificationEvidence | None,
    tenant_id: str,
    subject_digest: str,
    active_revision: int,
    required_policy: str,
) -> CodegenEligibility:
    """Evaluate the strict, fail-closed code-generation trust boundary."""

    if run.tenant_id != tenant_id:
        return CodegenEligibility(False, "wrong tenant")
    if run.status in {RunStatus.CANCELLED, RunStatus.FAILED, RunStatus.REJECTED}:
        return CodegenEligibility(False, f"run status is {run.status.value}")
    if run.superseded_by:
        return CodegenEligibility(False, "run revision was superseded")
    if run.revision != active_revision:
        return CodegenEligibility(False, "run revision is stale")
    if run.final_subject_digest != subject_digest:
        return CodegenEligibility(False, "final subject digest mismatch")
    if evidence is None:
        return CodegenEligibility(False, "trusted verification evidence is missing")
    if evidence.tenant_id != tenant_id or evidence.run_id != run.run_id:
        return CodegenEligibility(False, "verification evidence is outside the run scope")
    if evidence.subject_digest != subject_digest:
        return CodegenEligibility(False, "verification subject digest mismatch")
    if evidence.created_revision != active_revision:
        return CodegenEligibility(False, "verification evidence is stale")
    if evidence.policy != required_policy:
        return CodegenEligibility(False, "verification policy mismatch")
    if evidence.origin is not EvidenceOrigin.KERNEL or not evidence.trusted:
        return CodegenEligibility(False, "caller assertion is not trusted evidence")
    if evidence.outcome is not EvidenceOutcome.PASS:
        return CodegenEligibility(False, f"verification outcome is {evidence.outcome.value}")
    if not _has_complete_provenance(subject_digest, provenance):
        return CodegenEligibility(False, "provenance DAG is incomplete or untrusted")
    return CodegenEligibility(True, "trusted verification and provenance are complete")
