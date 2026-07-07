"""Acceptance-oracle execution in the L3 orchestrator (roadmap A: the VERIFY step).

A derived formula is trusted only when its oracles pass. These cover the four
oracle kinds executed by the orchestrator: equivalence, boundary, limit
(engine-driven) and dimensional (domain Verifier-driven).
"""

from __future__ import annotations

from typing import Any

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier


def _run(spec: dict[str, Any]) -> Any:
    dts = DerivationTaskSpec.from_dict(spec)
    return TaskOrchestrator(dts, engine=SymPyEngine(), verifier=BasicVerifier()).run()


def test_equivalence_boundary_and_limit_pass_for_first_order_decay() -> None:
    result = _run(
        {
            "name": "first_order_decay",
            "goal": "concentration after first-order elimination",
            "given": {"C0": "mg/L", "k": "1/h", "t": "h"},
            "unknowns": ["C"],
            "assumptions": ["k>0"],
            "base_formulas": ["C = C0*exp(-k*t)"],
            "acceptance": [
                {"kind": "equivalence", "params": {"reference": "C0*exp(-k*t)"}},
                {"kind": "boundary", "params": {"variable": "t", "at": "0", "expected": "C0"}},
                {"kind": "limit", "params": {"variable": "t", "to": "oo", "expected": "0"}},
            ],
        }
    )
    assert result.ok
    assert result.verified
    statuses = {o.kind: o.status for o in result.acceptance}
    assert statuses == {
        "equivalence": "verified",
        "boundary": "verified",
        "limit": "verified",
    }


def test_failing_boundary_marks_result_unverified() -> None:
    result = _run(
        {
            "name": "bad_boundary",
            "goal": "wrong boundary expectation",
            "given": {"C0": "mg/L", "k": "1/h", "t": "h"},
            "unknowns": ["C"],
            "assumptions": ["k>0"],
            "base_formulas": ["C = C0*exp(-k*t)"],
            "acceptance": [
                {"kind": "boundary", "params": {"variable": "t", "at": "0", "expected": "2*C0"}},
            ],
        }
    )
    assert not result.verified
    assert result.acceptance[0].status == "failed"


def test_dimensional_oracle_uses_the_verifier() -> None:
    result = _run(
        {
            "name": "velocity_dimensional",
            "goal": "velocity under constant force",
            "given": {"v0": "m/s", "F": "N", "m": "kg", "t": "s"},
            "unknowns": ["v"],
            "base_formulas": ["v = v0 + a*t", "a = F / m"],
            "acceptance": [
                {
                    "kind": "dimensional",
                    "params": {
                        "units": {"v0": "m/s", "F": "N", "m": "kg", "t": "s"},
                        "expected_units": "m/s",
                    },
                },
            ],
        }
    )
    assert result.verified
    assert result.acceptance[0].status == "verified"


def test_no_acceptance_defaults_to_verified() -> None:
    result = _run(
        {
            "name": "no_oracles",
            "goal": "compose only",
            "unknowns": ["v"],
            "base_formulas": ["v = v0 + a*t", "a = F / m"],
        }
    )
    assert result.verified  # nothing to check -> trivially verified
    assert result.acceptance == []
