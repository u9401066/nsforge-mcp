"""
Explore mode (roadmap phase 6) — branching derivation search.

Where the orchestrator's self-correction stops at the first alternative that
passes acceptance, explore mode runs EVERY branch (the base plus each
alternative) through the full reification loop and returns all the candidates —
each with its own acceptance result and provenance ledger — ranked best-first.
This turns "derive one answer" into "discover the space of verified answers".

Application layer: composes the L3 ``TaskOrchestrator`` over a branch set.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.services import SymbolicEngine, Verifier
from nsforge.domain.task_spec import DerivationTaskSpec


@dataclass(frozen=True)
class ExploreCandidate:
    """One explored branch and how well it turned out."""

    label: str  # "base" or "alternative:<id>"
    derived: str
    verified: bool
    provenance_complete: bool
    oracles_passed: int
    oracles_total: int
    generated_code: str = ""


@dataclass(frozen=True)
class ExploreResult:
    """All explored branches, ranked best-first."""

    concept: str
    candidates: tuple[ExploreCandidate, ...] = field(default_factory=tuple)

    @property
    def best(self) -> ExploreCandidate | None:
        return self.candidates[0] if self.candidates else None


@dataclass
class Explorer:
    """Runs a branching derivation search over a ``DerivationTaskSpec``."""

    spec: DerivationTaskSpec
    engine: SymbolicEngine
    verifier: Verifier | None = None

    def explore(self) -> ExploreResult:
        candidates: list[ExploreCandidate] = []
        for label, branch in self._branches():
            result = TaskOrchestrator(branch, engine=self.engine, verifier=self.verifier).run()
            passed = sum(1 for o in result.acceptance if o.status == "verified")
            candidates.append(
                ExploreCandidate(
                    label=label,
                    derived=result.derived_expression,
                    verified=result.verified,
                    provenance_complete=result.provenance.is_complete,
                    oracles_passed=passed,
                    oracles_total=len(result.acceptance),
                    generated_code=result.generated_code,
                )
            )
        # Rank: verified first, then more oracles passed, then simpler (shorter) result.
        candidates.sort(key=lambda c: (c.verified, c.oracles_passed, -len(c.derived)), reverse=True)
        return ExploreResult(concept=self.spec.goal, candidates=tuple(candidates))

    def _branches(self) -> list[tuple[str, DerivationTaskSpec]]:
        """The base derivation plus one branch per alternative (folded into mods)."""
        branches: list[tuple[str, DerivationTaskSpec]] = [
            ("base", replace(self.spec, alternatives=[]))
        ]
        for alt in self.spec.alternatives:
            branch = replace(
                self.spec, alternatives=[], modifications=[*self.spec.modifications, alt]
            )
            branches.append((f"alternative:{alt.id}", branch))
        return branches
