"""Tests for the Derivation Task Spec (L2) and Task Orchestrator (L3 skeleton)."""

from nsforge.application.task_orchestrator import (
    LadderPhase,
    PhaseStatus,
    TaskOrchestrator,
)
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.domain.value_objects import MathContext
from nsforge.infrastructure.sympy_engine import SymPyEngine

_GOOD_SPEC = {
    "name": "temp_corrected",
    "goal": "derive C(t) with temperature-corrected elimination rate",
    "given": {"C0": "mg/L", "t": "h", "T": "K"},
    "unknowns": ["C"],
    "assumptions": ["T>0"],
    "base_formulas": ["C = C0*exp(-k*t)", "k = A*exp(-Ea/(R*T))"],
    "modifications": [{"id": "arrhenius_k", "expression": "A*exp(-Ea/(R*T))"}],
    "acceptance": [{"kind": "dimensional", "params": {"target": "C"}}],
}


def test_from_dict_roundtrip() -> None:
    spec = DerivationTaskSpec.from_dict(_GOOD_SPEC)
    assert spec.name == "temp_corrected"
    assert spec.unknowns == ["C"]
    assert spec.symbols == {"C0", "t", "T", "C"}
    assert spec.modifications[0].id == "arrhenius_k"
    assert spec.validate() == []


def test_validate_flags_incomplete_spec() -> None:
    spec = DerivationTaskSpec.from_dict(
        {"name": "", "goal": "", "unknowns": [], "base_formulas": []}
    )
    problems = spec.validate()
    assert any("name" in p for p in problems)
    assert any("goal" in p for p in problems)
    assert any("unknowns" in p for p in problems)
    assert any("base_formulas" in p for p in problems)


def test_orchestrator_plan_covers_all_rungs() -> None:
    spec = DerivationTaskSpec.from_dict(_GOOD_SPEC)
    plan = TaskOrchestrator(spec).plan()
    phases = {step.phase for step in plan}
    assert LadderPhase.SYMBOL in phases
    assert LadderPhase.DERIVATION in phases
    assert LadderPhase.ALGORITHM in phases
    # every planned step names the tool that would produce it (provenance)
    assert all(step.tool for step in plan)


def test_orchestrator_run_ok_path() -> None:
    spec = DerivationTaskSpec.from_dict(_GOOD_SPEC)
    result = TaskOrchestrator(spec).run()
    assert result.ok is True
    statuses = {p.phase: p.status for p in result.phases}
    assert statuses[LadderPhase.CONCEPT] is PhaseStatus.OK
    assert statuses[LadderPhase.SYMBOL] is PhaseStatus.OK
    assert statuses[LadderPhase.DERIVATION] is PhaseStatus.PLANNED
    assert result.plan  # non-empty reified plan


def test_orchestrator_run_fails_on_bad_spec() -> None:
    spec = DerivationTaskSpec.from_dict(
        {"name": "x", "goal": "", "unknowns": [], "base_formulas": []}
    )
    result = TaskOrchestrator(spec).run()
    assert result.ok is False
    assert result.phases[0].phase is LadderPhase.CONCEPT
    assert result.phases[0].status is PhaseStatus.FAILED


def test_orchestrator_executes_derivation_with_engine() -> None:
    spec = DerivationTaskSpec.from_dict(_GOOD_SPEC)
    result = TaskOrchestrator(spec, engine=SymPyEngine()).run()
    assert result.ok is True
    statuses = {p.phase: p.status for p in result.phases}
    # With an engine wired, the derivation rung executes (no longer PLANNED).
    assert statuses[LadderPhase.DERIVATION] is PhaseStatus.OK
    assert result.derived_expression.startswith("C =")

    # The composed result must be the temperature-corrected form. Declare the
    # symbols so digit-suffixed C0 is not split into C*0 by the parser.
    engine = SymPyEngine()
    ctx = MathContext(assumptions={n: {} for n in ["C0", "A", "t", "Ea", "R", "T", "C", "k"]})
    derived_rhs = result.derived_expression.split("=", 1)[1]
    expected = engine.parse("C0*exp(-A*t*exp(-Ea/(R*T)))", ctx)
    assert engine.equals(engine.parse(derived_rhs, ctx), expected)


def test_modification_target_drives_substitution() -> None:
    spec = DerivationTaskSpec.from_dict(
        {
            "name": "mod_target",
            "goal": "apply a modification via its target symbol",
            "unknowns": ["a"],
            "base_formulas": ["a = F / m"],
            "modifications": [{"id": "friction", "expression": "F - mu*Fn", "target": "F"}],
        }
    )
    result = TaskOrchestrator(spec, engine=SymPyEngine()).run()
    assert result.ok is True
    engine = SymPyEngine()
    derived_rhs = result.derived_expression.split("=", 1)[1]
    assert engine.equals(engine.parse(derived_rhs), engine.parse("(F - mu*Fn)/m"))
