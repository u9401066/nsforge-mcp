"""
Advanced Simplification Tools - Phase 1 Extensions

═══════════════════════════════════════════════════════════════════════════════
🎯 NSForge Phase 1: Advanced Algebraic Simplification
═══════════════════════════════════════════════════════════════════════════════

These tools provide FINE-GRAINED CONTROL over simplification, complementing
SymPy-MCP's generic `simplify_expression()` with specialized operations.

WHY NOT JUST USE `simplify()`?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- `simplify()` is a BLACK BOX: It applies heuristics and may or may not expand
- `expand()` is DETERMINISTIC: Always expands products and powers
- `factor()` is DETERMINISTIC: Always attempts factorization

Users need PRECISE CONTROL over transformation direction!

P0 - BASIC ALGEBRA (7 tools):
───────────────────────────────────────────────────────────────────────────────
1. expand_expression      - Expand products: (x+1)² → x²+2x+1
2. factor_expression      - Factorize: x²-1 → (x-1)(x+1)
3. collect_expression     - Collect terms: x²+2x+x → x²+3x
4. trigsimp_expression    - Trig simplify: sin²+cos² → 1
5. powsimp_expression     - Power simplify: x²·x³ → x⁵
6. radsimp_expression     - Radical simplify: 1/(√3+√2) → -√2+√3
7. combsimp_expression    - Combinatorial: n!/(n-2)! → n(n-1)

P1 - RATIONAL FUNCTIONS (3 tools):
───────────────────────────────────────────────────────────────────────────────
8. apart_expression       - Partial fractions: 1/(x²-1) → 1/(2(x-1)) - 1/(2(x+1))
9. cancel_expression      - Cancel: (x²-1)/(x-1) → x+1
10. together_expression   - Combine: 1/x + 1/y → (x+y)/(xy)

═══════════════════════════════════════════════════════════════════════════════
WORKFLOW INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

These tools work WITH derivation tracking:

1. Use these for specific transformations
2. derivation_record_step() to track the step
3. derivation_complete() to finalize

Example:
    # Step 1: Expand
    expand_expression("(x + a)**2")
    → {"result": "x**2 + 2*a*x + a**2"}

    # Step 2: Record
    derivation_record_step(
        expression="x**2 + 2*a*x + a**2",
        description="Expanded (x+a)²"
    )

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

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


def register_simplify_tools(mcp: Any) -> None:
    """Register advanced simplification tools with MCP server.

    Phase 1 Extensions (10 tools):
    - P0: expand, factor, collect, trigsimp, powsimp, radsimp, combsimp
    - P1: apart, cancel, together
    """

    # ═══════════════════════════════════════════════════════════════════════
    # P0 - BASIC ALGEBRAIC SIMPLIFICATION (7 tools)
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def expand_expression(
        expression: str,
        deep: bool = True,
        modulus: int | None = None,
        power_base: bool = True,
        power_exp: bool = True,
        mul: bool = True,
        log: bool = True,
        multinomial: bool = True,
        basic: bool = True,
    ) -> dict[str, Any]:
        """
        Expand algebraic expression.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        DETERMINISTIC: Always expands products and powers (unlike `simplify()`).

        Use cases:
        - Expand polynomial products: (x+1)(x-1) → x²-1
        - Expand powers: (x+a)² → x²+2ax+a²
        - Prepare for coefficient extraction
        - Expand logarithms: log(xy) → log(x)+log(y)

        Args:
            expression: Expression to expand
            deep: Expand recursively into subexpressions (default: True)
            modulus: Modular arithmetic (for finite fields)
            power_base: Expand (x*y)^n → x^n*y^n (default: True)
            power_exp: Expand x^(a+b) → x^a*x^b (default: True)
            mul: Expand products (default: True)
            log: Expand log(xy) → log(x)+log(y) (default: True)
            multinomial: Use multinomial expansion (default: True)
            basic: Apply basic expansion rules (default: True)

        Returns:
            Expanded expression with LaTeX

        Examples:
            # Polynomial expansion
            expand_expression("(x + 1)**2")
            → {"result": "x**2 + 2*x + 1", ...}

            # Product expansion
            expand_expression("(x + y)*(x - y)")
            → {"result": "x**2 - y**2", ...}

            # Exponential expansion
            expand_expression("exp(x + y)")
            → {"result": "exp(x)*exp(y)", ...}

            # Log expansion
            expand_expression("log(x*y)")
            → {"result": "log(x) + log(y)", ...}

            # PK model: Expand dose calculation
            expand_expression("dose/(V1 + V2) * exp(-k*t)")
            → {"result": "dose*exp(-k*t)/(V1 + V2)", ...}

            # Michaelis-Menten expanded
            expand_expression("(V_max*S + V_max*I)/(K_m + S)")
            → {"result": "V_max*S/(K_m + S) + V_max*I/(K_m + S)", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Build expand() kwargs
            expand_kwargs: dict[str, Any] = {
                "deep": deep,
                "power_base": power_base,
                "power_exp": power_exp,
                "mul": mul,
                "log": log,
                "multinomial": multinomial,
                "basic": basic,
            }
            if modulus is not None:
                expand_kwargs["modulus"] = modulus

            result = sp.expand(expr, **expand_kwargs)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "original_latex": sp.latex(expr),
                "operation": "expand",
                "options_used": {k: v for k, v in expand_kwargs.items() if v is not None},
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def factor_expression(
        expression: str,
        deep: bool = False,
        modulus: int | None = None,
    ) -> dict[str, Any]:
        """
        Factorize algebraic expression.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        DETERMINISTIC: Always attempts factorization (unlike `simplify()`).

        Use cases:
        - Find roots: x²-1 → (x-1)(x+1) ⇒ roots at x=±1
        - Simplify rational functions
        - Characteristic equations (eigenvalues)
        - Stability analysis (find poles)

        Args:
            expression: Expression to factorize
            deep: Factor recursively into subexpressions (default: False)
            modulus: Modular arithmetic (for finite fields)

        Returns:
            Factored expression with LaTeX

        Examples:
            # Quadratic factorization
            factor_expression("x**2 - 1")
            → {"result": "(x - 1)*(x + 1)", ...}

            # Find roots
            factor_expression("x**2 + 5*x + 6")
            → {"result": "(x + 2)*(x + 3)", ...}

            # Compartment model characteristic equation
            factor_expression("s**2 + (k12 + k21 + k10)*s + k21*k10")
            → {"result": "(s + λ1)*(s + λ2)", ...}  # eigenvalues

            # Rational function numerator
            factor_expression("C**2 - K_m**2")
            → {"result": "(C - K_m)*(C + K_m)", ...}

            # Difference of cubes
            factor_expression("x**3 - 8")
            → {"result": "(x - 2)*(x**2 + 2*x + 4)", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            factor_kwargs: dict[str, Any] = {"deep": deep}
            if modulus is not None:
                factor_kwargs["modulus"] = modulus

            result = sp.factor(expr, **factor_kwargs)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "original_latex": sp.latex(expr),
                "operation": "factor",
                "options_used": factor_kwargs,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def collect_expression(
        expression: str,
        variable: str | list[str],
        evaluate: bool = True,
        exact: bool = False,
    ) -> dict[str, Any]:
        """
        Collect terms by specified variable(s).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Groups expression by powers of variable, useful for:
        - Polynomial standard form
        - Coefficient extraction
        - Preparing for numerical evaluation

        Args:
            expression: Expression to collect
            variable: Variable(s) to collect by (string or list)
            evaluate: Evaluate coefficients (default: True)
            exact: Use exact arithmetic (default: False)

        Returns:
            Collected expression with LaTeX

        Examples:
            # Collect by x
            collect_expression("x*y + x - 3 + 2*x**2 - y*x**2 + x**3", "x")
            → {"result": "x**3 + x**2*(2 - y) + x*(y + 1) - 3", ...}

            # Extract polynomial coefficients
            collect_expression("a*x**2 + b*x + c + x**2", "x")
            → {"result": "x**2*(a + 1) + b*x + c", ...}

            # Multiple variables
            collect_expression("x*y + x*z + y*z", ["x", "y"])
            → Groups by x and y powers

            # PK: Collect by exp terms
            collect_expression("A*exp(-alpha*t) + B*exp(-beta*t)", "exp(-alpha*t)")
            → {"result": "A*exp(-alpha*t) + B*exp(-beta*t)", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Parse variable(s)
            if isinstance(variable, str):
                if "," in variable:
                    vars_list = [sp.Symbol(v.strip()) for v in variable.split(",")]
                else:
                    vars_list = sp.Symbol(variable)
            else:
                vars_list = [sp.Symbol(v) for v in variable]

            result = sp.collect(expr, vars_list, evaluate=evaluate, exact=exact)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "variable": variable,
                "operation": "collect",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def trigsimp_expression(
        expression: str,
        deep: bool = False,
        recursive: bool = False,
        method: str = "matching",
    ) -> dict[str, Any]:
        """
        Simplify trigonometric expressions.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Applies trigonometric identities to simplify expressions.

        Use cases:
        - Simplify sin²+cos² → 1
        - Simplify tan(x) → sin(x)/cos(x)
        - Oscillating chemical reactions
        - Phase analysis in PK/PD

        Args:
            expression: Expression to simplify
            deep: Apply to subexpressions (default: False)
            recursive: Apply repeatedly (default: False)
            method: Simplification method
                - "matching": Pattern matching (default, fast)
                - "groebner": Gröbner basis (slower, more powerful)
                - "combined": Try both

        Returns:
            Simplified expression with LaTeX

        Examples:
            # Pythagorean identity
            trigsimp_expression("sin(x)**2 + cos(x)**2")
            → {"result": "1", ...}

            # Tan identity
            trigsimp_expression("sin(x)/cos(x)")
            → {"result": "tan(x)", ...}

            # Double angle
            trigsimp_expression("2*sin(x)*cos(x)")
            → {"result": "sin(2*x)", ...}

            # Oscillating kinetics
            trigsimp_expression("sin(omega*t)**2 + cos(omega*t)**2")
            → {"result": "1", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            result = sp.trigsimp(expr, deep=deep, recursive=recursive, method=method)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "operation": "trigsimp",
                "method": method,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def powsimp_expression(
        expression: str,
        deep: bool = False,
        combine: str = "all",
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Simplify powers and exponentials.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Combines and simplifies powers using algebraic rules.

        Use cases:
        - Combine exponentials: exp(x)*exp(y) → exp(x+y)
        - Simplify powers: x²·x³ → x⁵
        - Nested powers: (x^a)^b → x^(ab)

        Args:
            expression: Expression to simplify
            deep: Apply to subexpressions (default: False)
            combine: How to combine bases
                - "all": Combine all (default)
                - "base": Only combine same base
                - "exp": Only exponentials
            force: Force transformation even if not valid for all values

        Returns:
            Simplified expression with LaTeX

        Examples:
            # Combine powers
            powsimp_expression("x**2 * x**3")
            → {"result": "x**5", ...}

            # Nested powers
            powsimp_expression("(x**a)**b")
            → {"result": "x**(a*b)", ...}

            # Exponentials
            powsimp_expression("exp(x)*exp(y)")
            → {"result": "exp(x + y)", ...}

            # PK: Combine elimination terms
            powsimp_expression("exp(-k*t)*exp(-k*τ)")
            → {"result": "exp(-k*(t + τ))", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            result = sp.powsimp(expr, deep=deep, combine=combine, force=force)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "operation": "powsimp",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def radsimp_expression(
        expression: str,
        symbolic: bool = True,
        max_terms: int = 4,
    ) -> dict[str, Any]:
        """
        Simplify radicals (square roots, cube roots, etc.).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Rationalizes denominators and simplifies radical expressions.

        Use cases:
        - Rationalize denominators: 1/(√3+√2)
        - Simplify nested radicals
        - Standard form for half-life calculations
        - Geometric mean calculations

        Args:
            expression: Expression to simplify
            symbolic: Allow symbolic radicals (default: True)
            max_terms: Maximum terms in denominator for rationalization

        Returns:
            Simplified expression with LaTeX

        Examples:
            # Rationalize denominator
            radsimp_expression("1/(sqrt(3) + sqrt(2))")
            → {"result": "-sqrt(2) + sqrt(3)", ...}

            # Simplify radical
            radsimp_expression("sqrt(12)")
            → {"result": "2*sqrt(3)", ...}

            # PK: Half-life with roots
            radsimp_expression("ln(2)/sqrt(k1*k2)")
            → {"result": "sqrt(k1*k2)*ln(2)/(k1*k2)", ...}

            # Nested radicals
            radsimp_expression("sqrt(2 + sqrt(2))")
            → Attempts simplification
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            result = sp.radsimp(expr, symbolic=symbolic, max_terms=max_terms)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "operation": "radsimp",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def combsimp_expression(expression: str) -> dict[str, Any]:
        """
        Simplify combinatorial expressions (factorials, binomials).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Simplifies expressions involving:
        - Factorials: n!/(n-k)!
        - Binomial coefficients: C(n,k)
        - Permutations: P(n,k)

        Use cases:
        - Taylor series coefficients
        - Probability calculations
        - Statistical formulas
        - Series expansions

        Args:
            expression: Expression with factorials/binomials

        Returns:
            Simplified expression with LaTeX

        Examples:
            # Falling factorial
            combsimp_expression("factorial(n)/factorial(n - 3)")
            → {"result": "n*(n - 1)*(n - 2)", ...}

            # Binomial identity
            combsimp_expression("binomial(n, k) * factorial(k)")
            → {"result": "factorial(n)/factorial(n - k)", ...}

            # Taylor coefficient
            combsimp_expression("x**n / factorial(n)")
            → Standard form for Taylor series

            # Rising factorial
            combsimp_expression("rf(x, 3)")
            → {"result": "x*(x + 1)*(x + 2)", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            result = sp.combsimp(expr)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "operation": "combsimp",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # P1 - RATIONAL FUNCTION PROCESSING (3 tools)
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def apart_expression(
        expression: str,
        variable: str | None = None,
        full: bool = False,
    ) -> dict[str, Any]:
        """
        Partial fraction decomposition.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Decomposes rational functions into sum of simpler fractions.

        CRITICAL FOR:
        - Inverse Laplace transform
        - Integration of rational functions
        - Compartment model analysis
        - Transfer function decomposition

        Args:
            expression: Rational function to decompose
            variable: Variable for decomposition (auto-detect if None)
            full: Return full decomposition (default: False)

        Returns:
            Partial fraction decomposition with LaTeX

        Examples:
            # Simple decomposition
            apart_expression("(x**2 + 3*x + 2)/(x**2 + 5*x + 6)", "x")
            → {"result": "1 - 2/(x + 3)", ...}

            # Compartment model transfer function
            apart_expression("dose*k12 / ((s + λ1)*(s + λ2))", "s")
            → {"result": "A/(s + λ1) + B/(s + λ2)", ...}
            # Prepare for inverse Laplace!

            # Integration preparation
            apart_expression("1/(x**2 - 1)", "x")
            → {"result": "1/(2*(x - 1)) - 1/(2*(x + 1))", ...}

            # Complex poles
            apart_expression("1/(x**2 + 1)", "x")
            → {"result": "-I/(2*(x - I)) + I/(2*(x + I))", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Auto-detect variable if not provided
            if variable is None:
                free_symbols = expr.free_symbols
                if len(free_symbols) == 1:
                    var = list(free_symbols)[0]
                elif len(free_symbols) == 0:
                    return {"success": False, "error": "No variables found in expression"}
                else:
                    return {
                        "success": False,
                        "error": f"Multiple variables found: {free_symbols}. Please specify one.",
                    }
            else:
                var = sp.Symbol(variable)

            result = sp.apart(expr, var, full=full)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "variable": str(var),
                "operation": "apart",
                "use_case": "Prepare for inverse Laplace or integration",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def cancel_expression(expression: str) -> dict[str, Any]:
        """
        Cancel common factors in rational expression.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Reduces rational functions to lowest terms by canceling common factors.

        Use cases:
        - Simplify PK models
        - Remove singularities
        - Numerical stability
        - Standard form

        Args:
            expression: Rational expression to cancel

        Returns:
            Canceled expression with LaTeX

        Examples:
            # Simple cancellation
            cancel_expression("(x**2 - 1)/(x - 1)")
            → {"result": "x + 1", ...}  # Removed (x-1) factor

            # PK clearance
            cancel_expression("(V*CL)/(V)")
            → {"result": "CL", ...}

            # Multiple factors
            cancel_expression("(x**2 - 4)/(x**2 + 4*x + 4)")
            → {"result": "(x - 2)/(x + 2)", ...}

            # Remove common exponentials
            cancel_expression("exp(-k*t)*C0 / exp(-k*t)")
            → {"result": "C0", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            result = sp.cancel(expr)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "operation": "cancel",
                "note": "Canceled common factors",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def together_expression(expression: str, deep: bool = False) -> dict[str, Any]:
        """
        Combine rational expressions over a common denominator.

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 1 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Combines separate fractions into a single fraction.

        Use cases:
        - Combine clearance terms
        - Total bioavailability
        - Multiple dosing routes
        - Fraction addition

        Args:
            expression: Sum of rational expressions
            deep: Apply to subexpressions (default: False)

        Returns:
            Combined expression with LaTeX

        Examples:
            # Simple addition
            together_expression("1/x + 1/y")
            → {"result": "(x + y)/(x*y)", ...}

            # Multiple clearances
            together_expression("CL_renal/V + CL_hepatic/V")
            → {"result": "(CL_renal + CL_hepatic)/V", ...}

            # Complex fractions
            together_expression("1/(x-1) + 1/(x+1)")
            → {"result": "2*x/(x**2 - 1)", ...}

            # PK: Total clearance
            together_expression("Q/V1 + CL/V1")
            → {"result": "(Q + CL)/V1", ...}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            result = sp.together(expr, deep=deep)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "operation": "together",
                "note": "Combined over common denominator",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # P2 - INTEGRAL TRANSFORMS (4 tools) - Phase 2
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def laplace_transform_expression(
        expression: str,
        time_var: str = "t",
        freq_var: str = "s",
    ) -> dict[str, Any]:
        """
        Laplace transform: f(t) → F(s).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 2 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Transforms time-domain functions to s-domain (Laplace domain).

        CRITICAL FOR:
        - ODE solving (time → algebraic in s-domain)
        - Stability analysis (poles in s-plane)
        - Transfer functions (system response)
        - Compartment model analysis

        Args:
            expression: Time-domain expression f(t)
            time_var: Time variable (default: "t")
            freq_var: Frequency variable (default: "s")

        Returns:
            Laplace transform F(s) with convergence conditions

        Examples:
            # Exponential decay
            laplace_transform_expression("exp(-k*t)", "t", "s")
            → {"result": "1/(s + k)", "convergence": "Re(s) > -Re(k)"}

            # Compartment elimination
            laplace_transform_expression("C0*exp(-k*t)", "t", "s")
            → {"result": "C0/(s + k)", ...}

            # Step function response
            laplace_transform_expression("Heaviside(t)", "t", "s")
            → {"result": "1/s", "convergence": "Re(s) > 0"}

            # Dosing with absorption
            laplace_transform_expression("D*ka*exp(-ka*t)", "t", "s")
            → {"result": "D*ka/(s + ka)", ...}

            # PK: Convert ODE to algebra
            # dC/dt + k*C = 0 → s*C(s) - C(0) + k*C(s) = 0
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Create symbols with proper assumptions
            t = sp.Symbol(time_var, real=True, positive=True)
            s = sp.Symbol(freq_var)

            # Substitute to ensure expr uses the correct symbols
            expr = expr.subs(sp.Symbol(time_var), t)

            # Perform Laplace transform
            result, convergence_plane, conditions = sp.laplace_transform(expr, t, s)

            # Format convergence conditions
            conv_str = str(convergence_plane) if convergence_plane != sp.S.true else None
            cond_str = str(conditions) if conditions != sp.S.true else None

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "time_var": time_var,
                "freq_var": freq_var,
                "operation": "laplace_transform",
                "convergence": conv_str,
                "conditions": cond_str,
                "note": "Transformed to s-domain (Laplace domain)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def inverse_laplace_transform_expression(
        expression: str,
        freq_var: str = "s",
        time_var: str = "t",
    ) -> dict[str, Any]:
        """
        Inverse Laplace transform: F(s) → f(t).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 2 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Transforms s-domain (Laplace) back to time-domain.

        CRITICAL FOR:
        - Getting time response from transfer function
        - Multi-compartment PK model solutions
        - Impulse/step response analysis
        - Converting algebraic solutions back to ODE solutions

        Args:
            expression: Frequency-domain expression F(s)
            freq_var: Frequency variable (default: "s")
            time_var: Time variable (default: "t")

        Returns:
            Time-domain function f(t)

        Examples:
            # Simple pole
            inverse_laplace_transform_expression("1/(s + k)", "s", "t")
            → {"result": "exp(-k*t)*Heaviside(t)", ...}

            # Two-compartment model (after partial fractions)
            inverse_laplace_transform_expression("A/(s + λ1) + B/(s + λ2)", "s", "t")
            → {"result": "A*exp(-λ1*t) + B*exp(-λ2*t)", ...}

            # Step response
            inverse_laplace_transform_expression("1/(s*(s + k))", "s", "t")
            → {"result": "(1 - exp(-k*t))/k", ...}

            # PK: Bolus injection response
            inverse_laplace_transform_expression("dose/(V*(s + k))", "s", "t")
            → {"result": "dose*exp(-k*t)/V", ...}

            # WORKFLOW: Use with apart_expression!
            # 1. apart_expression("F(s)", "s") → partial fractions
            # 2. inverse_laplace_transform_expression(...) → f(t)
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Create symbols with proper assumptions
            s = sp.Symbol(freq_var)
            t = sp.Symbol(time_var, real=True, positive=True)

            # Substitute to ensure expr uses the correct symbols
            expr = expr.subs(sp.Symbol(freq_var), s)

            # Perform inverse Laplace transform
            result = sp.inverse_laplace_transform(expr, s, t)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "freq_var": freq_var,
                "time_var": time_var,
                "operation": "inverse_laplace_transform",
                "note": "Transformed back to time-domain",
                "reminder": "Use apart_expression() first for rational functions!",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def fourier_transform_expression(
        expression: str,
        space_var: str = "x",
        freq_var: str = "k",
    ) -> dict[str, Any]:
        """
        Fourier transform: f(x) → F(k).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 2 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Transforms spatial/time function to frequency domain.

        USE CASES:
        - Periodic dosing analysis (repeated administration)
        - Spectral analysis (frequency components)
        - Signal processing (filter design)
        - Diffusion problems (spatial frequency)

        Args:
            expression: Space/time-domain expression f(x)
            space_var: Space/time variable (default: "x")
            freq_var: Frequency variable (default: "k")

        Returns:
            Fourier transform F(k)

        Examples:
            # Gaussian pulse
            fourier_transform_expression("exp(-x**2)", "x", "k")
            → {"result": "sqrt(pi)*exp(-pi**2*k**2)", ...}

            # Exponential decay
            fourier_transform_expression("exp(-abs(x))", "x", "k")
            → {"result": "2/(1 + k**2)", ...}

            # Rectangular pulse
            fourier_transform_expression("Heaviside(x+1) - Heaviside(x-1)", "x", "k")
            → {"result": "2*sin(k)/k", ...}

            # PK: Periodic dosing spectrum
            # Analyze frequency components of repeated doses
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Create symbols with proper assumptions
            x = sp.Symbol(space_var, real=True)
            k = sp.Symbol(freq_var, real=True)

            # Substitute to ensure expr uses the correct symbols
            expr = expr.subs(sp.Symbol(space_var), x)

            # Perform Fourier transform
            result = sp.fourier_transform(expr, x, k)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "space_var": space_var,
                "freq_var": freq_var,
                "operation": "fourier_transform",
                "note": "Transformed to frequency domain",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def inverse_fourier_transform_expression(
        expression: str,
        freq_var: str = "k",
        space_var: str = "x",
    ) -> dict[str, Any]:
        """
        Inverse Fourier transform: F(k) → f(x).

        ═══════════════════════════════════════════════════════════════════════
        🆕 PHASE 2 - NOT IN SYMPY-MCP OR NSFORGE v0.2.3!
        ═══════════════════════════════════════════════════════════════════════

        Transforms frequency domain back to spatial/time domain.

        USE CASES:
        - Reconstruct signal from spectrum
        - Inverse filter design
        - Synthesize periodic patterns
        - Diffusion problem solutions

        Args:
            expression: Frequency-domain expression F(k)
            freq_var: Frequency variable (default: "k")
            space_var: Space/time variable (default: "x")

        Returns:
            Spatial/time-domain function f(x)

        Examples:
            # Lorentzian spectrum
            inverse_fourier_transform_expression("1/(1 + k**2)", "k", "x")
            → {"result": "pi*exp(-abs(x))", ...}

            # Sinc function
            inverse_fourier_transform_expression("Heaviside(k+1) - Heaviside(k-1)", "k", "x")
            → {"result": "sin(x)/(pi*x)", ...}

            # PK: Reconstruct concentration profile from spectrum
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            # Create symbols with proper assumptions
            k = sp.Symbol(freq_var, real=True)
            x = sp.Symbol(space_var, real=True)

            # Substitute to ensure expr uses the correct symbols
            expr = expr.subs(sp.Symbol(freq_var), k)

            # Perform inverse Fourier transform
            result = sp.inverse_fourier_transform(expr, k, x)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "original": expression,
                "freq_var": freq_var,
                "space_var": space_var,
                "operation": "inverse_fourier_transform",
                "note": "Transformed back to spatial/time domain",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
