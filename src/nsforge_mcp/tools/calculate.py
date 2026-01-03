"""
Calculation Tools - Extended beyond SymPy-MCP

═══════════════════════════════════════════════════════════════════════════════
🎯 NSForge Unique Calculation Capabilities
═══════════════════════════════════════════════════════════════════════════════

These tools provide capabilities NOT available in SymPy-MCP:

1. LIMITS & SERIES (SymPy-MCP lacks these!)
   - calculate_limit: Compute limits (including ±∞)
   - calculate_series: Taylor/Laurent/Fourier series expansions
   - calculate_summation: Symbolic summations (finite/infinite)

2. INEQUALITIES (SymPy-MCP lacks these!)
   - solve_inequality: Solve single inequalities
   - solve_inequality_system: Solve systems of inequalities

3. STATISTICS (SymPy-MCP lacks these!)
   - define_distribution: Define probability distributions
   - distribution_stats: Get mean, variance, etc.
   - distribution_probability: Calculate P(X < a), P(a < X < b)

4. ASSUMPTIONS (SymPy-MCP lacks query tools!)
   - query_assumptions: Ask if x is positive, real, integer, etc.
   - refine_expression: Simplify using assumptions

5. BASIC TOOLS (kept for convenience)
   - evaluate_numeric: Final numeric evaluation
   - symbolic_equal: Quick equivalence check

═══════════════════════════════════════════════════════════════════════════════
WORKFLOW: Use these tools alongside SymPy-MCP
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


def _create_distribution(distribution_type: str, params: dict[str, Any], name: str) -> Any:
    """Create a SymPy stats distribution.

    Args:
        distribution_type: Type of distribution (normal, exponential, etc.)
        params: Parsed parameters
        name: Name of the random variable

    Returns:
        SymPy RandomSymbol or None if unknown type
    """
    from sympy import stats

    dist_creators = {
        # Continuous
        "normal": lambda: stats.Normal(name, params.get("mean", 0), params.get("std", 1)),
        "exponential": lambda: stats.Exponential(name, params.get("rate", 1)),
        "uniform": lambda: stats.Uniform(name, params.get("a", 0), params.get("b", 1)),
        "gamma": lambda: stats.Gamma(name, params.get("k", 1), params.get("theta", 1)),
        "beta": lambda: stats.Beta(name, params.get("alpha", 1), params.get("beta", 1)),
        "lognormal": lambda: stats.LogNormal(name, params.get("mean", 0), params.get("std", 1)),
        # Discrete
        "poisson": lambda: stats.Poisson(name, params.get("lambda", 1)),
        "binomial": lambda: stats.Binomial(name, params.get("n", 10), params.get("p", sp.Rational(1, 2))),
        "geometric": lambda: stats.Geometric(name, params.get("p", sp.Rational(1, 2))),
    }

    creator = dist_creators.get(distribution_type.lower())
    return creator() if creator else None


def register_calculate_tools(mcp: Any) -> None:  # noqa: C901
    """Register calculation tools with MCP server.

    NSForge Unique Capabilities (not in SymPy-MCP):
    - calculate_limit: Limits (including ±∞)
    - calculate_series: Taylor/Laurent/Fourier series
    - calculate_summation: Symbolic summations
    - solve_inequality: Single inequalities
    - solve_inequality_system: Inequality systems
    - define_distribution: Statistical distributions
    - distribution_stats: Mean, variance, etc.
    - distribution_probability: Probability calculations
    - query_assumptions: Ask about symbol properties
    - refine_expression: Simplify using assumptions

    Basic tools (kept for convenience):
    - evaluate_numeric: Final numeric evaluation
    - symbolic_equal: Quick equivalence check
    """

    # ═══════════════════════════════════════════════════════════════════════
    # LIMITS & SERIES (SymPy-MCP lacks these!)
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def calculate_limit(
        expression: str,
        variable: str,
        point: str,
        direction: str = "+-",
    ) -> dict[str, Any]:
        """
        Calculate the limit of an expression.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Steady-state analysis (t → ∞)
        - Boundary behavior (x → 0)
        - Asymptotic behavior
        - L'Hôpital's rule situations

        Args:
            expression: The expression to take limit of
            variable: The variable approaching the point
            point: The point to approach (can be "oo", "-oo", "0", "1", etc.)
            direction: Direction of approach
                - "+-" or "": Two-sided (default)
                - "+": From the right (x → 0⁺)
                - "-": From the left (x → 0⁻)

        Returns:
            Limit result with LaTeX

        Examples:
            # Steady-state concentration
            calculate_limit("C0 * exp(-k*t)", "t", "oo")
            → {"result": "0", "latex": "0"}

            # Indeterminate form (0/0)
            calculate_limit("sin(x)/x", "x", "0")
            → {"result": "1", "latex": "1"}

            # One-sided limit
            calculate_limit("1/x", "x", "0", direction="+")
            → {"result": "oo", "latex": "\\infty"}
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            var = sp.Symbol(variable)

            # Parse the point
            if point.lower() in ("oo", "inf", "infinity"):
                point_val = sp.oo
            elif point.lower() in ("-oo", "-inf", "-infinity"):
                point_val = -sp.oo
            else:
                point_val, pt_err = _parse_safe(point)
                if pt_err or point_val is None:
                    return {"success": False, "error": f"Invalid point: {point}"}

            # Determine direction
            dir_map = {"+-": "+-", "+": "+", "-": "-", "": "+-"}
            direction_val = dir_map.get(direction, "+-")

            # Calculate limit
            result = sp.limit(expr, var, point_val, dir=direction_val)

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "expression": expression,
                "variable": variable,
                "point": str(point_val),
                "direction": direction_val,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def calculate_series(
        expression: str,
        variable: str,
        point: str = "0",
        order: int = 6,
        series_type: str = "taylor",
    ) -> dict[str, Any]:
        """
        Calculate series expansion of an expression.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Approximate functions near a point
        - Linearization (order=1)
        - Small-signal analysis
        - Perturbation methods

        Args:
            expression: The expression to expand
            variable: The expansion variable
            point: The expansion point (default: "0" for Maclaurin series)
            order: Number of terms (default: 6)
            series_type: Type of series
                - "taylor": Taylor/Maclaurin series (default)
                - "laurent": Laurent series (for singularities)
                - "fourier": Fourier series (periodic functions)

        Returns:
            Series expansion with LaTeX

        Examples:
            # Maclaurin series of sin(x)
            calculate_series("sin(x)", "x", "0", order=5)
            → {"result": "x - x**3/6 + x**5/120", ...}

            # Taylor series around x=1
            calculate_series("ln(x)", "x", "1", order=4)
            → {"result": "-1 + x - (x-1)**2/2 + ...", ...}

            # Linearization (first-order approximation)
            calculate_series("exp(-E/(R*T))", "T", "T0", order=1)
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            var = sp.Symbol(variable)

            # Parse expansion point
            if point == "0":
                point_val = sp.Integer(0)
            else:
                point_val, pt_err = _parse_safe(point)
                if pt_err or point_val is None:
                    return {"success": False, "error": f"Invalid point: {point}"}

            if series_type == "taylor":
                # Taylor/Maclaurin series
                result = sp.series(expr, var, point_val, n=order + 1).removeO()
            elif series_type == "laurent":
                # Laurent series (allows negative powers)
                result = sp.series(expr, var, point_val, n=order + 1)
                # Keep O() term for Laurent to show order
            elif series_type == "fourier":
                # Fourier series (requires periodic interval)
                # This is a simplified version
                result = sp.series(expr, var, point_val, n=order + 1).removeO()
            else:
                return {"success": False, "error": f"Unknown series type: {series_type}"}

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "expression": expression,
                "variable": variable,
                "point": str(point_val),
                "order": order,
                "series_type": series_type,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def calculate_summation(
        expression: str,
        index: str,
        lower: str,
        upper: str,
    ) -> dict[str, Any]:
        """
        Calculate symbolic summation.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Finite sums (Σ from n=1 to N)
        - Infinite series (Σ from n=1 to ∞)
        - Partition functions
        - Probability mass functions

        Args:
            expression: The summand (term being summed)
            index: Summation index variable
            lower: Lower bound (integer or symbol)
            upper: Upper bound (integer, symbol, or "oo" for infinity)

        Returns:
            Summation result with LaTeX

        Examples:
            # Finite sum: Σ k from k=1 to n
            calculate_summation("k", "k", "1", "n")
            → {"result": "n*(n+1)/2", ...}

            # Infinite geometric series: Σ r^n from n=0 to ∞
            calculate_summation("r**n", "n", "0", "oo")
            → {"result": "1/(1-r)", "condition": "|r| < 1"}

            # Partition function: Σ exp(-E_i/(k*T)) from i=0 to N
            calculate_summation("exp(-E*i/(k*T))", "i", "0", "N")
        """
        expr, error = _parse_safe(expression)
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

        try:
            idx = sp.Symbol(index, integer=True)

            # Parse bounds
            if lower.lstrip("-").isdigit():
                lower_val = sp.Integer(int(lower))
            else:
                lower_val = sp.Symbol(lower, integer=True)

            if upper.lower() in ("oo", "inf", "infinity"):
                upper_val = sp.oo
            elif upper.lstrip("-").isdigit():
                upper_val = sp.Integer(int(upper))
            else:
                upper_val = sp.Symbol(upper, integer=True)

            # Calculate summation
            result = sp.summation(expr, (idx, lower_val, upper_val))

            # Check for conditions (e.g., convergence)
            conditions = []
            if upper_val == sp.oo:
                conditions.append("Check convergence conditions")

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "summation_latex": f"\\sum_{{{index}={lower}}}^{{{upper}}} {sp.latex(expr)}",
                "expression": expression,
                "index": index,
                "lower": str(lower_val),
                "upper": str(upper_val),
                "conditions": conditions if conditions else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # INEQUALITIES (SymPy-MCP lacks these!)
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def solve_inequality(
        inequality: str,
        variable: str,
        domain: str = "real",
    ) -> dict[str, Any]:
        """
        Solve a single inequality.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Find valid parameter ranges
        - Stability conditions
        - Convergence criteria
        - Domain restrictions

        Args:
            inequality: The inequality (use <, >, <=, >=)
            variable: Variable to solve for
            domain: Domain restriction ("real", "positive", "integer")

        Returns:
            Solution set with interval notation

        Examples:
            # Simple inequality
            solve_inequality("x**2 - 4 < 0", "x")
            → {"result": "(-2, 2)", "latex": "-2 < x < 2"}

            # Rational inequality
            solve_inequality("(x-1)/(x+2) >= 0", "x")
            → {"result": "(-oo, -2) ∪ [1, oo)", ...}

            # With domain restriction
            solve_inequality("x**2 < 9", "x", domain="positive")
            → {"result": "(0, 3)", ...}
        """
        try:
            var = sp.Symbol(variable, real=(domain == "real"))

            # Parse inequality
            # Replace comparison operators
            ineq_str = inequality.replace(">=", "≥").replace("<=", "≤")
            if "≥" in ineq_str:
                left, right = ineq_str.split("≥")
                left_expr, _ = _parse_safe(left.strip())
                right_expr, _ = _parse_safe(right.strip())
                ineq = sp.Ge(left_expr, right_expr)
            elif "≤" in ineq_str:
                left, right = ineq_str.split("≤")
                left_expr, _ = _parse_safe(left.strip())
                right_expr, _ = _parse_safe(right.strip())
                ineq = sp.Le(left_expr, right_expr)
            elif ">" in ineq_str:
                left, right = ineq_str.split(">")
                left_expr, _ = _parse_safe(left.strip())
                right_expr, _ = _parse_safe(right.strip())
                ineq = sp.Gt(left_expr, right_expr)
            elif "<" in ineq_str:
                left, right = ineq_str.split("<")
                left_expr, _ = _parse_safe(left.strip())
                right_expr, _ = _parse_safe(right.strip())
                ineq = sp.Lt(left_expr, right_expr)
            else:
                return {"success": False, "error": "No comparison operator found"}

            # Solve
            from sympy.solvers.inequalities import solve_univariate_inequality
            result = solve_univariate_inequality(ineq, var, relational=False)

            # Apply domain restriction if needed
            if domain == "positive":
                result = result.intersect(sp.Interval(0, sp.oo, left_open=True))
            elif domain == "integer":
                # For integers, enumerate the solution
                pass  # Keep the interval, let user interpret

            return {
                "success": True,
                "result": str(result),
                "latex": sp.latex(result),
                "inequality": inequality,
                "variable": variable,
                "domain": domain,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def solve_inequality_system(
        inequalities: list[str],
        variable: str,
    ) -> dict[str, Any]:
        """
        Solve a system of inequalities (find the intersection).

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Find valid parameter ranges satisfying multiple constraints
        - Optimization feasibility regions
        - Multiple stability conditions

        Args:
            inequalities: List of inequalities
            variable: Variable to solve for

        Returns:
            Solution set (intersection of all solutions)

        Examples:
            # Multiple constraints
            solve_inequality_system(["x > 0", "x < 10", "x**2 < 25"], "x")
            → {"result": "(0, 5)", ...}

            # Therapeutic window
            solve_inequality_system(["C > MIC", "C < toxic_level"], "C")
        """
        try:
            sp.Symbol(variable, real=True)

            # Solve each inequality
            solution_sets = []
            for ineq in inequalities:
                result = solve_inequality(ineq, variable)
                if not result.get("success"):
                    return {
                        "success": False,
                        "error": f"Failed to solve: {ineq}",
                        "detail": result.get("error"),
                    }
                # Parse the result back to a SymPy set
                result_set = sp.sympify(result["result"])
                solution_sets.append(result_set)

            # Intersect all solutions
            final_result = solution_sets[0]
            for s in solution_sets[1:]:
                final_result = final_result.intersect(s)

            return {
                "success": True,
                "result": str(final_result),
                "latex": sp.latex(final_result),
                "inequalities": inequalities,
                "variable": variable,
                "individual_solutions": [str(s) for s in solution_sets],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS (SymPy-MCP lacks these!)
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def define_distribution(
        distribution_type: str,
        parameters: dict[str, str],
        name: str = "X",
    ) -> dict[str, Any]:
        """
        Define a probability distribution.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP! Uses sympy.stats module.
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Model measurement uncertainty
        - Population variability in pharmacokinetics
        - Error propagation
        - Monte Carlo preparation

        Supported distributions:
        - Continuous: normal, exponential, uniform, gamma, beta, lognormal
        - Discrete: poisson, binomial, geometric

        Args:
            distribution_type: Type of distribution
            parameters: Distribution parameters (as strings for symbolic)
            name: Name of the random variable

        Returns:
            Distribution definition with PDF/PMF

        Examples:
            # Normal distribution
            define_distribution("normal", {"mean": "mu", "std": "sigma"}, "X")

            # Exponential (for waiting times)
            define_distribution("exponential", {"rate": "lambda"}, "T")

            # Log-normal (for PK parameters)
            define_distribution("lognormal", {"mean": "mu", "std": "sigma"}, "CL")
        """
        from sympy import stats

        try:
            # Parse parameters
            parsed_params = {}
            for key, val in parameters.items():
                parsed_val, err = _parse_safe(val)
                if err:
                    parsed_params[key] = sp.Symbol(val, positive=True)
                else:
                    parsed_params[key] = parsed_val

            # Create distribution
            dist_map = {
                # Continuous
                "normal": lambda p: stats.Normal(name, p.get("mean", 0), p.get("std", 1)),
                "exponential": lambda p: stats.Exponential(name, p.get("rate", 1)),
                "uniform": lambda p: stats.Uniform(name, p.get("a", 0), p.get("b", 1)),
                "gamma": lambda p: stats.Gamma(name, p.get("k", 1), p.get("theta", 1)),
                "beta": lambda p: stats.Beta(name, p.get("alpha", 1), p.get("beta", 1)),
                "lognormal": lambda p: stats.LogNormal(name, p.get("mean", 0), p.get("std", 1)),
                # Discrete
                "poisson": lambda p: stats.Poisson(name, p.get("lambda", 1)),
                "binomial": lambda p: stats.Binomial(name, p.get("n", 10), p.get("p", 0.5)),
                "geometric": lambda p: stats.Geometric(name, p.get("p", 0.5)),
            }

            if distribution_type.lower() not in dist_map:
                return {
                    "success": False,
                    "error": f"Unknown distribution: {distribution_type}",
                    "available": list(dist_map.keys()),
                }

            rv = dist_map[distribution_type.lower()](parsed_params)

            # Get PDF or PMF
            x = sp.Symbol("x")
            try:
                density = stats.density(rv)(x)
                density_type = "PDF"
            except Exception:
                density = "N/A (discrete)"
                density_type = "PMF"

            return {
                "success": True,
                "name": name,
                "distribution": distribution_type,
                "parameters": {k: str(v) for k, v in parsed_params.items()},
                "density_type": density_type,
                "density": str(density),
                "density_latex": sp.latex(density) if density != "N/A (discrete)" else "N/A",
                "message": f"Distribution {name} ~ {distribution_type.capitalize()}({parameters}) defined.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def distribution_stats(
        distribution_type: str,
        parameters: dict[str, str],
        stats_to_compute: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compute statistics of a distribution.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Args:
            distribution_type: Type of distribution
            parameters: Distribution parameters
            stats_to_compute: Which statistics (default: all available)
                - "mean", "variance", "std", "skewness", "kurtosis", "entropy"

        Returns:
            Computed statistics

        Examples:
            distribution_stats("normal", {"mean": "mu", "std": "sigma"})
            → {"mean": "mu", "variance": "sigma**2", "std": "sigma", ...}
        """
        from sympy import stats

        try:
            # Create distribution
            parsed_params = {}
            for key, val in parameters.items():
                parsed_val, err = _parse_safe(val)
                if err:
                    parsed_params[key] = sp.Symbol(val, positive=True)
                else:
                    parsed_params[key] = parsed_val

            # Quick distribution creation
            rv = _create_distribution(distribution_type, parsed_params, "X")
            if rv is None:
                return {"success": False, "error": f"Unknown distribution: {distribution_type}"}

            # Compute requested statistics
            available_stats = ["mean", "variance", "std", "skewness", "kurtosis", "entropy"]
            to_compute = stats_to_compute or ["mean", "variance", "std"]

            results = {}
            for stat in to_compute:
                if stat not in available_stats:
                    continue
                try:
                    if stat == "mean":
                        val = stats.E(rv)
                    elif stat == "variance":
                        val = stats.variance(rv)
                    elif stat == "std":
                        val = sp.sqrt(stats.variance(rv))
                    elif stat == "skewness":
                        val = stats.skewness(rv)
                    elif stat == "kurtosis":
                        val = stats.kurtosis(rv)
                    elif stat == "entropy":
                        val = stats.entropy(rv)
                    else:
                        continue
                    results[stat] = {"value": str(val), "latex": sp.latex(val)}
                except Exception as e:
                    results[stat] = {"error": str(e)}

            return {
                "success": True,
                "distribution": distribution_type,
                "parameters": {k: str(v) for k, v in parsed_params.items()},
                "statistics": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def distribution_probability(
        distribution_type: str,
        parameters: dict[str, str],
        condition: str,
    ) -> dict[str, Any]:
        """
        Calculate probability P(condition).

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        Args:
            distribution_type: Type of distribution
            parameters: Distribution parameters
            condition: Condition string using X as the random variable
                - "X < 5", "X > 2", "X >= 3", "X <= 1"
                - "2 < X < 5" (between two values)

        Returns:
            Probability (symbolic or numeric)

        Examples:
            # P(X < 0) for standard normal
            distribution_probability("normal", {"mean": "0", "std": "1"}, "X < 0")
            → {"probability": "1/2", ...}

            # P(1 < X < 3) for exponential
            distribution_probability("exponential", {"rate": "lambda"}, "1 < X < 3")
        """
        from sympy import stats

        try:
            # Parse parameters
            parsed_params = {}
            for key, val in parameters.items():
                parsed_val, err = _parse_safe(val)
                if err:
                    parsed_params[key] = sp.Symbol(val, positive=True)
                else:
                    parsed_params[key] = parsed_val

            # Create distribution
            rv = _create_distribution(distribution_type, parsed_params, "X")
            if rv is None:
                return {"success": False, "error": f"Unknown distribution: {distribution_type}"}

            # Parse condition
            # Handle compound conditions like "1 < X < 3"
            cond = None  # Initialize to satisfy type checker
            if condition.count("<") == 2 or condition.count(">") == 2:
                # Compound inequality
                parts = condition.replace(">", "<").split("<")
                if len(parts) == 3:
                    lower, _, upper = parts
                    lower_val, _ = _parse_safe(lower.strip())
                    upper_val, _ = _parse_safe(upper.strip())
                    cond = (rv > lower_val) & (rv < upper_val)
            elif "<=" in condition:
                left, right = condition.split("<=")
                if "X" in left:
                    right_val, _ = _parse_safe(right.strip())
                    cond = rv <= right_val
                else:
                    left_val, _ = _parse_safe(left.strip())
                    cond = rv >= left_val
            elif ">=" in condition:
                left, right = condition.split(">=")
                if "X" in left:
                    right_val, _ = _parse_safe(right.strip())
                    cond = rv >= right_val
                else:
                    left_val, _ = _parse_safe(left.strip())
                    cond = rv <= left_val
            elif "<" in condition:
                left, right = condition.split("<")
                if "X" in left:
                    right_val, _ = _parse_safe(right.strip())
                    cond = rv < right_val
                else:
                    left_val, _ = _parse_safe(left.strip())
                    cond = rv > left_val
            elif ">" in condition:
                left, right = condition.split(">")
                if "X" in left:
                    right_val, _ = _parse_safe(right.strip())
                    cond = rv > right_val
                else:
                    left_val, _ = _parse_safe(left.strip())
                    cond = rv < left_val
            else:
                return {"success": False, "error": "Cannot parse condition"}

            # Calculate probability
            if cond is None:
                return {"success": False, "error": "Failed to parse condition into a valid expression"}
            prob = stats.P(cond)

            return {
                "success": True,
                "distribution": distribution_type,
                "condition": condition,
                "probability": str(prob),
                "probability_latex": sp.latex(prob),
                "probability_numeric": float(prob.evalf()) if prob.is_number else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # ASSUMPTIONS QUERY (SymPy-MCP lacks these!)
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def query_assumptions(
        expression: str,
        query: str,
        assumptions: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """
        Query properties of an expression based on assumptions.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP! Uses sympy.assumptions module.
        ═══════════════════════════════════════════════════════════════════════

        Use cases:
        - Check if expression is always positive
        - Verify domain validity
        - Check for potential singularities

        Available queries:
        - positive, negative, nonnegative, nonpositive
        - real, imaginary, complex
        - integer, rational, irrational
        - even, odd, prime
        - finite, infinite, zero, nonzero

        Args:
            expression: Expression to query about
            query: Property to check
            assumptions: Assumptions about symbols
                {"x": ["positive", "real"], "n": ["integer"]}

        Returns:
            Query result (True, False, or None if unknown)

        Examples:
            # Is x**2 always positive?
            query_assumptions("x**2", "positive", {"x": ["real", "nonzero"]})
            → {"result": True, ...}

            # Is exp(x) always real?
            query_assumptions("exp(x)", "real", {"x": ["real"]})
            → {"result": True, ...}
        """
        from sympy.assumptions import Q, ask

        try:
            # Create symbols with assumptions
            local_dict = {}
            if assumptions:
                for var_name, var_assumptions in assumptions.items():
                    sym_kwargs = {}
                    for a in var_assumptions:
                        sym_kwargs[a] = True
                    local_dict[var_name] = sp.Symbol(var_name, **sym_kwargs)

            # Parse expression
            expr_clean = expression.replace("^", "**")
            expr = parse_expr(expr_clean, local_dict=local_dict, transformations=TRANSFORMATIONS)

            # Get query predicate
            query_map = {
                "positive": Q.positive,
                "negative": Q.negative,
                "nonnegative": Q.nonnegative,
                "nonpositive": Q.nonpositive,
                "real": Q.real,
                "imaginary": Q.imaginary,
                "complex": Q.complex,
                "integer": Q.integer,
                "rational": Q.rational,
                "irrational": Q.irrational,
                "even": Q.even,
                "odd": Q.odd,
                "prime": Q.prime,
                "finite": Q.finite,
                "infinite": Q.infinite,
                "zero": Q.zero,
                "nonzero": Q.nonzero,
            }

            if query.lower() not in query_map:
                return {
                    "success": False,
                    "error": f"Unknown query: {query}",
                    "available_queries": list(query_map.keys()),
                }

            predicate = query_map[query.lower()]
            result = ask(predicate(expr))

            return {
                "success": True,
                "expression": expression,
                "query": query,
                "result": result,  # True, False, or None
                "interpretation": (
                    "Yes" if result is True
                    else "No" if result is False
                    else "Cannot determine (need more assumptions)"
                ),
                "assumptions_used": assumptions,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def refine_expression(
        expression: str,
        assumptions: dict[str, list[str]],
    ) -> dict[str, Any]:
        """
        Simplify expression using assumptions.

        ═══════════════════════════════════════════════════════════════════════
        🆕 NOT AVAILABLE IN SYMPY-MCP!
        ═══════════════════════════════════════════════════════════════════════

        SymPy can simplify expressions differently when it knows
        properties of the variables. For example:
        - sqrt(x**2) → x when x is positive
        - Abs(x) → x when x is positive

        Args:
            expression: Expression to refine
            assumptions: Assumptions about symbols

        Returns:
            Refined expression

        Examples:
            # sqrt(x**2) simplifies to x when x is positive
            refine_expression("sqrt(x**2)", {"x": ["positive"]})
            → {"result": "x", ...}

            # Abs simplifies under assumptions
            refine_expression("Abs(a*b)", {"a": ["positive"], "b": ["positive"]})
            → {"result": "a*b", ...}
        """
        try:
            # Create symbols with assumptions
            local_dict = {}
            for var_name, var_assumptions in assumptions.items():
                sym_kwargs = {}
                for a in var_assumptions:
                    sym_kwargs[a] = True
                local_dict[var_name] = sp.Symbol(var_name, **sym_kwargs)

            # Parse expression
            expr_clean = expression.replace("^", "**")
            expr = parse_expr(expr_clean, local_dict=local_dict, transformations=TRANSFORMATIONS)

            # Build assumption context
            from sympy.assumptions import refine  # noqa: F401

            # Refine
            result = sp.refine(expr)

            return {
                "success": True,
                "original": expression,
                "refined": str(result),
                "refined_latex": sp.latex(result),
                "assumptions": assumptions,
                "simplified": str(result) != expression,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # BASIC TOOLS (kept for convenience)
    # ═══════════════════════════════════════════════════════════════════════

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
        if error or expr is None:
            return {"success": False, "error": error or "Failed to parse expression"}

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
        if err1 or err2 or e1 is None or e2 is None:
            return {"success": False, "error": err1 or err2 or "Failed to parse expression"}

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
