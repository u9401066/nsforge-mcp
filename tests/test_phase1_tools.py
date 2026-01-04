"""
Test Phase 1 Advanced Simplification Tools

Tests all 10 new tools:
- P0: expand, factor, collect, trigsimp, powsimp, radsimp, combsimp
- P1: apart, cancel, together
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Direct import to avoid nsforge dependencies
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# Direct import of simplify module (avoid __init__.py chain)
sys.path.insert(0, str(src_path / "nsforge_mcp" / "tools"))
import simplify


class MockMCP:
    """Mock MCP server to collect tools."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


def test_all_tools():
    """Test all 10 Phase 1 tools."""
    print("═" * 80)
    print("🧪 Testing Phase 1 Advanced Simplification Tools (10 tools)")
    print("═" * 80)

    # Register tools
    mcp = MockMCP()
    simplify.register_simplify_tools(mcp)

    print(f"\n✅ Registered {len(mcp.tools)} tools:")
    for name in sorted(mcp.tools.keys()):
        print(f"   - {name}")

    # ═══════════════════════════════════════════════════════════════════════
    # P0 Tests - Basic Algebraic Simplification
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 80)
    print("📦 P0 - BASIC ALGEBRAIC SIMPLIFICATION (7 tools)")
    print("─" * 80)

    # Test 1: expand_expression
    print("\n1️⃣  expand_expression")
    result = mcp.tools["expand_expression"]("(x + 1)**2")
    print(f"   Input:  (x + 1)**2")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    assert "x**2" in result["result"] or "x^{2}" in result["latex"]
    print("   ✅ PASS")

    # Test 2: factor_expression
    print("\n2️⃣  factor_expression")
    result = mcp.tools["factor_expression"]("x**2 - 1")
    print(f"   Input:  x**2 - 1")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    assert "x - 1" in result["result"] and "x + 1" in result["result"]
    print("   ✅ PASS")

    # Test 3: collect_expression
    print("\n3️⃣  collect_expression")
    result = mcp.tools["collect_expression"]("x*y + x - 3 + 2*x**2", "x")
    print(f"   Input:  x*y + x - 3 + 2*x**2")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    print("   ✅ PASS")

    # Test 4: trigsimp_expression
    print("\n4️⃣  trigsimp_expression")
    result = mcp.tools["trigsimp_expression"]("sin(x)**2 + cos(x)**2")
    print(f"   Input:  sin(x)**2 + cos(x)**2")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    assert result["result"] == "1"
    print("   ✅ PASS")

    # Test 5: powsimp_expression
    print("\n5️⃣  powsimp_expression")
    result = mcp.tools["powsimp_expression"]("x**2 * x**3")
    print(f"   Input:  x**2 * x**3")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    assert "x**5" in result["result"]
    print("   ✅ PASS")

    # Test 6: radsimp_expression
    print("\n6️⃣  radsimp_expression")
    result = mcp.tools["radsimp_expression"]("1/(sqrt(3) + sqrt(2))")
    print(f"   Input:  1/(sqrt(3) + sqrt(2))")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    print("   ✅ PASS")

    # Test 7: combsimp_expression
    print("\n7️⃣  combsimp_expression")
    result = mcp.tools["combsimp_expression"]("factorial(n)/factorial(n - 2)")
    print(f"   Input:  factorial(n)/factorial(n - 2)")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    print("   ✅ PASS")

    # ═══════════════════════════════════════════════════════════════════════
    # P1 Tests - Rational Function Processing
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 80)
    print("📦 P1 - RATIONAL FUNCTION PROCESSING (3 tools)")
    print("─" * 80)

    # Test 8: apart_expression
    print("\n8️⃣  apart_expression")
    result = mcp.tools["apart_expression"]("(x**2 + 3*x + 2)/(x**2 + 5*x + 6)", "x")
    print(f"   Input:  (x**2 + 3*x + 2)/(x**2 + 5*x + 6)")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    print("   ✅ PASS")

    # Test 9: cancel_expression
    print("\n9️⃣  cancel_expression")
    result = mcp.tools["cancel_expression"]("(x**2 - 1)/(x - 1)")
    print(f"   Input:  (x**2 - 1)/(x - 1)")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    assert "x + 1" in result["result"]
    print("   ✅ PASS")

    # Test 10: together_expression
    print("\n🔟 together_expression")
    result = mcp.tools["together_expression"]("1/x + 1/y")
    print(f"   Input:  1/x + 1/y")
    print(f"   Output: {result['result']}")
    print(f"   LaTeX:  {result['latex']}")
    assert result["success"]
    print("   ✅ PASS")

    # ═══════════════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 80)
    print("✅ ALL 10 TOOLS PASSED!")
    print("═" * 80)
    print("\nPhase 1 Implementation Summary:")
    print("  P0 (Basic Algebra):        7 tools ✅")
    print("  P1 (Rational Functions):   3 tools ✅")
    print("  Total:                    10 tools ✅")
    print("\n🎉 Ready for production use!")


if __name__ == "__main__":
    try:
        test_all_tools()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
