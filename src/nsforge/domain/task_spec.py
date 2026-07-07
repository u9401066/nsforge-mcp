"""
NSForge Derivation Task Spec (DTS) — L2 of the reification ladder.

A declarative, machine-readable description of a large derivation task, so that
any agent (Copilot / Cline / OpenHands / Hermes) can run it deterministically.
It turns a fuzzy prompt into a checkable job.

The fields map onto the reification ladder
(see docs/reification-ladder-direction.md):

    concept  -> name, goal
    symbols  -> given, unknowns, assumptions
    derive   -> base_formulas, modifications
    verify   -> acceptance

Pure domain: no I/O. Build one from a plain ``dict`` (e.g. parsed JSON) via
``DerivationTaskSpec.from_dict``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AcceptanceKind(str, Enum):
    """Kinds of acceptance oracle used to verify a derived result."""

    DIMENSIONAL = "dimensional"  # dimensional consistency
    BOUNDARY = "boundary"  # value at a boundary condition
    LIMIT = "limit"  # behaviour in a limit
    EQUIVALENCE = "equivalence"  # equals a known reference expression


@dataclass(frozen=True)
class Modification:
    """A named modification that may be composed onto a base formula."""

    id: str
    description: str = ""
    expression: str = ""  # optional symbolic term, e.g. "-mu*N"
    target: str = ""  # optional: the symbol this modification replaces (enables auto-substitution)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Modification:
        return cls(
            id=str(data["id"]),
            description=str(data.get("description", "")),
            expression=str(data.get("expression", "")),
            target=str(data.get("target", "")),
        )


@dataclass(frozen=True)
class AcceptanceCheck:
    """A single acceptance oracle (how the derived result is verified)."""

    kind: AcceptanceKind
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcceptanceCheck:
        return cls(
            kind=AcceptanceKind(str(data["kind"])),
            description=str(data.get("description", "")),
            params=dict(data.get("params", {})),
        )


@dataclass(frozen=True)
class DerivationTaskSpec:
    """Declarative spec for a derivation task (L2)."""

    name: str
    goal: str
    given: dict[str, str] = field(default_factory=dict)  # symbol -> unit/description
    unknowns: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)  # e.g. "k>0", "T>0"
    base_formulas: list[str] = field(default_factory=list)  # ids or expressions
    modifications: list[Modification] = field(default_factory=list)
    acceptance: list[AcceptanceCheck] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Return a list of problems; an empty list means the spec is coherent."""
        problems: list[str] = []
        if not self.name.strip():
            problems.append("spec.name is empty")
        if not self.goal.strip():
            problems.append("spec.goal is empty")
        if not self.unknowns:
            problems.append("spec.unknowns is empty (nothing to solve for)")
        if not self.base_formulas:
            problems.append("spec.base_formulas is empty (no starting point)")
        return problems

    @property
    def symbols(self) -> set[str]:
        """All symbol names referenced by the spec (given + unknowns)."""
        return set(self.given) | set(self.unknowns)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DerivationTaskSpec:
        return cls(
            name=str(data["name"]),
            goal=str(data["goal"]),
            given={str(k): str(v) for k, v in dict(data.get("given", {})).items()},
            unknowns=[str(u) for u in data.get("unknowns", [])],
            assumptions=[str(a) for a in data.get("assumptions", [])],
            base_formulas=[str(b) for b in data.get("base_formulas", [])],
            modifications=[Modification.from_dict(m) for m in data.get("modifications", [])],
            acceptance=[AcceptanceCheck.from_dict(a) for a in data.get("acceptance", [])],
            metadata=dict(data.get("metadata", {})),
        )
