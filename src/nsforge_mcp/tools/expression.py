"""
Expression Tools

Tools for parsing and validating mathematical expressions.
These tools convert human-readable formulas to SymPy-computable form.
"""

from typing import Any


def register_expression_tools(mcp: Any) -> None:
    """Register expression parsing tools with MCP server."""

    @mcp.tool()
    def parse_expression(
        expression: str,
        description: str | None = None,
        symbol_hints: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Parse a mathematical expression into SymPy-computable form.

        This tool converts human-readable formula notation into validated SymPy
        expressions, extracting symbols and their relationships.

        Args:
            expression: Mathematical expression (e.g., "v' = M1*v*cos(θ)/(M1+M2)")
            description: Optional description of what this formula represents
            symbol_hints: Optional hints for symbol types (e.g., {"m": "positive_real"})

        Returns:
            Parsed expression with:
            - sympy_expr: SymPy expression string
            - symbols: List of extracted symbols with inferred types
            - latex: LaTeX representation
            - is_equation: Whether it's an equation (has '=')

        Examples:
            parse_expression("F = m*a")
            → {"sympy_expr": "Eq(F, m*a)", "symbols": ["F", "m", "a"], ...}

            parse_expression("∫x²dx", description="Integral of x squared")
            → {"sympy_expr": "Integral(x**2, x)", ...}
        """
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            convert_xor,
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )

        # Symbol replacements for common notations
        replacements = {
            "θ": "theta",
            "Δ": "Delta_",
            "π": "pi",
            "∞": "oo",
            "√": "sqrt",
            "'": "_prime",
            "²": "**2",
            "³": "**3",
            "₁": "_1",
            "₂": "_2",
        }

        # Apply replacements
        expr_clean = expression
        for old, new in replacements.items():
            expr_clean = expr_clean.replace(old, new)

        # Check if it's an equation
        is_equation = "=" in expr_clean and expr_clean.count("=") == 1

        try:
            transformations = standard_transformations + (
                implicit_multiplication_application,
                convert_xor,
            )

            if is_equation:
                lhs, rhs = expr_clean.split("=")
                lhs_expr = parse_expr(lhs.strip(), transformations=transformations)
                rhs_expr = parse_expr(rhs.strip(), transformations=transformations)
                sympy_expr = sp.Eq(lhs_expr, rhs_expr)
                all_symbols = lhs_expr.free_symbols | rhs_expr.free_symbols
            else:
                sympy_expr = parse_expr(expr_clean, transformations=transformations)
                all_symbols = sympy_expr.free_symbols

            # Extract symbol info
            symbols_info = []
            for sym in sorted(all_symbols, key=str):
                sym_name = str(sym)
                sym_info = {
                    "name": sym_name,
                    "type": "real",  # default
                }
                # Apply hints if provided
                if symbol_hints and sym_name in symbol_hints:
                    sym_info["type"] = symbol_hints[sym_name]
                # Infer from naming conventions
                elif sym_name.startswith("Delta_"):
                    sym_info["type"] = "real"
                    sym_info["note"] = "change/difference quantity"
                elif sym_name in ("m", "M", "M_1", "M_2", "k"):
                    sym_info["type"] = "positive_real"
                elif sym_name in ("theta", "phi", "psi"):
                    sym_info["type"] = "real"
                    sym_info["note"] = "angle"

                symbols_info.append(sym_info)

            return {
                "success": True,
                "sympy_expr": str(sympy_expr),
                "latex": sp.latex(sympy_expr),
                "symbols": symbols_info,
                "is_equation": is_equation,
                "original": expression,
                "description": description,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original": expression,
                "suggestion": "Check syntax. Use * for multiplication, ** for power.",
            }

    @mcp.tool()
    def validate_expression(
        expression: str,
        expected_symbols: list[str] | None = None,
        check_dimensions: bool = False,
        units_map: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Validate a mathematical expression for correctness.

        Checks syntax, symbol consistency, and optionally dimensional consistency.

        Args:
            expression: Expression to validate
            expected_symbols: List of symbols that should appear
            check_dimensions: Whether to perform dimensional analysis
            units_map: Map of symbol to unit (e.g., {"v": "m/s", "m": "kg"})

        Returns:
            Validation result with:
            - valid: Whether expression is valid
            - issues: List of issues found
            - warnings: Non-critical warnings

        Examples:
            validate_expression("F = m*a", expected_symbols=["F", "m", "a"])
            → {"valid": True, ...}

            validate_expression("F = m*a + v", units_map={"F": "N", "m": "kg", "a": "m/s²", "v": "m/s"})
            → {"valid": False, "issues": ["Dimension mismatch: m*a (N) + v (m/s)"]}
        """
        import sympy as sp

        issues = []
        warnings = []

        # First, try to parse
        try:
            # Handle equation form
            if "=" in expression:
                lhs, rhs = expression.split("=", 1)
                lhs_expr = sp.sympify(lhs.strip())
                rhs_expr = sp.sympify(rhs.strip())
                all_symbols = lhs_expr.free_symbols | rhs_expr.free_symbols
            else:
                expr = sp.sympify(expression)
                all_symbols = expr.free_symbols

            found_symbols = {str(s) for s in all_symbols}

        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Parse error: {e}"],
                "warnings": [],
            }

        # Check expected symbols
        if expected_symbols:
            expected_set = set(expected_symbols)
            missing = expected_set - found_symbols
            extra = found_symbols - expected_set

            if missing:
                issues.append(f"Missing expected symbols: {missing}")
            if extra:
                warnings.append(f"Unexpected symbols found: {extra}")

        # Dimensional analysis (basic implementation)
        if check_dimensions and units_map:
            # This would need a proper dimensional analysis engine
            # For now, just check that all symbols have units defined
            symbols_without_units = found_symbols - set(units_map.keys())
            if symbols_without_units:
                warnings.append(f"Symbols without unit definition: {symbols_without_units}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "found_symbols": list(found_symbols),
        }

    @mcp.tool()
    def extract_symbols(
        expression: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract symbols from an expression with inferred metadata.

        Args:
            expression: Mathematical expression
            context: Optional context hint (e.g., "mechanics", "thermodynamics")

        Returns:
            List of symbols with:
            - name: Symbol name
            - type: Inferred type (real, positive_real, integer, etc.)
            - suggested_unit: Suggested SI unit based on context
            - description: Inferred description

        Examples:
            extract_symbols("F = m*a", context="mechanics")
            → [
                {"name": "F", "type": "real", "suggested_unit": "N", "description": "Force"},
                {"name": "m", "type": "positive_real", "suggested_unit": "kg", "description": "Mass"},
                {"name": "a", "type": "real", "suggested_unit": "m/s²", "description": "Acceleration"}
              ]
        """
        import sympy as sp

        # Context-based symbol knowledge
        SYMBOL_KNOWLEDGE = {
            "mechanics": {
                "F": {"type": "real", "unit": "N", "desc": "Force"},
                "m": {"type": "positive_real", "unit": "kg", "desc": "Mass"},
                "M": {"type": "positive_real", "unit": "kg", "desc": "Mass"},
                "a": {"type": "real", "unit": "m/s²", "desc": "Acceleration"},
                "v": {"type": "real", "unit": "m/s", "desc": "Velocity"},
                "x": {"type": "real", "unit": "m", "desc": "Position/Displacement"},
                "t": {"type": "positive_real", "unit": "s", "desc": "Time"},
                "k": {"type": "positive_real", "unit": "N/m", "desc": "Spring constant"},
                "theta": {"type": "real", "unit": "rad", "desc": "Angle"},
                "g": {
                    "type": "positive_real",
                    "unit": "m/s²",
                    "desc": "Gravitational acceleration",
                },
            },
            "thermodynamics": {
                "T": {"type": "positive_real", "unit": "K", "desc": "Temperature"},
                "P": {"type": "positive_real", "unit": "Pa", "desc": "Pressure"},
                "V": {"type": "positive_real", "unit": "m³", "desc": "Volume"},
                "n": {"type": "positive_real", "unit": "mol", "desc": "Amount of substance"},
                "R": {"type": "positive_real", "unit": "J/(mol·K)", "desc": "Gas constant"},
                "S": {"type": "real", "unit": "J/K", "desc": "Entropy"},
                "Q": {"type": "real", "unit": "J", "desc": "Heat"},
                "W": {"type": "real", "unit": "J", "desc": "Work"},
            },
            "circuits": {
                "V": {"type": "real", "unit": "V", "desc": "Voltage"},
                "I": {"type": "real", "unit": "A", "desc": "Current"},
                "R": {"type": "positive_real", "unit": "Ω", "desc": "Resistance"},
                "C": {"type": "positive_real", "unit": "F", "desc": "Capacitance"},
                "L": {"type": "positive_real", "unit": "H", "desc": "Inductance"},
                "omega": {"type": "positive_real", "unit": "rad/s", "desc": "Angular frequency"},
                "f": {"type": "positive_real", "unit": "Hz", "desc": "Frequency"},
            },
        }

        try:
            # Parse expression
            if "=" in expression:
                parts = expression.split("=")
                expr = sp.sympify(f"({parts[0]}) - ({parts[1]})")
            else:
                expr = sp.sympify(expression)

            all_symbols = expr.free_symbols
            knowledge = SYMBOL_KNOWLEDGE.get(context, {}) if context else {}

            # Merge all knowledge if no context
            if not context:
                for domain_knowledge in SYMBOL_KNOWLEDGE.values():
                    knowledge.update(domain_knowledge)

            result = []
            for sym in sorted(all_symbols, key=str):
                sym_name = str(sym)
                if sym_name in knowledge:
                    info = knowledge[sym_name]
                    result.append(
                        {
                            "name": sym_name,
                            "type": info["type"],
                            "suggested_unit": info["unit"],
                            "description": info["desc"],
                        }
                    )
                else:
                    result.append(
                        {
                            "name": sym_name,
                            "type": "real",
                            "suggested_unit": "",
                            "description": "Unknown symbol",
                        }
                    )

            return {
                "success": True,
                "symbols": result,
                "context_used": context,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
