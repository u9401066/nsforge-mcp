"""Pure, injection-safe Python rendering for the ALGORITHM rung.

Generated source is executable, so verified mathematics alone is not a sufficient
trust boundary: names, annotations, prose, and expression strings must also be
rendered as data.  This module validates identifiers and types, canonicalises
expressions through NSForge's no-eval parser, and emits comments/docstrings with
newlines escaped before assembling source deterministically.
"""

from __future__ import annotations

import ast
import keyword

import sympy as sp

from nsforge.domain.safe_parse import (
    ALLOWED_CONSTANT_NAMES,
    ALLOWED_FUNCTION_NAMES,
    parse_expression_allowlisted,
)

_ALLOWED_PARAMETER_TYPES = frozenset({"bool", "complex", "float", "int", "str"})
_SYMBOLIC_FUNCTION_NAMES = frozenset({"f", "g", "h"})
_SYMPY_NAMES = (ALLOWED_FUNCTION_NAMES - _SYMBOLIC_FUNCTION_NAMES) | (
    ALLOWED_CONSTANT_NAMES - {"True", "False"}
)


class UnsafeCodegenInput(ValueError):
    """Raised when caller data cannot be represented as safe Python source."""


def validate_python_identifier(value: object, *, field: str) -> str:
    """Return one non-keyword, non-dunder Python identifier."""
    if (
        not isinstance(value, str)
        or not value.isidentifier()
        or keyword.iskeyword(value)
        or value.startswith("__")
    ):
        raise UnsafeCodegenInput(f"{field} must be a safe Python identifier")
    return value


def safe_python_comment(value: object) -> str:
    """Collapse untrusted prose to one inert comment line."""
    if not isinstance(value, str):
        raise UnsafeCodegenInput("comment text must be a string")
    return " ".join(value.splitlines()).replace("\x00", "")


class _PrefixSymPyNames(ast.NodeTransformer):
    """Make canonical SymPy functions/constants explicit module attributes."""

    def __init__(self, symbol_names: frozenset[str]) -> None:
        self.symbol_names = symbol_names
        super().__init__()

    def visit_Call(self, node: ast.Call) -> ast.expr:  # noqa: N802 - AST visitor API
        visited = self.generic_visit(node)
        assert isinstance(visited, ast.Call)
        if isinstance(visited.func, ast.Name) and visited.func.id in _SYMBOLIC_FUNCTION_NAMES:
            symbolic_constructor = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="sp", ctx=ast.Load()),
                    attr="Function",
                    ctx=ast.Load(),
                ),
                args=[ast.Constant(visited.func.id)],
                keywords=[],
            )
            return ast.copy_location(
                ast.Call(func=symbolic_constructor, args=visited.args, keywords=[]),
                visited,
            )
        return visited

    def visit_Name(self, node: ast.Name) -> ast.expr:  # noqa: N802 - AST visitor API
        if node.id in _SYMPY_NAMES and node.id not in self.symbol_names:
            return ast.copy_location(
                ast.Attribute(value=ast.Name(id="sp", ctx=ast.Load()), attr=node.id, ctx=node.ctx),
                node,
            )
        return node


def canonical_python_expression(value: object, *, field: str) -> str:
    """Return safe Python source for one allowlisted mathematical expression."""
    if not isinstance(value, str):
        raise UnsafeCodegenInput(f"{field} must be a mathematical expression string")
    try:
        parsed = parse_expression_allowlisted(value)
    except ValueError as exc:
        raise UnsafeCodegenInput(f"unsafe {field}: {exc}") from exc
    tree = ast.parse(str(parsed), mode="eval")
    symbol_names = frozenset(str(symbol) for symbol in getattr(parsed, "free_symbols", ()))
    tree = ast.fix_missing_locations(_PrefixSymPyNames(symbol_names).visit(tree))
    return ast.unparse(tree.body)


def python_expression_symbols(value: object, *, field: str) -> frozenset[str]:
    """Return free-symbol names from the same safe parse used for rendering."""
    if not isinstance(value, str):
        raise UnsafeCodegenInput(f"{field} must be a mathematical expression string")
    try:
        parsed = parse_expression_allowlisted(value)
    except ValueError as exc:
        raise UnsafeCodegenInput(f"unsafe {field}: {exc}") from exc
    if not isinstance(parsed, sp.Basic):
        raise UnsafeCodegenInput(f"{field} must produce a SymPy expression")
    return frozenset(str(symbol) for symbol in parsed.free_symbols)


def _parameter_type(value: object, *, field: str) -> str:
    resolved = "float" if value is None else value
    if not isinstance(resolved, str) or resolved not in _ALLOWED_PARAMETER_TYPES:
        allowed = ", ".join(sorted(_ALLOWED_PARAMETER_TYPES))
        raise UnsafeCodegenInput(f"{field} must be one of: {allowed}")
    return resolved


def _validated_parameters(parameters: list[dict[str, str]]) -> list[dict[str, str]]:
    validated: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, parameter in enumerate(parameters):
        name = validate_python_identifier(parameter.get("name"), field=f"parameters[{index}].name")
        if name == "sp" or name in seen:
            raise UnsafeCodegenInput(f"duplicate or reserved parameter name: {name}")
        seen.add(name)
        validated.append(
            {
                "name": name,
                "type": _parameter_type(
                    parameter.get("type", "float"), field=f"parameters[{index}].type"
                ),
                "description": safe_python_comment(parameter.get("description", "")),
            }
        )
    return validated


def _validated_steps(steps: list[dict[str, str]]) -> list[dict[str, str]]:
    validated: list[dict[str, str]] = []
    for index, step in enumerate(steps):
        validated.append(
            {
                "description": safe_python_comment(step.get("description", "")),
                "expression": canonical_python_expression(
                    step.get("expression"), field=f"steps[{index}].expression"
                ),
                "result_var": validate_python_identifier(
                    step.get("result_var"), field=f"steps[{index}].result_var"
                ),
            }
        )
    return validated


def render_python_function(
    name: str,
    description: str,
    parameters: list[dict[str, str]],
    steps: list[dict[str, str]],
    return_vars: list[str],
) -> str:
    """Assemble deterministic Python without allowing metadata/source injection."""
    function_name = validate_python_identifier(name, field="name")
    safe_parameters = _validated_parameters(parameters)
    safe_steps = _validated_steps(steps)
    safe_returns = [
        validate_python_identifier(value, field=f"return_vars[{index}]")
        for index, value in enumerate(return_vars)
    ]
    if len(set(safe_returns)) != len(safe_returns):
        raise UnsafeCodegenInput("return_vars must not contain duplicates")
    available = {item["name"] for item in safe_parameters} | {
        item["result_var"] for item in safe_steps
    }
    missing = sorted(set(safe_returns) - available)
    if missing:
        raise UnsafeCodegenInput(f"return_vars are not parameters or generated results: {missing}")

    param_str = ", ".join(f"{item['name']}: {item['type']}" for item in safe_parameters)
    doc_lines = [safe_python_comment(description), "", "Args:"]
    for parameter in safe_parameters:
        doc_lines.append(f"    {parameter['name']}: {parameter['description']}")
    doc_lines += [
        "",
        "Returns:",
        f"    dict with keys: {safe_returns}",
        "",
        "Note:",
        "    Generated by NSForge from a verification-gated derivation.",
    ]
    docstring = f"    {chr(10).join(doc_lines)!r}"

    body_lines = ["    import sympy as sp", ""]
    for index, step in enumerate(safe_steps, 1):
        body_lines.append(f"    # Step {index}: {step['description']}")
        body_lines.append(f"    {step['result_var']} = {step['expression']}")
        body_lines.append("")
    return_dict = ", ".join(f"{value!r}: {value}" for value in safe_returns)
    body_lines.append(f"    return {{{return_dict}}}")
    source = f"def {function_name}({param_str}):\n{docstring}\n{chr(10).join(body_lines)}\n"

    # A final structural parse is a cheap invariant: the renderer never returns
    # malformed source, even if future formatting code changes.
    try:
        ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover - guarded by component validation
        raise UnsafeCodegenInput(f"renderer produced invalid Python: {exc.msg}") from exc
    return source
