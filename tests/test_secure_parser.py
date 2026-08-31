"""Regression coverage for the no-eval expression trust boundary."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from typing import Any

import pytest
import sympy as sp

from nsforge.domain.formula import Formula, FormulaParser, ParseError
from nsforge.domain.safe_parse import (
    UnsafeExpressionError,
    check_expression_safety,
    parse_expression_allowlisted,
)
from nsforge.infrastructure.derivation_repository import DerivationResult
from nsforge.infrastructure.parsing import parse_expression_safe
from nsforge_mcp.tools.expression import register_expression_tools
from nsforge_mcp.tools.music import register_music_tools

MALICIOUS_EXPRESSIONS = (
    "__import__('os')",
    "x.__class__",
    "(1).real",
    "(lambda x: x + 1)(2)",
    "[x for x in values]",
    "{x: x for x in values}",
    "eval(x)",
)


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.mark.parametrize("expression", MALICIOUS_EXPRESSIONS)
def test_malicious_corpus_is_rejected_before_construction(expression: str) -> None:
    assert check_expression_safety(expression) is not None

    parsed, error = parse_expression_safe(expression)
    assert parsed is None
    assert error

    with pytest.raises(UnsafeExpressionError):
        parse_expression_allowlisted(expression)


def test_parser_does_not_call_python_eval(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_eval(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("Python eval must never be used at the expression boundary")

    monkeypatch.setattr(builtins, "eval", forbidden_eval)
    parsed = parse_expression_allowlisted("2x + 3sin(x)")
    x = sp.Symbol("x")
    assert sp.simplify(parsed - (2 * x + 3 * sp.sin(x))) == 0


@pytest.mark.parametrize(
    "expression",
    (
        "2**100000000",
        "10**(10**6)",
        "factorial(1000000)",
        "factorial2(1000000)",
        "binomial(1000000, 500000)",
        "gamma(1000000)",
        "beta(1001, 1001)",
        "digamma(1001)",
        "polygamma(129, 129)",
        "lowergamma(1001, 1001)",
        "uppergamma(1001, 1001)",
    ),
)
def test_eager_numeric_construction_has_literal_resource_budgets(expression: str) -> None:
    with pytest.raises(UnsafeExpressionError, match="eager-construction budget"):
        parse_expression_allowlisted(expression)


def test_implicit_functions_and_equations_remain_supported() -> None:
    parsed = parse_expression_allowlisted("sin x + f(x) + exp(-k*t)")
    x, k, t = sp.symbols("x k t")
    expected = sp.sin(x) + sp.Function("f")(x) + sp.exp(-k * t)
    assert sp.simplify(parsed - expected) == 0

    equation = parse_expression_allowlisted("F = m*a")
    assert isinstance(equation, sp.Equality)
    assert {str(symbol) for symbol in equation.free_symbols} == {"F", "a", "m"}


def test_formula_parser_uses_the_same_secure_boundary() -> None:
    accepted = FormulaParser.parse("2x + sin(x)", formula_id="valid")
    assert isinstance(accepted, Formula)

    rejected = FormulaParser.parse("x.__class__", formula_id="malicious")
    assert isinstance(rejected, ParseError)


def test_persisted_derivation_expression_uses_secure_boundary() -> None:
    assert str(DerivationResult(id="valid", name="valid", expression="2x").to_sympy()) == "2*x"

    result = DerivationResult(id="malicious", name="malicious", expression="x.__class__")
    with pytest.raises(ValueError, match="not allowed"):
        result.to_sympy()


@pytest.mark.parametrize("expression", MALICIOUS_EXPRESSIONS)
def test_mcp_expression_tools_reject_malicious_corpus(expression: str) -> None:
    mcp = _FakeMCP()
    register_expression_tools(mcp)

    assert mcp.tools["parse_expression"](expression)["success"] is False
    assert mcp.tools["validate_expression"](expression)["valid"] is False
    assert mcp.tools["extract_symbols"](expression)["success"] is False


def test_music_expression_path_uses_secure_boundary() -> None:
    mcp = _FakeMCP()
    register_music_tools(mcp)

    rejected = mcp.tools["music_function_info"]("x.__class__")
    accepted = mcp.tools["music_function_info"]("2sin(2*pi*t)")

    assert rejected["success"] is False
    assert accepted["success"] is True
