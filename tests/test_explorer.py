"""Explore mode: branching derivation search (roadmap phase 6).

Unlike self-correction (which stops at the first passing alternative), explore
runs every branch and returns all candidates ranked, each carrying its own
acceptance verdict and provenance.
"""

from __future__ import annotations

from nsforge.application.explorer import Explorer
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier


def _explore(spec: dict[str, object]) -> object:
    dts = DerivationTaskSpec.from_dict(spec)
    return Explorer(dts, engine=SymPyEngine(), verifier=BasicVerifier()).explore()


def test_explores_all_branches_and_ranks_verified_first() -> None:
    result = _explore(
        {
            "name": "explore_gain",
            "goal": "gains matching the calibration point",
            "given": {"x": "input"},
            "unknowns": ["y"],
            "base_formulas": ["y = k*x"],
            "acceptance": [
                {"kind": "boundary", "params": {"variable": "x", "at": "1", "expected": "5"}}
            ],
            "alternatives": [
                {"id": "gain_2", "target": "k", "expression": "2"},  # at x=1 -> 2 (fails)
                {"id": "gain_5", "target": "k", "expression": "5"},  # at x=1 -> 5 (passes)
            ],
        }
    )
    labels = {c.label for c in result.candidates}
    assert labels == {"base", "alternative:gain_2", "alternative:gain_5"}  # whole tree explored
    assert result.best is not None
    assert result.best.label == "alternative:gain_5"  # the verified branch ranks first
    assert result.best.verified
    # every explored branch is fully provenanced (they all executed on the engine)
    assert all(c.provenance_complete for c in result.candidates)


def test_no_alternatives_explores_just_the_base() -> None:
    result = _explore(
        {
            "name": "single",
            "goal": "one path",
            "given": {"v0": "m/s", "F": "N", "m": "kg", "t": "s"},
            "unknowns": ["v"],
            "base_formulas": ["v = v0 + a*t", "a = F / m"],
        }
    )
    assert [c.label for c in result.candidates] == ["base"]
    assert result.best is not None
    assert result.best.provenance_complete
