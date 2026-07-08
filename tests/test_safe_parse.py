"""Tests for the untrusted-input parse guard (multi-agent DoS hardening).

As a shared service NSForge must not let one agent's pathological expression
(power towers, huge literals, deep nesting) exhaust CPU/memory and starve the
others. The guard rejects those cheaply, before parsing.
"""

from __future__ import annotations

from nsforge.domain.safe_parse import check_expression_safety
from nsforge.infrastructure.sympy_engine import SymPyEngine


def test_ordinary_formulas_pass() -> None:
    assert check_expression_safety("C0*exp(-k*t) + v0 + a*t/m") is None
    assert check_expression_safety("V = I*R") is None
    assert check_expression_safety("x**2 + y**2 + z**2") is None  # multiple powers ok


def test_power_tower_rejected() -> None:
    assert check_expression_safety("9**9**9") is not None


def test_overlong_expression_rejected() -> None:
    assert check_expression_safety("x+" * 5000) is not None


def test_deep_nesting_rejected() -> None:
    assert check_expression_safety("(" * 200 + "x" + ")" * 200) is not None


def test_huge_integer_literal_rejected() -> None:
    assert check_expression_safety("x**123456789012345678") is not None


def test_engine_returns_invalid_for_unsafe_input() -> None:
    assert not SymPyEngine().parse("9**9**9").is_valid
    assert SymPyEngine().parse("a*t + v0").is_valid  # ordinary input still parses
