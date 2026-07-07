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

from nsforge.domain.codegen import render_python_function
from nsforge.domain.entities import Expression
from nsforge.domain.services import SymbolicEngine, Verifier
from nsforge.domain.task_spec import AcceptanceCheck, AcceptanceKind, DerivationTaskSpec
from nsforge.domain.value_objects import MathContext, VerificationStatus

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


def _verdict(ok: bool) -> str:
    """Map a boolean oracle result to an acceptance status string."""
    return "verified" if ok else "failed"


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
class AcceptanceOutcome:
    """The result of executing one acceptance oracle against the derived result."""

    kind: str
    status: str  # verified | failed | inconclusive | error
    detail: str = ""


@dataclass(frozen=True)
class TaskRunResult:
    spec_name: str
    ok: bool
    phases: list[PhaseResult] = field(default_factory=list)
    derived_expression: str = ""  # set when the DERIVATION rung executes on an engine
    generated_code: str = ""  # set when the ALGORITHM rung reifies code
    acceptance: list[AcceptanceOutcome] = field(default_factory=list)
    verified: bool = True  # False if any acceptance oracle did not pass

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
    verifier: Verifier | None = None  # inject to execute DIMENSIONAL acceptance oracles

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

        # VERIFY: run the acceptance oracles against the derived result.
        acceptance: list[AcceptanceOutcome] = []
        if derived_expression and self.engine is not None and self.spec.acceptance:
            acceptance = self._execute_acceptance(derived_expression)

        # ALGORITHM: reify the verified derivation into code when we have one.
        generated_code = ""
        if derived_expression and self.engine is not None:
            algo_result, generated_code = self._execute_algorithm(derived_expression)
            phases.append(algo_result)
        else:
            algo_steps = [s for s in plan if s.phase is LadderPhase.ALGORITHM]
            phases.append(
                PhaseResult(
                    LadderPhase.ALGORITHM,
                    PhaseStatus.PLANNED,
                    "pseudocode -> code (needs the verified derivation)",
                    algo_steps,
                )
            )

        verified = all(o.status == "verified" for o in acceptance) if acceptance else True
        return TaskRunResult(
            self.spec.name,
            ok=True,
            phases=phases,
            derived_expression=derived_expression,
            generated_code=generated_code,
            acceptance=acceptance,
            verified=verified,
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

        # solve_for: if the primary unknown isn't already the LHS, isolate it by
        # solving the composed equation (working = target_lhs) for the unknown.
        primary = self.spec.unknowns[0] if self.spec.unknowns else ""
        if primary and primary != target_lhs:
            equation = engine.parse(f"({working.raw}) - ({target_lhs})", context)
            solutions = engine.solve(equation, primary, context) if equation.is_valid else []
            if solutions:
                working = solutions[0]
                steps.append(
                    PlannedStep(
                        LadderPhase.DERIVATION,
                        "engine.solve",
                        f"solve {target_lhs} = ... for {primary}",
                        {"target": primary},
                    )
                )
                target_lhs = primary

        working = engine.simplify(working)
        derived = f"{target_lhs} = {working.raw}"
        detail = f"executed: {derived}  ({len(steps)} step(s))"
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
        # Apply simple sign assumptions ("k>0", "T>=0") so limits/simplifications
        # behave (e.g. lim t->oo of exp(-k*t) needs k>0).
        for raw in self.spec.assumptions:
            match = re.match(r"\s*([A-Za-z_]\w*)\s*(>=|>)\s*0\s*$", raw)
            if match:
                name, op = match.group(1), match.group(2)
                assumptions.setdefault(name, {})
                assumptions[name]["positive" if op == ">" else "nonnegative"] = True
        return MathContext(assumptions=assumptions)

    def _execute_acceptance(self, derived: str) -> list[AcceptanceOutcome]:
        """Run each acceptance oracle against the derived result (the VERIFY step).

        A derived formula is trusted only when its oracles pass -- the provenance
        of *correctness*, executed by tools rather than asserted by the agent.
        """
        engine = self.engine
        assert engine is not None  # guarded by caller

        context = self._symbol_context()
        rhs = derived.split("=", 1)[1].strip() if "=" in derived else derived
        working = engine.parse(rhs, context)
        return [self._run_oracle(check, working, context) for check in self.spec.acceptance]

    def _run_oracle(
        self, check: AcceptanceCheck, working: Expression, context: MathContext
    ) -> AcceptanceOutcome:
        """Execute a single acceptance oracle; never raises."""
        engine = self.engine
        assert engine is not None  # guarded by caller
        kind = check.kind
        params = check.params

        try:
            if kind is AcceptanceKind.EQUIVALENCE:
                ref = engine.parse(str(params.get("reference", "")), context)
                ok = ref.is_valid and engine.equals(working, ref, context)
                return AcceptanceOutcome(kind.value, _verdict(ok), f"reference={ref.raw}")

            if kind is AcceptanceKind.BOUNDARY:
                var = str(params.get("variable", ""))
                at = engine.parse(str(params.get("at", "")), context)
                got = (
                    engine.substitute(working, {var: at.sympy_expr}, context)
                    if at.is_valid
                    else working
                )
                exp = engine.parse(str(params.get("expected", "")), context)
                ok = exp.is_valid and engine.equals(got, exp, context)
                return AcceptanceOutcome(kind.value, _verdict(ok), f"{var}@{at.raw} -> {got.raw}")

            if kind is AcceptanceKind.LIMIT:
                var = str(params.get("variable", ""))
                to = str(params.get("to", ""))
                got = engine.limit(working, var, to, context)
                exp = engine.parse(str(params.get("expected", "")), context)
                ok = got.is_valid and exp.is_valid and engine.equals(got, exp, context)
                return AcceptanceOutcome(kind.value, _verdict(ok), f"lim {var}->{to}: {got.raw}")

            if kind is AcceptanceKind.DIMENSIONAL:
                if self.verifier is None:
                    return AcceptanceOutcome(kind.value, "inconclusive", "no verifier injected")
                units = {str(k): str(v) for k, v in dict(params.get("units", {})).items()}
                expected = params.get("expected_units")
                result = self.verifier.check_dimensions(
                    working, units, str(expected) if expected is not None else None
                )
                status = (
                    "error"
                    if result.status is VerificationStatus.ERROR
                    else _verdict(result.is_verified)
                )
                return AcceptanceOutcome(kind.value, status, result.message)
        except Exception as exc:  # an oracle must never crash the run
            return AcceptanceOutcome(kind.value, "error", str(exc))
        return AcceptanceOutcome(kind.value, "inconclusive", "unhandled acceptance kind")

    def _execute_algorithm(self, derived: str) -> tuple[PhaseResult, str]:
        """Reify the verified derivation into an executable Python function.

        The ALGORITHM rung: assemble the derived expression into provenance-tagged
        code via the domain code renderer (no hand-writing). Returns
        (phase_result, generated_code).
        """
        engine = self.engine
        assert engine is not None  # guarded by caller

        context = self._symbol_context()
        lhs, _, rhs = derived.partition("=")
        lhs, rhs = lhs.strip(), rhs.strip()

        expr = engine.parse(rhs, context)
        rhs_syms = {str(s) for s in expr.sympy_expr.free_symbols} if expr.is_valid else set()

        parameters: list[dict[str, str]] = [
            {"name": name, "type": "float", "description": str(self.spec.given.get(name, ""))}
            for name in sorted(self.spec.given)
            if name in rhs_syms
        ]
        for name in sorted(rhs_syms - set(self.spec.given)):
            parameters.append({"name": name, "type": "float", "description": ""})

        steps: list[dict[str, str]] = [
            {
                "description": self.spec.goal or f"compute {lhs}",
                "expression": rhs,
                "result_var": lhs,
            }
        ]
        func_name = re.sub(r"\W+", "_", self.spec.name).strip("_").lower() or "derived_function"
        code = render_python_function(
            func_name, self.spec.goal or self.spec.name, parameters, steps, [lhs]
        )
        step = PlannedStep(
            LadderPhase.ALGORITHM,
            "generate_python_function",
            "reify the verified derivation into provenance-bound code",
            {"function": func_name},
        )
        return (
            PhaseResult(LadderPhase.ALGORITHM, PhaseStatus.OK, f"generated {func_name}()", [step]),
            code,
        )
