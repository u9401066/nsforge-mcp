"""Tests for the Derivation Task Spec (L2) and Task Orchestrator (L3 skeleton)."""

from nsforge.application.task_orchestrator import (
    LadderPhase,
    PhaseStatus,
    TaskOrchestrator,
)
from nsforge.domain.task_spec import DerivationTaskSpec

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
