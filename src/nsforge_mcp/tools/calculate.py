"""
Calculation Tools

Pure symbolic calculation tools using SymPy.
No hard-coded formulas - all expressions come from User/Agent.
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
    """Register calculation tools with MCP server."""

    @mcp.tool()
    def simplify(
        expression: str,
        strategy: str = "basic",
    ) -> dict[str, Any]:
        """
        Simplify a mathematical expression using SymPy.

        Args:
            expression: Expression to simplify
            strategy: "basic", "full", "trig", "radical"

        Returns:
            Simplified expression with LaTeX

        Examples:
            simplify("x**2 + 2*x + 1") → "(x + 1)**2"
            simplify("sin(x)**2 + cos(x)**2", strategy="trig") → "1"
        """
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}

        try:
            if strategy in ("trigonometric", "trig"):
                result = sp.trigsimp(expr)
            elif strategy == "radical":
                result = sp.radsimp(expr)
            elif strategy == "full":
                result = sp.simplify(expr, full=True)
            else:
                result = sp.simplify(expr)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def substitute(
        expression: str,
        values: dict[str, str | int | float],
        simplify_result: bool = True,
    ) -> dict[str, Any]:
        """
        Substitute values into an expression.

        Core tool for derivation steps - values can be symbolic or numeric.

        Args:
            expression: Expression with variables
            values: Substitutions (e.g., {"a": "F/m"} or {"x": 5})
            simplify_result: Whether to simplify after substitution

        Returns:
            Expression after substitution

        Examples:
            substitute("Delta_v * sqrt(m/k)", {"Delta_v": "M2*v/(M1+M2)"})
            → "M2*v*sqrt(m/k)/(M1 + M2)"
        """
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": f"Parse error: {error}"}

        try:
            subs_dict = {}
            for var, val in values.items():
                var_sym = sp.Symbol(var)
                if isinstance(val, str):
                    val_expr, val_err = _parse_safe(val)
                    if val_err:
                        return {"success": False, "error": f"Parse error for '{var}': {val_err}"}
                    subs_dict[var_sym] = val_expr
                else:
                    subs_dict[var_sym] = val

            result = expr.subs(subs_dict)
            if simplify_result:
                result = sp.simplify(result)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def solve(
        equation: str,
        variable: str,
        domain: str = "complex",
    ) -> dict[str, Any]:
        """
        Solve an equation for a variable using SymPy.

        Args:
            equation: "lhs = rhs" or "expr" (treated as expr = 0)
            variable: Variable to solve for
            domain: "complex", "real", or "positive"

        Returns:
            List of solutions

        Examples:
            solve("m1*v1 = (m1+m2)*v_f", "v_f")
            → ["m1*v1/(m1 + m2)"]
        """
        try:
            if "=" in equation:
                parts = equation.split("=", 1)
                lhs, _ = _parse_safe(parts[0].strip())
                rhs, _ = _parse_safe(parts[1].strip())
                eq_expr = lhs - rhs
            else:
                eq_expr, error = _parse_safe(equation)
                if error:
                    return {"success": False, "error": error}

            var_sym = sp.Symbol(variable)

            if domain == "real":
                solutions = sp.solveset(eq_expr, var_sym, domain=sp.S.Reals)
            elif domain == "positive":
                solutions = sp.solveset(eq_expr, var_sym, domain=sp.Interval(0, sp.oo, left_open=True))
            else:
                solutions = sp.solve(eq_expr, var_sym)

            # Convert to list
            if isinstance(solutions, sp.Set):
                sol_list = list(solutions) if solutions.is_FiniteSet else [solutions]
            else:
                sol_list = solutions if isinstance(solutions, list) else [solutions]

            return {
                "success": True,
                "variable": variable,
                "solutions": [{"result": str(s), "latex": sp.latex(s)} for s in sol_list],
                "count": len(sol_list),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def differentiate(
        expression: str,
        variable: str,
        order: int = 1,
    ) -> dict[str, Any]:
        """
        Differentiate an expression using SymPy.

        Args:
            expression: Expression to differentiate
            variable: Variable to differentiate with respect to
            order: Derivative order (default: 1)

        Returns:
            Derivative expression

        Examples:
            differentiate("x**3 + 2*x", "x") → "3*x**2 + 2"
            differentiate("sin(x)", "x", order=2) → "-sin(x)"
        """
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}

        try:
            var_sym = sp.Symbol(variable)
            result = sp.diff(expr, var_sym, order)
            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "operation": f"d^{order}/d{variable}^{order}" if order > 1 else f"d/d{variable}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def integrate(
        expression: str,
        variable: str,
        lower_bound: str | None = None,
        upper_bound: str | None = None,
    ) -> dict[str, Any]:
        """
        Integrate an expression using SymPy.

        Args:
            expression: Expression to integrate
            variable: Integration variable
            lower_bound: Lower limit (for definite integral)
            upper_bound: Upper limit (for definite integral)

        Returns:
            Integral result

        Examples:
            integrate("x**2", "x") → "x**3/3"
            integrate("x**2", "x", "0", "1") → "1/3"
        """
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}

        try:
            var_sym = sp.Symbol(variable)

            if lower_bound and upper_bound:
                lb, _ = _parse_safe(lower_bound)
                ub, _ = _parse_safe(upper_bound)
                result = sp.integrate(expr, (var_sym, lb, ub))
                is_definite = True
            else:
                result = sp.integrate(expr, var_sym)
                is_definite = False

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "definite": is_definite,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def expand(expression: str) -> dict[str, Any]:
        """Expand an expression (distribute products)."""
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}
        try:
            result = sp.expand(expr)
            return {"success": True, "result": str(result), "latex": sp.latex(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def factor(expression: str) -> dict[str, Any]:
        """Factor an expression."""
        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}
        try:
            result = sp.factor(expr)
            return {"success": True, "result": str(result), "latex": sp.latex(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def evaluate_numeric(
        expression: str,
        values: dict[str, float | int],
        precision: int = 6,
    ) -> dict[str, Any]:
        """
        Evaluate expression numerically.

        Args:
            expression: Expression to evaluate
            values: Numeric values for all variables
            precision: Decimal precision

        Returns:
            Numeric result
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

        Useful for verifying derivation steps.
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
