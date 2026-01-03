"""
Tests for SymPy Engine Implementation
"""

import pytest

# Skip all tests if sympy not installed
pytest.importorskip("sympy")

from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.domain.value_objects import MathContext, SimplificationLevel


@pytest.fixture
def engine():
    """Create a SymPyEngine instance."""
    return SymPyEngine()


class TestSymPyEngineParsing:
    """Tests for expression parsing."""
    
    def test_parse_simple(self, engine):
        """Test parsing simple expression."""
        expr = engine.parse("x**2 + 1")
        assert expr.is_valid
        assert "x**2" in expr.raw
    
    def test_parse_with_functions(self, engine):
        """Test parsing with mathematical functions."""
        expr = engine.parse("sin(x) + cos(x)")
        assert expr.is_valid
    
    def test_parse_invalid(self, engine):
        """Test parsing invalid expression."""
        expr = engine.parse("x +++ @#$ y")  # Clearly invalid
        assert not expr.is_valid
    
    def test_implicit_multiplication(self, engine):
        """Test implicit multiplication parsing."""
        expr = engine.parse("2x")  # Should parse as 2*x
        assert expr.is_valid


class TestSymPyEngineSimplification:
    """Tests for expression simplification."""
    
    def test_simplify_polynomial(self, engine):
        """Test simplifying polynomial."""
        expr = engine.parse("x**2 + 2*x + 1")
        result = engine.simplify(expr)
        # Should simplify to (x + 1)**2
        assert result.is_valid
    
    def test_simplify_trig(self, engine):
        """Test trigonometric simplification."""
        ctx = MathContext(simplify_level=SimplificationLevel.TRIGONOMETRIC)
        expr = engine.parse("sin(x)**2 + cos(x)**2")
        result = engine.simplify(expr, ctx)
        assert result.raw == "1"


class TestSymPyEngineCalculus:
    """Tests for calculus operations."""
    
    def test_differentiate_polynomial(self, engine):
        """Test differentiating polynomial."""
        expr = engine.parse("x**3")
        result = engine.differentiate(expr, "x")
        assert result.is_valid
        assert "3" in result.raw and "x**2" in result.raw
    
    def test_differentiate_trig(self, engine):
        """Test differentiating trig function."""
        expr = engine.parse("sin(x)")
        result = engine.differentiate(expr, "x")
        assert "cos" in result.raw
    
    def test_integrate_polynomial(self, engine):
        """Test integrating polynomial."""
        expr = engine.parse("x**2")
        result = engine.integrate(expr, "x")
        assert result.is_valid
        assert "x**3" in result.raw
    
    def test_definite_integral(self, engine):
        """Test definite integration."""
        expr = engine.parse("x")
        result = engine.integrate(expr, "x", 0, 1)
        # ∫₀¹ x dx = 1/2
        assert "1/2" in result.raw or result.raw == "1/2"


class TestSymPyEngineSolve:
    """Tests for equation solving."""
    
    def test_solve_linear(self, engine):
        """Test solving linear equation."""
        expr = engine.parse("x - 5")  # x - 5 = 0
        solutions = engine.solve(expr, "x")
        assert len(solutions) == 1
        assert solutions[0].raw == "5"
    
    def test_solve_quadratic(self, engine):
        """Test solving quadratic equation."""
        expr = engine.parse("x**2 - 4")  # x² - 4 = 0
        solutions = engine.solve(expr, "x")
        assert len(solutions) == 2


class TestSymPyEngineSubstitution:
    """Tests for variable substitution."""
    
    def test_substitute_number(self, engine):
        """Test substituting a number."""
        expr = engine.parse("x**2 + x")
        result = engine.substitute(expr, {"x": 2})
        # 2² + 2 = 6
        assert result.raw == "6"
    
    def test_substitute_expression(self, engine):
        """Test substituting an expression."""
        expr = engine.parse("f(x)")
        # Note: This tests symbolic substitution
        result = engine.substitute(expr, {"x": "a + b"})
        assert result.is_valid


class TestSymPyEngineEquality:
    """Tests for expression equality checking."""
    
    def test_equals_identical(self, engine):
        """Test identical expressions."""
        expr1 = engine.parse("x + 1")
        expr2 = engine.parse("x + 1")
        assert engine.equals(expr1, expr2)
    
    def test_equals_equivalent(self, engine):
        """Test equivalent expressions."""
        expr1 = engine.parse("(x + 1)**2")
        expr2 = engine.parse("x**2 + 2*x + 1")
        assert engine.equals(expr1, expr2)
    
    def test_not_equals(self, engine):
        """Test non-equal expressions."""
        expr1 = engine.parse("x")
        expr2 = engine.parse("x + 1")
        assert not engine.equals(expr1, expr2)
