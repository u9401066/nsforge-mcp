"""
Calculation Tools - SIMPLIFIED

═══════════════════════════════════════════════════════════════════════════════
⚠️ IMPORTANT: Most calculation tools have been REMOVED.
   Use SymPy-MCP for symbolic calculations instead!
═══════════════════════════════════════════════════════════════════════════════

SymPy-MCP provides (use these for symbolic work):
- intro_many() / introduce_expression() - Define variables/expressions
- solve_algebraically() / solve_linear_system() - Solve equations
- differentiate_expression() / integrate_expression() - Calculus
- simplify_expression() / expand_expression() - Simplification
- dsolve_ode() / pdsolve_pde() - Differential equations
- print_latex_expression() - Display results to user ⬅️ CRITICAL!

This module only provides:
- evaluate_numeric: For final numeric evaluation (after symbolic work)
- symbolic_equal: Quick equivalence check (for verification)

═══════════════════════════════════════════════════════════════════════════════
CORRECT WORKFLOW:
1. SymPy-MCP: Do symbolic calculations
2. print_latex_expression(): Show formula to user for confirmation
3. NSForge: Store verified result (derivation_start → derivation_complete)
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# Standard transformations for parsing
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _parse_safe(expression: str) -> tuple[sp.Expr | None, str | None]:
    """Safely parse an expression, returning (expr, error)."""
    try:
        expr_clean = expression.replace("^", "**")
        return parse_expr(expr_clean, transformations=TRANSFORMATIONS), None
    except Exception as e:
        return None, str(e)


def register_calculate_tools(mcp) -> None:
    """Register calculation tools with MCP server.

    ⚠️ Most tools REMOVED - use SymPy-MCP for symbolic calculations!

    Remaining tools:
    - evaluate_numeric: Final numeric evaluation
    - symbolic_equal: Quick equivalence check
    """

    @mcp.tool()
    def evaluate_numeric(
        expression: str,
        values: dict[str, float | int],
        precision: int = 6,
    ) -> dict[str, Any]:
        """
        Evaluate expression numerically.

        ⚠️ USE AFTER SYMBOLIC WORK: This tool is for final numeric evaluation
        after you've done symbolic calculations with SymPy-MCP.

        Correct Workflow:
        1. Use SymPy-MCP for symbolic calculations (solve, simplify, etc.)
        2. Use print_latex_expression() to show result to user
        3. Use this tool for final numeric values

        Args:
            expression: Expression to evaluate
            values: Numeric values for all variables
            precision: Decimal precision

        Returns:
            Numeric result

        Examples:
            evaluate_numeric("sin(pi/4)", {}) → 0.707107
            evaluate_numeric("m * v**2 / 2", {"m": 70, "v": 10}) → 3500.0
        """
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}

        try:
            subs_dict = {sp.Symbol(k): v for k, v in values.items()}
            result = expr.subs(subs_dict)
            numeric = float(result.evalf(precision + 2))
            return {
                "success": True,
                "result": round(numeric, precision),
                "expression": expression,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def symbolic_equal(expr1: str, expr2: str) -> dict[str, Any]:
        """
        Check if two expressions are symbolically equivalent.

        Useful for quick verification of derivation steps.
        For more thorough verification, use verify.py tools.

        Args:
            expr1: First expression
            expr2: Second expression

        Returns:
            Whether expressions are equivalent

        Examples:
            symbolic_equal("(x+1)**2", "x**2 + 2*x + 1") → True
            symbolic_equal("sin(x)**2 + cos(x)**2", "1") → True
        """
        e1, err1 = _parse_safe(expr1)
        e2, err2 = _parse_safe(expr2)
        if err1 or err2:
            return {"success": False, "error": err1 or err2}

        try:
            diff = sp.simplify(e1 - e2)
            is_equal = diff == 0
            if not is_equal:
                diff = sp.trigsimp(e1 - e2)
                is_equal = diff == 0

            return {
                "success": True,
                "equivalent": is_equal,
                "expr1": str(e1),
                "expr2": str(e2),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
