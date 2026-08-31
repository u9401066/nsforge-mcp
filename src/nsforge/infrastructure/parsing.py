"""Shared no-eval parsing adapter used across the MCP and infrastructure layers."""

from __future__ import annotations

from typing import Any

from nsforge.domain.safe_parse import (
    ALLOWLIST_TRANSFORMATIONS,
    parse_expression_allowlisted,
)

# Backward-compatible public alias.  These are token-to-token transformations;
# expression construction is performed by the allowlisted AST walker, not eval.
SYMPY_PARSER_TRANSFORMATIONS = ALLOWLIST_TRANSFORMATIONS


def parse_expression_safe(
    expression: str,
    *,
    local_dict: dict[str, Any] | None = None,
    check_safety: bool = True,
    evaluate: bool = True,
) -> tuple[Any, str | None]:
    """Parse an expression string, returning ``(sympy expr | None, error | None)``.

    ``check_safety=False`` bypasses only complexity budgets for trusted persisted
    data; the structural allowlist is always enforced.  No mode executes input.
    """
    try:
        parsed = parse_expression_allowlisted(
            expression,
            local_dict=local_dict,
            evaluate=evaluate,
            check_complexity=check_safety,
        )
        return parsed, None
    except Exception as exc:
        return None, str(exc)
