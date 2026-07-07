"""
NSForge Task Orchestrator (L3 skeleton) — drives the reification ladder.

Turns a declarative ``DerivationTaskSpec`` (L2) into an ordered, provenance-tagged
plan of tool calls, and executes the phases it can do deterministically
(concept validation, symbol registry). The symbolic-execution rungs are reified
into a plan whose steps each name the tool that would produce them — the
"birth certificate" (provenance) required by the north star. Wiring those steps
to the real derivation engine / sympy-mcp is the extension point.

Application layer: coordinates the domain spec via the ``SymbolicEngine`` domain
service (injected); performs no I/O. When an engine is wired, the DERIVATION rung
executes deterministically (compose base formulas via substitution); otherwise it
is reified into a plan. See docs/reification-ladder-direction.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from nsforge.domain.services import SymbolicEngine
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.domain.value_objects import MathContext

# Names that must NOT be declared as symbols (SymPy functions / constants).
_FUNCTION_NAMES = frozenset(
    {
        "exp",
        "log",
        "ln",
        "sqrt",
        "Abs",
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "asin",
        "acos",
        "atan",
        "sinh",
        "cosh",
        "tanh",
        "pi",
        "E",
        "I",
        "oo",
    }
)


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
    derived_expression: str = ""  # set when the DERIVATION rung executes on an engine

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
    engine: SymbolicEngine | None = None  # inject an engine to execute the DERIVATION rung

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

        # DERIVATION: execute deterministically if an engine is wired; else plan.
        derived_expression = ""
        if self.engine is not None:
            derivation_result, derived_expression = self._execute_derivation()
            phases.append(derivation_result)
        else:
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

        return TaskRunResult(
            self.spec.name, ok=True, phases=phases, derived_expression=derived_expression
        )

    def _execute_derivation(self) -> tuple[PhaseResult, str]:
        """Compose the base formulas via substitution using the injected engine.

        Deterministically resolves "lhs = rhs" base formulas into a single derived
        expression for the primary unknown, recording each substitution with
        provenance. Falls back to PLANNED (an extension point for the derivation
        engine / sympy-mcp handoff) for anything it cannot handle.

        Returns (phase_result, derived_expression).
        """
        engine = self.engine
        assert engine is not None  # guarded by caller

        # Declare every identifier as a symbol so digit-suffixed names (C0, V1,
        # k10) parse as single symbols instead of implicit products (C*0).
        context = self._symbol_context()

        # Split "lhs = rhs" base formulas into (lhs_symbol, rhs_str).
        defs: list[tuple[str, str]] = []
        for formula in self.spec.base_formulas:
            if "=" not in formula:
                return (
                    PhaseResult(
                        LadderPhase.DERIVATION,
                        PhaseStatus.PLANNED,
                        f"base formula is not an equation: {formula!r} (needs handoff)",
                    ),
                    "",
                )
            lhs, rhs = formula.split("=", 1)
            defs.append((lhs.strip(), rhs.strip()))

        # Target = the definition whose LHS is an unknown (else the first).
        unknowns = set(self.spec.unknowns)
        target_idx = next((i for i, (lhs, _) in enumerate(defs) if lhs in unknowns), 0)
        target_lhs, target_rhs = defs[target_idx]

        working = engine.parse(target_rhs, context)
        if not working.is_valid:
            return (
                PhaseResult(
                    LadderPhase.DERIVATION,
                    PhaseStatus.PLANNED,
                    f"could not parse target formula: {target_rhs!r} (needs handoff)",
                ),
                "",
            )

        # Substitution rules: other base formulas + modifications with a target.
        rules: list[tuple[str, str, str]] = []  # (symbol, replacement, source)
        for i, (lhs, rhs) in enumerate(defs):
            if i != target_idx and lhs:
                rules.append((lhs, rhs, "base_formula"))
        for mod in self.spec.modifications:
            if mod.target and mod.expression:
                rules.append((mod.target, mod.expression, f"modification:{mod.id}"))

        # Apply each substitution rule once, in order (give base formulas
        # target-first so a single pass resolves the chain). A single pass also
        # keeps self-referential modifications (e.g. F -> F - mu*N) from runaway
        # re-application.
        steps: list[PlannedStep] = []
        for symbol, replacement, source in rules:
            repl = engine.parse(replacement, context)
            if not repl.is_valid:
                continue
            substituted = engine.substitute(working, {symbol: repl.sympy_expr}, context)
            if substituted.raw != working.raw:
                steps.append(
                    PlannedStep(
                        LadderPhase.DERIVATION,
                        "engine.substitute",
                        f"substitute {symbol} -> {replacement} (from {source})",
                        {"symbol": symbol, "replacement": replacement, "source": source},
                    )
                )
                working = substituted

        working = engine.simplify(working)
        derived = f"{target_lhs} = {working.raw}"
        detail = f"executed: {derived}  ({len(steps)} substitution step(s))"
        return (PhaseResult(LadderPhase.DERIVATION, PhaseStatus.OK, detail, steps), derived)

    def _symbol_context(self) -> MathContext:
        """Declare every identifier in the spec as a symbol.

        Prevents SymPy's implicit-multiplication parser from splitting
        digit-suffixed names (e.g. ``C0`` -> ``C*0``), essential for
        pharmacokinetic notation (C0, V1, k10, ...).
        """
        names = set(self.spec.given) | set(self.spec.unknowns)
        texts = [*self.spec.base_formulas, *(m.expression for m in self.spec.modifications)]
        for text in texts:
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
                if token not in _FUNCTION_NAMES:
                    names.add(token)
        assumptions: dict[str, dict[str, bool]] = {name: {} for name in names}
        return MathContext(assumptions=assumptions)
