"""
Code Generation Tools

Tools for generating executable Python code from derivation steps.

═══════════════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW - READ BEFORE USING THESE TOOLS!
═══════════════════════════════════════════════════════════════════════════════

CORRECT order:
1. Use SymPy-MCP for symbolic calculations (solve, simplify, diff, etc.)
2. Use print_latex_expression() to show formulas to user
3. User confirms the results
4. THEN use these tools to generate code/reports

❌ NEVER use these tools to generate code for UNVERIFIED calculations!
❌ NEVER skip the SymPy-MCP verification step!

The generated code assembles VERIFIED expressions into executable form.
It does NOT perform new calculations.
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Any

from nsforge.domain.codegen import (
    UnsafeCodegenInput,
    canonical_python_expression,
    python_expression_symbols,
    render_python_function,
    safe_python_comment,
    validate_python_identifier,
)


def register_codegen_tools(mcp: Any) -> None:
    """Register code generation tools with MCP server.

    ⚠️ These tools generate code from VERIFIED derivation steps.
    Always use SymPy-MCP first to verify calculations!
    """

    @mcp.tool()
    def generate_python_function(
        name: str,
        description: str,
        parameters: list[dict[str, str]],
        steps: list[dict[str, str]],
        return_vars: list[str],
    ) -> dict[str, Any]:
        """
        Generate a Python function from VERIFIED derivation steps.

        ═══════════════════════════════════════════════════════════════════════
        ⚠️ PREREQUISITE: All expressions must be verified with SymPy-MCP first!
        ═══════════════════════════════════════════════════════════════════════

        Correct workflow:
        1. Use SymPy-MCP to derive and verify each expression
        2. Use print_latex_expression() to show results to user
        3. User confirms the derivation is correct
        4. Call this tool with the verified expressions

        The generated code uses SymPy for computation, ensuring correctness.
        This is NOT Agent-generated code - it's assembled from verified steps.

        Args:
            name: Function name (e.g., "calculate_seatbelt_tension")
            description: Function docstring description
            parameters: List of {"name": str, "type": str, "description": str}
            steps: List of {"description": str, "expression": str, "result_var": str}
            return_vars: Variables to return

        Returns:
            Generated Python code

        Example:
            generate_python_function(
                name="calculate_tension",
                description="Calculate seatbelt tension from collision",
                parameters=[
                    {"name": "M1", "type": "float", "description": "Vehicle 1 mass (kg)"},
                    {"name": "M2", "type": "float", "description": "Vehicle 2 mass (kg)"},
                    {"name": "v", "type": "float", "description": "Initial velocity (m/s)"},
                    {"name": "m", "type": "float", "description": "Person mass (kg)"},
                    {"name": "k", "type": "float", "description": "Seatbelt constant (N/m)"},
                ],
                steps=[
                    {"description": "Final velocity after collision",
                     "expression": "M1 * v / (M1 + M2)",
                     "result_var": "v_f"},
                    {"description": "Velocity change",
                     "expression": "v - v_f",
                     "result_var": "delta_v"},
                    {"description": "Maximum tension",
                     "expression": "delta_v * sqrt(m * k)",
                     "result_var": "T_max"},
                ],
                return_vars=["v_f", "delta_v", "T_max"]
            )
        """
        try:
            code = render_python_function(name, description, parameters, steps, return_vars)
        except (KeyError, TypeError, UnsafeCodegenInput) as exc:
            return {"success": False, "error": str(exc)}

        return {
            "success": True,
            "code": code,
            "function_name": name,
            "parameters": [p["name"] for p in parameters],
            "returns": return_vars,
        }

    @mcp.tool()
    def generate_latex_derivation(
        title: str,
        steps: list[dict[str, str]],
        final_result: str,
    ) -> dict[str, Any]:
        """
        Generate LaTeX documentation for a derivation.

        Args:
            title: Derivation title
            steps: List of {"description": str, "latex": str}
            final_result: Final result in LaTeX

        Returns:
            LaTeX document string
        """
        lines = [
            f"\\section{{{title}}}",
            "",
            "\\begin{align}",
        ]

        for i, step in enumerate(steps, 1):
            desc = step.get("description", f"Step {i}")
            latex = step.get("latex", step.get("expression", ""))
            lines.append(f"    &\\text{{{desc}}} \\nonumber \\\\")
            lines.append(f"    &{latex} \\\\")

        lines.append("\\end{align}")
        lines.append("")
        lines.append(f"\\textbf{{Final Result:}} ${final_result}$")

        latex_doc = "\n".join(lines)

        return {
            "success": True,
            "latex": latex_doc,
            "title": title,
            "steps_count": len(steps),
        }

    @mcp.tool()
    def generate_derivation_report(
        problem: str,
        given: dict[str, str],
        steps: list[dict[str, str]],
        results: dict[str, str],
        verification: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a complete derivation report in Markdown.

        Args:
            problem: Problem description
            given: Given parameters {"symbol": "value with unit"}
            steps: Derivation steps
            results: Final results {"symbol": "expression"}
            verification: Optional verification status

        Returns:
            Markdown report
        """
        lines = [
            "# Derivation Report",
            "",
            "## Problem",
            problem,
            "",
            "## Given",
            "",
        ]

        for sym, val in given.items():
            lines.append(f"- ${sym}$ = {val}")

        lines.extend(
            [
                "",
                "## Derivation Steps",
                "",
            ]
        )

        for i, step in enumerate(steps, 1):
            lines.append(f"### Step {i}: {step.get('description', '')}")
            if "expression" in step:
                lines.append(f"$${step['expression']}$$")
            if "result" in step:
                lines.append(f"**Result:** ${step.get('result_var', '')} = {step['result']}$")
            lines.append("")

        lines.extend(
            [
                "## Results",
                "",
            ]
        )

        for sym, expr in results.items():
            lines.append(f"- ${sym} = {expr}$")

        if verification:
            lines.extend(
                [
                    "",
                    "## Verification",
                    "",
                ]
            )
            for check, passed in verification.items():
                status = "✅" if passed else "❌"
                lines.append(f"- {check}: {status}")

        lines.extend(
            [
                "",
                "---",
                "*Generated by NSForge - Where Neural Meets Symbolic*",
            ]
        )

        report = "\n".join(lines)

        return {
            "success": True,
            "report": report,
            "format": "markdown",
        }

    @mcp.tool()
    def generate_sympy_script(
        expressions: list[dict[str, str]],
        operations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a standalone SymPy script for a computation.

        This generates a complete, runnable Python script that can be
        executed independently to reproduce the derivation.

        Args:
            expressions: List of {"name": str, "expr": str, "description": str}
            operations: List of operations to perform
                {"op": "simplify|solve|diff|integrate", "input": str, ...}

        Returns:
            Complete Python script

        Example:
            generate_sympy_script(
                expressions=[
                    {"name": "momentum", "expr": "m1*v1 + m2*v2", "description": "Total momentum"},
                ],
                operations=[
                    {"op": "solve", "input": "momentum = (m1+m2)*v_f", "for": "v_f"},
                ]
            )
        """
        lines = [
            '"""',
            "Auto-generated SymPy script by NSForge",
            "Run with: python script.py",
            '"""',
            "",
            "import sympy as sp",
            "from sympy import symbols, sqrt, sin, cos, tan, pi, exp, log, Eq, solve, diff, integrate, simplify",
            "",
            "# Define symbols",
        ]

        try:
            prepared_expressions = [
                {
                    "name": validate_python_identifier(
                        item.get("name"), field=f"expressions[{index}].name"
                    ),
                    "expr": canonical_python_expression(
                        item.get("expr"), field=f"expressions[{index}].expr"
                    ),
                    "description": safe_python_comment(item.get("description", "")),
                    "symbols": python_expression_symbols(
                        item.get("expr"), field=f"expressions[{index}].expr"
                    ),
                }
                for index, item in enumerate(expressions)
            ]
            prepared_operations: list[dict[str, str]] = []
            for index, operation in enumerate(operations):
                operation_name = operation.get("op")
                if operation_name not in {"solve", "simplify", "diff", "integrate"}:
                    raise UnsafeCodegenInput(
                        f"operations[{index}].op must be solve, simplify, diff, or integrate"
                    )
                prepared: dict[str, str] = {
                    "op": str(operation_name),
                    "input": canonical_python_expression(
                        operation.get("input"), field=f"operations[{index}].input"
                    ),
                }
                if operation_name == "solve":
                    prepared["var"] = validate_python_identifier(
                        operation.get("for"), field=f"operations[{index}].for"
                    )
                elif operation_name in {"diff", "integrate"}:
                    prepared["var"] = validate_python_identifier(
                        operation.get("var", "x"), field=f"operations[{index}].var"
                    )
                prepared_operations.append(prepared)
        except (KeyError, TypeError, UnsafeCodegenInput) as exc:
            return {"success": False, "error": str(exc)}

        # Collect symbols from the same no-eval parse used to render source.
        all_symbols = set().union(*(item["symbols"] for item in prepared_expressions))
        all_symbols.update(prepared["var"] for prepared in prepared_operations if "var" in prepared)

        if all_symbols:
            lines.append(
                f"{', '.join(sorted(all_symbols))} = symbols('{' '.join(sorted(all_symbols))}')"
            )

        lines.append("")
        lines.append("# Define expressions")

        for expr in prepared_expressions:
            lines.append(f"# {expr['description']}")
            lines.append(f"{expr['name']} = {expr['expr']}")
            lines.append("")

        lines.append("# Operations")
        for i, op in enumerate(prepared_operations, 1):
            lines.append(f"# Operation {i}: {op['op']}")
            if op["op"] == "solve":
                lines.append(f"result_{i} = sp.solve({op['input']}, {op['var']})")
            elif op["op"] == "simplify":
                lines.append(f"result_{i} = sp.simplify({op['input']})")
            elif op["op"] == "diff":
                lines.append(f"result_{i} = sp.diff({op['input']}, {op['var']})")
            elif op["op"] == "integrate":
                lines.append(f"result_{i} = sp.integrate({op['input']}, {op['var']})")
            lines.append(f"print(f'Result {i}: {{result_{i}}}')")
            lines.append("")

        script = "\n".join(lines)

        return {
            "success": True,
            "script": script,
            "language": "python",
            "requires": ["sympy"],
        }
