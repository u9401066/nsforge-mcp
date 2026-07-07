"""Regression tests for the L3 orchestrator closing the reification ladder.

Covers the rungs wired in roadmap phase A: the DERIVATION rung isolating an
unknown via ``engine.solve`` (solve_for), and the ALGORITHM rung reifying the
verified derivation into executable code.
"""

from __future__ import annotations

from nsforge.application.task_orchestrator import LadderPhase, PhaseStatus, TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine


def _run(spec: dict[str, object]) -> object:
    dts = DerivationTaskSpec.from_dict(spec)
    return TaskOrchestrator(dts, engine=SymPyEngine()).run()


def _phase(result: object, phase: LadderPhase) -> object:
    return next(p for p in result.phases if p.phase is phase)  # type: ignore[attr-defined]


def test_solve_for_isolates_the_unknown() -> None:
    """d = v*t, unknown t  ->  t = d/v (unknown not already the LHS)."""
    result = _run(
        {
            "name": "distance_solve_for_time",
            "goal": "solve for elapsed time",
            "given": {"d": "m", "v": "m/s"},
            "unknowns": ["t"],
            "base_formulas": ["d = v*t"],
        }
    )
    assert result.ok  # type: ignore[attr-defined]
    lhs, _, rhs = result.derived_expression.partition("=")  # type: ignore[attr-defined]
    assert lhs.strip() == "t"
    engine = SymPyEngine()
    assert engine.equals(engine.parse(rhs), engine.parse("d/v"))


def test_algorithm_rung_reifies_code() -> None:
    """A produced derivation is compiled into a runnable, correct function."""
    result = _run(
        {
            "name": "velocity_constant_force",
            "goal": "velocity under constant force",
            "given": {"v0": "m/s", "F": "N", "m": "kg", "t": "s"},
            "unknowns": ["v"],
            "base_formulas": ["v = v0 + a*t", "a = F / m"],
        }
    )
    assert result.ok  # type: ignore[attr-defined]

    algorithm = _phase(result, LadderPhase.ALGORITHM)
    assert algorithm.status is PhaseStatus.OK  # type: ignore[attr-defined]

    code = result.generated_code  # type: ignore[attr-defined]
    assert code.startswith("def velocity_constant_force(")
    assert "return" in code

    # The generated function computes the derived expression correctly.
    namespace: dict[str, object] = {}
    exec(code, namespace)  # noqa: S102 - generated from a verified derivation, test-only
    out = namespace["velocity_constant_force"](v0=1.0, F=6.0, m=2.0, t=3.0)
    assert out["v"] == 1.0 + 6.0 * 3.0 / 2.0


def test_plain_composition_still_planned_without_engine() -> None:
    """Without an engine the ALGORITHM rung stays PLANNED (no hand-derivation)."""
    dts = DerivationTaskSpec.from_dict(
        {
            "name": "no_engine",
            "goal": "compose",
            "unknowns": ["v"],
            "base_formulas": ["v = v0 + a*t"],
        }
    )
    result = TaskOrchestrator(dts).run()  # no engine injected
    algorithm = _phase(result, LadderPhase.ALGORITHM)
    assert algorithm.status is PhaseStatus.PLANNED  # type: ignore[attr-defined]
    assert result.generated_code == ""  # type: ignore[attr-defined]
