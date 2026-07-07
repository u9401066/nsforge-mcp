"""
NSForge Task Orchestrator (L3 skeleton) — drives the reification ladder.

Turns a declarative ``DerivationTaskSpec`` (L2) into an ordered, provenance-tagged
plan of tool calls, and executes the phases it can do deterministically
(concept validation, symbol registry). The symbolic-execution rungs are reified
into a plan whose steps each name the tool that would produce them — the
"birth certificate" (provenance) required by the north star. Wiring those steps
to the real derivation engine / sympy-mcp is the extension point.

Application layer: coordinates the domain spec; performs no I/O.
See docs/reification-ladder-direction.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from nsforge.domain.task_spec import DerivationTaskSpec


class LadderPhase(str, Enum):
    """The four rungs of the reification ladder."""

    CONCEPT = "concept"
    SYMBOL = "symbol"
    DERIVATION = "derivation"
    ALGORITHM = "algorithm"


class PhaseStatus(str, Enum):
    OK = "ok"  # executed deterministically
    PLANNED = "planned"  # reified into a plan; needs engine/tool execution
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class PlannedStep:
    """One reified, provenance-tagged intended tool call."""

    phase: LadderPhase
    tool: str  # the tool that would produce this entity (its "birth certificate")
    purpose: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PhaseResult:
    phase: LadderPhase
    status: PhaseStatus
    detail: str = ""
    steps: list[PlannedStep] = field(default_factory=list)


@dataclass(frozen=True)
class TaskRunResult:
    spec_name: str
    ok: bool
    phases: list[PhaseResult] = field(default_factory=list)

    @property
    def plan(self) -> list[PlannedStep]:
        steps: list[PlannedStep] = []
        for phase in self.phases:
            steps.extend(phase.steps)
        return steps


@dataclass
class TaskOrchestrator:
    """Drives a ``DerivationTaskSpec`` through the reification ladder."""

    spec: DerivationTaskSpec

    def plan(self) -> list[PlannedStep]:
        """Reify the spec into an ordered list of intended tool calls."""
        steps: list[PlannedStep] = []

        # SYMBOL rung: introduce every symbol into the registry.
        for sym, meta in self.spec.given.items():
            steps.append(
                PlannedStep(
                    LadderPhase.SYMBOL,
                    "intro_many",
                    f"introduce given symbol {sym} ({meta})",
                    {"symbol": sym},
                )
            )
        for sym in self.spec.unknowns:
            steps.append(
                PlannedStep(
                    LadderPhase.SYMBOL,
                    "intro_many",
                    f"introduce unknown {sym}",
                    {"symbol": sym},
                )
            )

        # DERIVATION rung: load base formulas, apply modifications, solve.
        for base in self.spec.base_formulas:
            steps.append(
                PlannedStep(
                    LadderPhase.DERIVATION,
                    "derivation_load_formula",
                    f"load base formula: {base}",
                    {"formula": base},
                )
            )
        for mod in self.spec.modifications:
            steps.append(
                PlannedStep(
                    LadderPhase.DERIVATION,
                    "derivation_substitute",
                    f"apply modification {mod.id}",
                    {"modification": mod.id, "expression": mod.expression},
                )
            )
        for unknown in self.spec.unknowns:
            steps.append(
                PlannedStep(
                    LadderPhase.DERIVATION,
                    "derivation_solve_for",
                    f"solve for {unknown}",
                    {"target": unknown},
                )
            )
        for check in self.spec.acceptance:
            steps.append(
                PlannedStep(
                    LadderPhase.DERIVATION,
                    f"verify_{check.kind.value}",
                    check.description or f"acceptance oracle: {check.kind.value}",
                    dict(check.params),
                )
            )

        # ALGORITHM rung: reify the verified derivation into code.
        steps.append(
            PlannedStep(
                LadderPhase.ALGORITHM,
                "generate_pseudocode",
                "reify the verified derivation into human-checkable pseudocode",
            )
        )
        steps.append(
            PlannedStep(
                LadderPhase.ALGORITHM,
                "generate_python_function",
                "compile pseudocode into provenance-bound executable code",
            )
        )
        return steps

    def run(self) -> TaskRunResult:
        """Execute the deterministic phases; reify the rest into a plan."""
        phases: list[PhaseResult] = []
        plan = self.plan()

        # CONCEPT: validate coherence (deterministic).
        problems = self.spec.validate()
        if problems:
            phases.append(PhaseResult(LadderPhase.CONCEPT, PhaseStatus.FAILED, "; ".join(problems)))
            return TaskRunResult(self.spec.name, ok=False, phases=phases)
        phases.append(PhaseResult(LadderPhase.CONCEPT, PhaseStatus.OK, f"goal: {self.spec.goal}"))

        # SYMBOL: build the registry (deterministic).
        symbol_steps = [s for s in plan if s.phase is LadderPhase.SYMBOL]
        phases.append(
            PhaseResult(
                LadderPhase.SYMBOL,
                PhaseStatus.OK,
                f"{len(self.spec.symbols)} symbols: {', '.join(sorted(self.spec.symbols))}",
                symbol_steps,
            )
        )

        # DERIVATION: reified into a plan; execution is the engine extension point.
        derivation_steps = [s for s in plan if s.phase is LadderPhase.DERIVATION]
        phases.append(
            PhaseResult(
                LadderPhase.DERIVATION,
                PhaseStatus.PLANNED,
                f"{len(derivation_steps)} planned tool calls "
                "(wire to derivation engine / sympy-mcp)",
                derivation_steps,
            )
        )

        # ALGORITHM: reified into a plan.
        algo_steps = [s for s in plan if s.phase is LadderPhase.ALGORITHM]
        phases.append(
            PhaseResult(
                LadderPhase.ALGORITHM,
                PhaseStatus.PLANNED,
                "pseudocode -> code (needs the verified derivation)",
                algo_steps,
            )
        )

        return TaskRunResult(self.spec.name, ok=True, phases=phases)
