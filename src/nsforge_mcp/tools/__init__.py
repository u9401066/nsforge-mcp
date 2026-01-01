"""
NSForge MCP Tools

Tool modules for the MCP server.

Architecture:
- expression.py: Parse and validate mathematical expressions
- calculate.py: Symbolic computation (simplify, solve, diff, integrate)
- verify.py: Verification (equality, reverse, dimensions)
- codegen.py: Generate Python code and reports from derivations

Design Principles:
1. No hard-coded formulas - all expressions come from User/Agent
2. Use SymPy for all symbolic computation
3. Use sympy.physics.units for dimensional analysis
4. Generated code uses SymPy (not Agent-generated)
"""

from nsforge_mcp.tools.expression import register_expression_tools
from nsforge_mcp.tools.calculate import register_calculate_tools
from nsforge_mcp.tools.verify import register_verify_tools
from nsforge_mcp.tools.codegen import register_codegen_tools


def register_all_tools(mcp) -> None:
    """Register all NSForge tools with the MCP server."""
    register_expression_tools(mcp)
    register_calculate_tools(mcp)
    register_verify_tools(mcp)
    register_codegen_tools(mcp)
