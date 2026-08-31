"""Executable renderers keep caller metadata and expressions out of Python syntax."""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any

import pytest
import sympy as sp

from nsforge.domain.codegen import UnsafeCodegenInput, render_python_function
from nsforge_mcp.tools.codegen import register_codegen_tools


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., dict[str, Any]]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _assigned_names(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def test_domain_renderer_escapes_multiline_prose_and_canonicalizes_math() -> None:
    source = render_python_function(
        "safe_function",
        "trusted description\n    injected = 7",
        [{"name": "x", "type": "float", "description": "input\n    injected = 8"}],
        [
            {
                "description": "calculation\n    injected = 9",
                "expression": "sin(x) + 1",
                "result_var": "y",
            }
        ],
        ["y"],
    )

    assert "injected" not in _assigned_names(source)
    assert "y" in _assigned_names(source)
    assert "sp.sin(x)" in source


def test_domain_renderer_materializes_allowlisted_symbolic_functions() -> None:
    source = render_python_function(
        "symbolic_function",
        "evaluate a symbolic function",
        [{"name": "x", "type": "float"}],
        [{"description": "apply f", "expression": "f(x) + sin(x)", "result_var": "y"}],
        ["y"],
    )
    namespace: dict[str, Any] = {}
    exec(source, namespace)  # noqa: S102 - source is produced by the renderer under test
    x = sp.Symbol("x")

    result = namespace["symbolic_function"](x)

    assert result["y"] == sp.Function("f")(x) + sp.sin(x)


def test_domain_renderer_preserves_gamma_and_beta_as_free_symbols() -> None:
    source = render_python_function(
        "reserved_symbol_names",
        "preserve ambiguous scientific symbols",
        [
            {"name": "gamma", "type": "float"},
            {"name": "beta", "type": "float"},
        ],
        [{"description": "sum symbols", "expression": "gamma + beta", "result_var": "y"}],
        ["y"],
    )
    namespace: dict[str, Any] = {}
    exec(source, namespace)  # noqa: S102 - source is produced by the renderer under test

    result = namespace["reserved_symbol_names"](gamma=1.0, beta=2.0)

    assert result["y"] == 3.0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("name", "safe):\n    injected = 1\n#"),
        ("parameter", "x: float = 7"),
        ("type", "float = 7"),
        ("expression", "x\ninjected = 7"),
        ("result", "y; injected = 7"),
        ("return", "y; injected = 7"),
    ),
)
def test_domain_renderer_rejects_source_shaped_fields(field: str, value: str) -> None:
    name = value if field == "name" else "safe_function"
    parameter_name = value if field == "parameter" else "x"
    parameter_type = value if field == "type" else "float"
    expression = value if field == "expression" else "x + 1"
    result_var = value if field == "result" else "y"
    return_var = value if field == "return" else "y"

    with pytest.raises(UnsafeCodegenInput):
        render_python_function(
            name,
            "safe",
            [{"name": parameter_name, "type": parameter_type}],
            [{"description": "safe", "expression": expression, "result_var": result_var}],
            [return_var],
        )


def test_legacy_python_tool_uses_the_same_safe_renderer() -> None:
    mcp = _FakeMCP()
    register_codegen_tools(mcp)
    result = mcp.tools["generate_python_function"](
        name="legacy_safe",
        description="description\n    injected = 7",
        parameters=[{"name": "x", "type": "float", "description": "input"}],
        steps=[
            {
                "description": "step\n    injected = 8",
                "expression": "sqrt(x)",
                "result_var": "y",
            }
        ],
        return_vars=["y"],
    )
    rejected = mcp.tools["generate_python_function"](
        name="legacy_bad",
        description="bad",
        parameters=[{"name": "x", "type": "float"}],
        steps=[{"description": "bad", "expression": "x\ninjected = 1", "result_var": "y"}],
        return_vars=["y"],
    )

    assert result["success"] is True
    assert "injected" not in _assigned_names(result["code"])
    assert rejected["success"] is False


def test_sympy_script_validates_names_expressions_operations_and_comments() -> None:
    mcp = _FakeMCP()
    register_codegen_tools(mcp)
    generated = mcp.tools["generate_sympy_script"](
        expressions=[
            {
                "name": "momentum",
                "expr": "m*v",
                "description": "safe comment\ninjected = 7",
            }
        ],
        operations=[{"op": "diff", "input": "momentum", "var": "v"}],
    )
    rejected = mcp.tools["generate_sympy_script"](
        expressions=[{"name": "bad\ninjected", "expr": "x", "description": "bad"}],
        operations=[],
    )

    assert generated["success"] is True
    assert "injected" not in _assigned_names(generated["script"])
    assert rejected["success"] is False
