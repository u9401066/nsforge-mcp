"""Regression tests for Unicode-friendly derivation expression parsing."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import sympy as sp

from nsforge.domain.derivation_session import SessionManager
from nsforge_mcp.tools import derivation as derivation_tools


class MockMCP:
    """Minimal MCP stub for registering tool functions in tests."""

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[func.__name__] = func
            return func

        return decorator


def _build_derivation_tools(tmp_path: Path) -> MockMCP:
    derivation_tools._manager = SessionManager(tmp_path / "derivation_sessions")
    derivation_tools._set_current_session(None)

    mcp = MockMCP()
    derivation_tools.register_derivation_tools(mcp)
    return mcp


def test_preprocess_for_sympify_uses_safe_placeholders() -> None:
    """Greek identifiers should map to Symbols instead of SymPy functions/keywords."""
    prepared, local_dict = derivation_tools._preprocess_for_sympify("N_0 * exp(-λ*t) + β")

    assert "λ" not in prepared
    assert "β" not in prepared
    assert "__nsf_symbol_0__" in prepared
    assert prepared == "N_0 * exp(-__nsf_symbol_0__*t) + __nsf_symbol_1__"
    assert local_dict["__nsf_symbol_0__"].name == "lambda"
    assert local_dict["__nsf_symbol_1__"].name == "beta"


def test_derivation_record_step_accepts_unicode_greek_input(tmp_path: Path) -> None:
    """derivation_record_step should accept Unicode Greek letters without SyntaxError."""
    mcp = _build_derivation_tools(tmp_path)

    start = mcp.tools["derivation_start"]
    record_step = mcp.tools["derivation_record_step"]

    assert callable(start)
    assert callable(record_step)

    start(name="unicode_record_step")
    result = record_step(
        expression="N_0 * exp(-λ*t) + β",
        description="Record Unicode expression",
    )

    assert result["success"] is True
    assert result["expression"] == "N_0*exp(-lambda*t) + beta"
    assert r"\lambda" in result["latex"]
    assert r"\beta" in result["latex"]
    session = derivation_tools._get_current_session()
    assert session is not None
    expected = sp.Symbol("N_0") * sp.exp(-sp.Symbol("lambda") * sp.Symbol("t")) + sp.Symbol("beta")
    assert session.current_expression is not None
    assert sp.simplify(session.current_expression - expected) == 0


def test_derivation_import_from_sympy_accepts_unicode_subscripts(tmp_path: Path) -> None:
    """derivation_import_from_sympy should normalize Greek letters and Unicode subscripts."""
    mcp = _build_derivation_tools(tmp_path)

    start = mcp.tools["derivation_start"]
    import_from_sympy = mcp.tools["derivation_import_from_sympy"]

    assert callable(start)
    assert callable(import_from_sympy)

    start(name="unicode_import_step")
    result = import_from_sympy(
        expression="β₀ * exp(-λ*t)",
        operation_performed="Imported Unicode-rich result",
        sympy_tool_used="introduce_expression",
    )

    assert result["success"] is True
    assert result["expression"] == "beta0*exp(-lambda*t)"
    assert r"\beta_{0}" in result["latex"]
    assert r"\lambda" in result["latex"]


def test_sympify_expression_normalizes_superscript_minus() -> None:
    """Superscript minus should be normalized before SymPy parsing."""
    result = derivation_tools._sympify_expression("dose⁻¹")

    assert str(result) == "1/dose"
