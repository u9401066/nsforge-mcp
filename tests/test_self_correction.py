"""Self-correction loop (roadmap phase 4): retry alternatives until acceptance passes.

The orchestrator now tries the base derivation, then each alternative candidate,
stopping at the first that satisfies the acceptance oracles — closing the
explore -> verify -> revise -> re-verify loop.
"""

from __future__ import annotations

from typing import Any

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier

# Calibration oracle: at x = 1 the model must equal 5.
_ACCEPT = [{"kind": "boundary", "params": {"variable": "x", "at": "1", "expected": "5"}}]


def _run(spec: dict[str, Any]) -> Any:
    dts = DerivationTaskSpec.from_dict(spec)
    return TaskOrchestrator(dts, engine=SymPyEngine(), verifier=BasicVerifier()).run()


def test_retries_until_an_alternative_passes() -> None:
    result = _run(
        {
            "name": "corrected_gain",
            "goal": "gain matching the calibration point",
            "given": {"x": "input"},
            "unknowns": ["y"],
            "base_formulas": ["y = k*x"],
            "acceptance": _ACCEPT,
            "alternatives": [
                {"id": "gain_2", "target": "k", "expression": "2"},  # y=2x -> at x=1 is 2 (fails)
                {"id": "gain_5", "target": "k", "expression": "5"},  # y=5x -> at x=1 is 5 (passes)
            ],
        }
    )
    assert result.verified
    assert [(a.label, a.verified) for a in result.attempts] == [
        ("base", False),
        ("alternative:gain_2", False),
        ("alternative:gain_5", True),
    ]
    engine = SymPyEngine()
    rhs = result.derived_expression.split("=", 1)[1]
    assert engine.equals(engine.parse(rhs), engine.parse("5*x"))


def test_no_retry_when_base_passes() -> None:
    result = _run(
        {
            "name": "base_ok",
            "goal": "base already satisfies",
            "given": {"x": "input"},
            "unknowns": ["y"],
            "base_formulas": ["y = 5*x"],
            "acceptance": _ACCEPT,
            "alternatives": [{"id": "gain_9", "target": "k", "expression": "9"}],
        }
    )
    assert result.verified
    assert len(result.attempts) == 1  # base passed -> no alternatives tried
    assert result.attempts[0].label == "base"


def test_all_attempts_fail_reports_unverified() -> None:
    result = _run(
        {
            "name": "no_fix",
            "goal": "nothing satisfies the calibration",
            "given": {"x": "input"},
            "unknowns": ["y"],
            "base_formulas": ["y = k*x"],
            "acceptance": _ACCEPT,
            "alternatives": [{"id": "gain_2", "target": "k", "expression": "2"}],
        }
    )
    assert not result.verified
    assert len(result.attempts) == 2  # base + gain_2, both fail
    assert all(not attempt.verified for attempt in result.attempts)
