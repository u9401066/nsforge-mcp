"""
Verification Tools

Tools for verifying mathematical derivations using:
- SymPy (symbolic verification)
- sympy.physics.units (dimensional analysis)
- Future: Lean4 formal verification
"""

from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _parse_safe(expression: str) -> tuple[Any, str | None]:
    """Safely parse expression."""
    try:
        expr_clean = expression.replace("^", "**")
        return parse_expr(expr_clean, transformations=TRANSFORMATIONS), None
    except Exception as e:
        return None, str(e)


def register_verify_tools(mcp: Any) -> None:
    """Register verification tools with MCP server."""

    @mcp.tool()
    def verify_equality(
        expression1: str,
        expression2: str,
    ) -> dict[str, Any]:
        """
        Verify that two expressions are symbolically equal.

        Args:
            expression1: First expression
            expression2: Second expression

        Returns:
            Verification result

        Examples:
            verify_equality("(x+1)**2", "x**2 + 2*x + 1") → verified: True
            verify_equality("sin(x)**2 + cos(x)**2", "1") → verified: True
        """
        e1, err1 = _parse_safe(expression1)
        e2, err2 = _parse_safe(expression2)

        if err1 or err2:
            return {"verified": False, "error": err1 or err2}

        try:
            diff = sp.simplify(e1 - e2)
            is_equal = diff == 0

            if not is_equal:
                diff = sp.trigsimp(e1 - e2)
                is_equal = diff == 0

            return {
                "verified": is_equal,
                "expression1": str(e1),
                "expression2": str(e2),
                "message": "Expressions are equal" if is_equal else f"Difference: {diff}",
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    @mcp.tool()
    def verify_derivative(
        function: str,
        claimed_derivative: str,
        variable: str = "x",
    ) -> dict[str, Any]:
        """
        Verify a derivative by computing and comparing.

        Args:
            function: Original function
            claimed_derivative: Claimed derivative
            variable: Variable (default: "x")

        Returns:
            Verification result

        Examples:
            verify_derivative("x**3", "3*x**2") → verified: True
        """
        func_expr, err1 = _parse_safe(function)
        claimed_expr, err2 = _parse_safe(claimed_derivative)

        if err1 or err2:
            return {"verified": False, "error": err1 or err2}

        try:
            var_sym = sp.Symbol(variable)
            actual = sp.diff(func_expr, var_sym)
            diff = sp.simplify(actual - claimed_expr)
            is_equal = diff == 0

            return {
                "verified": is_equal,
                "function": function,
                "claimed": claimed_derivative,
                "actual": str(actual),
                "message": "Derivative correct" if is_equal else f"Expected: {actual}",
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    @mcp.tool()
    def verify_integral(
        integrand: str,
        claimed_integral: str,
        variable: str = "x",
    ) -> dict[str, Any]:
        """
        Verify an integral by differentiating the result.

        Args:
            integrand: Original function to integrate
            claimed_integral: Claimed integral result
            variable: Variable (default: "x")

        Returns:
            Verification result

        Examples:
            verify_integral("x**2", "x**3/3") → verified: True
        """
        integrand_expr, err1 = _parse_safe(integrand)
        integral_expr, err2 = _parse_safe(claimed_integral)

        if err1 or err2:
            return {"verified": False, "error": err1 or err2}

        try:
            var_sym = sp.Symbol(variable)
            # Differentiate claimed integral
            derivative = sp.diff(integral_expr, var_sym)
            diff = sp.simplify(derivative - integrand_expr)
            is_equal = diff == 0

            return {
                "verified": is_equal,
                "integrand": integrand,
                "claimed_integral": claimed_integral,
                "derivative_check": str(derivative),
                "message": "Integral correct" if is_equal else f"d/d{variable} gives: {derivative}",
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    @mcp.tool()
    def verify_solution(
        equation: str,
        solution: str,
        variable: str = "x",
    ) -> dict[str, Any]:
        """
        Verify that a value satisfies an equation.

        Args:
            equation: Equation ("lhs = rhs" or "expr" for expr = 0)
            solution: Claimed solution
            variable: Variable (default: "x")

        Returns:
            Verification result

        Examples:
            verify_solution("x**2 - 4 = 0", "2") → verified: True
        """
        # Parse equation
        if "=" in equation:
            parts = equation.split("=", 1)
            lhs, _ = _parse_safe(parts[0].strip())
            rhs, _ = _parse_safe(parts[1].strip())
            eq_expr = lhs - rhs
        else:
            eq_expr, error = _parse_safe(equation)
            if error:
                return {"verified": False, "error": error}

        sol_expr, sol_err = _parse_safe(solution)
        if sol_err:
            return {"verified": False, "error": sol_err}

        try:
            var_sym = sp.Symbol(variable)
            result = eq_expr.subs(var_sym, sol_expr)
            result = sp.simplify(result)
            is_zero = result == 0

            return {
                "verified": is_zero,
                "equation": equation,
                "solution": solution,
                "substituted": str(result),
                "message": f"{variable}={solution} is valid" if is_zero else f"Result: {result} ≠ 0",
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    @mcp.tool()
    def check_dimensions(
        expression: str,
        units_map: dict[str, str],
    ) -> dict[str, Any]:
        """
        Check dimensional consistency of an expression.

        Uses sympy.physics.units for dimensional analysis.

        Args:
            expression: Expression to check
            units_map: Map of symbol to SI unit string
                       e.g., {"v": "m/s", "m": "kg", "F": "N"}

        Returns:
            Dimensional analysis result

        Examples:
            check_dimensions("F", {"F": "kg*m/s**2"})
            → dimension: [mass]*[length]/[time]**2

            check_dimensions("m*a", {"m": "kg", "a": "m/s**2"})
            → dimension: [mass]*[length]/[time]**2 (Force)
        """
        from sympy.physics import units as u
        from sympy.physics.units.systems import SI

        expr, error = _parse_safe(expression)
        if error:
            return {"success": False, "error": error}

        try:
            # Map unit strings to sympy units
            unit_mapping = {
                "m": u.meter, "kg": u.kilogram, "s": u.second,
                "N": u.newton, "J": u.joule, "W": u.watt,
                "Pa": u.pascal, "K": u.kelvin, "A": u.ampere,
                "V": u.volt, "Hz": u.hertz, "rad": u.radian,
            }

            # Build substitution with units
            subs = {}
            for sym_name, unit_str in units_map.items():
                sym = sp.Symbol(sym_name)
                # Parse unit expression
                unit_expr = parse_expr(
                    unit_str,
                    local_dict=unit_mapping,
                    transformations=TRANSFORMATIONS,
                )
                subs[sym] = unit_expr

            # Substitute units
            expr_with_units = expr.subs(subs)

            # Get dimension
            try:
                dim = SI.get_dimensional_expr(expr_with_units)
                dim_str = str(dim)
            except Exception:
                dim_str = str(expr_with_units)

            return {
                "success": True,
                "expression": expression,
                "dimension": dim_str,
                "units_applied": units_map,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def reverse_verify(
        result_expr: str,
        original_expr: str,
        operation: str,
        variable: str = "x",
    ) -> dict[str, Any]:
        """
        Verify a result by applying the reverse operation.

        This is a key verification method:
        - Derivative → integrate back
        - Integral → differentiate back
        - Solve → substitute back

        Args:
            result_expr: The computed result
            original_expr: The original expression
            operation: "differentiate", "integrate", or "solve"
            variable: Variable involved

        Returns:
            Verification result

        Examples:
            reverse_verify("3*x**2", "x**3", "differentiate")
            → Integrates 3*x² and checks if it gives x³

            reverse_verify("x**3/3", "x**2", "integrate")
            → Differentiates x³/3 and checks if it gives x²
        """
        result, err1 = _parse_safe(result_expr)
        original, err2 = _parse_safe(original_expr)

        if err1 or err2:
            return {"verified": False, "error": err1 or err2}

        try:
            var_sym = sp.Symbol(variable)

            if operation == "differentiate":
                # Reverse: integrate the derivative
                reversed_result = sp.integrate(result, var_sym)
                # Check if differs only by constant
                diff = sp.simplify(reversed_result - original)
                # If diff is constant (no var_sym), it's correct
                is_valid = var_sym not in diff.free_symbols

            elif operation == "integrate":
                # Reverse: differentiate the integral
                reversed_result = sp.diff(result, var_sym)
                diff = sp.simplify(reversed_result - original)
                is_valid = diff == 0

            elif operation == "solve":
                # Reverse: substitute solution back
                # original should be equation, result is solution
                substituted = original.subs(var_sym, result)
                substituted = sp.simplify(substituted)
                is_valid = substituted == 0
                reversed_result = substituted

            else:
                return {"verified": False, "error": f"Unknown operation: {operation}"}

            return {
                "verified": is_valid,
                "operation": operation,
                "result": result_expr,
                "original": original_expr,
                "reverse_check": str(reversed_result),
                "message": "Reverse verification passed" if is_valid else "Reverse verification failed",
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}
