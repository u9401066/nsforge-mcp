"""Tests for consolidated dimensional analysis (roadmap B).

The SI dimensional logic now lives in one place (infrastructure/dimensional.py),
shared by the domain ``BasicVerifier`` and the MCP tool. Comparisons reduce to
base dimensions so derived units match (``N/kg`` == ``m/s**2``).
"""

from __future__ import annotations

from nsforge.domain.entities import Expression
from nsforge.infrastructure.dimensional import dimension_of, dimensions_match
from nsforge.infrastructure.verifier import BasicVerifier


def test_dimension_of_force() -> None:
    dim, error = dimension_of("m*a", {"m": "kg", "a": "m/s**2"})
    assert error is None
    assert dim == "length*mass/time**2"


def test_dimensions_match_reduces_derived_units() -> None:
    # N/kg is acceleration even though SymPy names the raw dimension "force/mass".
    match, _ = dimensions_match("F/m", {"F": "N", "m": "kg"}, "m/s**2")
    assert match is True


def test_dimensions_match_rejects_wrong_dimension() -> None:
    match, _ = dimensions_match("F*m", {"F": "N", "m": "kg"}, "m/s**2")
    assert match is False


def test_dimensions_match_accepts_consistent_sum() -> None:
    match, _ = dimensions_match("v0 + a*t", {"v0": "m/s", "a": "m/s**2", "t": "s"}, "m/s")
    assert match is True


def test_basic_verifier_verifies_matching_dimension() -> None:
    result = BasicVerifier().check_dimensions(
        Expression(raw="F/m"), {"F": "N", "m": "kg"}, expected_units="m/s**2"
    )
    assert result.is_verified
    assert result.dimension_check is True


def test_basic_verifier_fails_mismatched_dimension() -> None:
    result = BasicVerifier().check_dimensions(
        Expression(raw="F*m"), {"F": "N", "m": "kg"}, expected_units="m/s**2"
    )
    assert not result.is_verified


def test_basic_verifier_reports_dimension_without_expected() -> None:
    result = BasicVerifier().check_dimensions(Expression(raw="m*a"), {"m": "kg", "a": "m/s**2"})
    assert result.is_verified
    assert "length*mass/time**2" in result.message
