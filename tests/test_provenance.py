"""Provenance ledger + enforcement (roadmap phase 5).

Every executed derivation carries a complete chain of birth certificates (base
formula -> tool steps -> final expression); code is emitted only from a complete
ledger, so nothing un-sourced (hand-derived) reaches a result.
"""

from __future__ import annotations

from typing import Any

from nsforge.application.task_orchestrator import LadderPhase, PhaseStatus, TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine


def _run(spec: dict[str, Any]) -> Any:
    return TaskOrchestrator(DerivationTaskSpec.from_dict(spec), engine=SymPyEngine()).run()


def test_executed_derivation_is_fully_provenanced() -> None:
    result = _run(
        {
            "name": "velocity",
            "goal": "velocity under constant force",
            "given": {"v0": "m/s", "F": "N", "m": "kg", "t": "s"},
            "unknowns": ["v"],
            "base_formulas": ["v = v0 + a*t", "a = F / m"],
        }
    )
    assert result.provenance.is_complete
    assert not result.provenance.unsourced()
    assert all(entry.tool for entry in result.provenance.entries)  # every entity tool-sourced
    # base formulas are recorded as inputs, the result as engine-produced
    tools = {entry.tool for entry in result.provenance.entries}
    assert "input:base_formula" in tools
    assert result.generated_code  # code emitted precisely because provenance is complete


def test_unexecutable_derivation_gets_no_code() -> None:
    # A non-equation "formula" cannot be composed -> PLANNED -> no provenance, no code.
    result = _run(
        {
            "name": "handoff_case",
            "goal": "cannot be composed by substitution",
            "unknowns": ["y"],
            "base_formulas": ["diff(y, x) + y"],  # no '=' -> needs handoff
        }
    )
    assert not result.provenance.is_complete
    assert result.generated_code == ""  # code refused: no complete provenance
    algorithm = next(p for p in result.phases if p.phase is LadderPhase.ALGORITHM)
    assert algorithm.status is PhaseStatus.PLANNED
