"""
Shared SymPy parsing helpers — the single source of truth for the parser
transformations and the guarded parse wrapper used across the tool layer.

Consolidates what were seven near-identical ``TRANSFORMATIONS`` definitions and
three ``_parse_safe`` helpers, and closes a gap where some tools parsed
caller-supplied expressions without the untrusted-input safety guard.
"""

from __future__ import annotations

from typing import Any

from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from nsforge.domain.safe_parse import check_expression_safety

# The one parser configuration every tool should use.
SYMPY_PARSER_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def parse_expression_safe(
    expression: str,
    *,
    local_dict: dict[str, Any] | None = None,
    check_safety: bool = True,
) -> tuple[Any, str | None]:
    """Parse an expression string, returning ``(sympy expr | None, error | None)``.

    Applies the untrusted-input safety guard before parsing (unless disabled),
    normalises ``^`` to ``**``, optionally injects ``local_dict`` symbols, and
    reports any parse error as a string. This is the single place tool code should
    parse caller-supplied expressions.
    """
    if check_safety:
        unsafe = check_expression_safety(expression)
        if unsafe:
            return None, unsafe
    try:
        parsed = parse_expr(
            expression.replace("^", "**"),
            local_dict=local_dict,
            transformations=SYMPY_PARSER_TRANSFORMATIONS,
        )
        return parsed, None
    except Exception as exc:
        return None, str(exc)
