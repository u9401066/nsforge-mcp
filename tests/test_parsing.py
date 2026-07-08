"""The shared guarded parser (infrastructure/parsing.py).

Consolidates three duplicate ``_parse_safe`` helpers and closes the gap where
calculate/simplify parsed caller-supplied input without the DoS guard.
"""

from __future__ import annotations

import sympy as sp

from nsforge.infrastructure.parsing import parse_expression_safe


def test_guards_unsafe_input() -> None:
    expr, error = parse_expression_safe("9**9**9")
    assert expr is None
    assert error is not None


def test_accepts_ordinary_expression() -> None:
    expr, error = parse_expression_safe("a*x + b")
    assert error is None
    assert expr is not None


def test_supports_local_dict_assumptions() -> None:
    expr, error = parse_expression_safe("x + 1", local_dict={"x": sp.Symbol("x", positive=True)})
    assert error is None
    assert expr is not None


def test_can_disable_safety_check() -> None:
    # Explicit opt-out still parses (used for trusted internal input).
    expr, error = parse_expression_safe("a + b", check_safety=False)
    assert error is None
    assert expr is not None
