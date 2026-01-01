"""
SymPy Engine Implementation

Concrete implementation of the SymbolicEngine interface using SymPy.
"""

from typing import Any
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

from nsforge.domain.entities import Expression, ExpressionType
from nsforge.domain.value_objects import MathContext, SimplificationLevel
from nsforge.domain.services import SymbolicEngine


class SymPyEngine(SymbolicEngine):
    """
    SymPy-based implementation of the symbolic computation engine.
    
    This is the primary symbolic engine used by NSForge.
    """
    
    # Parser transformations for flexible input
    TRANSFORMATIONS = (
        standard_transformations + 
        (implicit_multiplication_application, convert_xor)
    )
    
    def parse(self, expr_str: str, context: MathContext | None = None) -> Expression:
        """Parse a string into an Expression using SymPy."""
        try:
            # Get symbols with assumptions if provided
            local_dict = self._get_local_dict(context)
            
            # Parse the expression
            sympy_expr = parse_expr(
                expr_str,
                local_dict=local_dict,
                transformations=self.TRANSFORMATIONS,
                evaluate=False,
            )
            
            # Determine expression type
            expr_type = self._classify_expression(sympy_expr)
            
            return Expression(
                raw=str(sympy_expr),
                latex=sp.latex(sympy_expr),
                sympy_expr=sympy_expr,
                expr_type=expr_type,
            )
            
        except Exception as e:
            # Return invalid expression on parse error
            return Expression(
                raw=expr_str,
                latex="",
                sympy_expr=None,
                expr_type=ExpressionType.UNKNOWN,
            )
    
    def simplify(self, expr: Expression, context: MathContext | None = None) -> Expression:
        """Simplify an expression using SymPy."""
        if not expr.is_valid:
            return expr
        
        level = context.simplify_level if context else SimplificationLevel.BASIC
        
        match level:
            case SimplificationLevel.NONE:
                result = expr.sympy_expr
            case SimplificationLevel.BASIC:
                result = sp.simplify(expr.sympy_expr)
            case SimplificationLevel.FULL:
                result = sp.simplify(sp.expand(expr.sympy_expr))
            case SimplificationLevel.TRIGONOMETRIC:
                result = sp.trigsimp(expr.sympy_expr)
            case SimplificationLevel.RADICAL:
                result = sp.radsimp(expr.sympy_expr)
            case _:
                result = sp.simplify(expr.sympy_expr)
        
        return Expression(
            raw=str(result),
            latex=sp.latex(result),
            sympy_expr=result,
            expr_type=expr.expr_type,
        )
    
    def differentiate(
        self,
        expr: Expression,
        variable: str,
        order: int = 1,
        context: MathContext | None = None,
    ) -> Expression:
        """Differentiate an expression using SymPy."""
        if not expr.is_valid:
            return expr
        
        var = sp.Symbol(variable, **self._get_assumptions(variable, context))
        result = sp.diff(expr.sympy_expr, var, order)
        
        return Expression(
            raw=str(result),
            latex=sp.latex(result),
            sympy_expr=result,
            expr_type=ExpressionType.CALCULUS,
        )
    
    def integrate(
        self,
        expr: Expression,
        variable: str,
        lower: Any = None,
        upper: Any = None,
        context: MathContext | None = None,
    ) -> Expression:
        """Integrate an expression using SymPy."""
        if not expr.is_valid:
            return expr
        
        var = sp.Symbol(variable, **self._get_assumptions(variable, context))
        
        if lower is not None and upper is not None:
            # Definite integral
            lower_val = self._to_sympy(lower)
            upper_val = self._to_sympy(upper)
            result = sp.integrate(expr.sympy_expr, (var, lower_val, upper_val))
        else:
            # Indefinite integral
            result = sp.integrate(expr.sympy_expr, var)
        
        return Expression(
            raw=str(result),
            latex=sp.latex(result),
            sympy_expr=result,
            expr_type=ExpressionType.CALCULUS,
        )
    
    def solve(
        self,
        equation: Expression,
        variable: str,
        context: MathContext | None = None,
    ) -> list[Expression]:
        """Solve an equation for a variable using SymPy."""
        if not equation.is_valid:
            return []
        
        var = sp.Symbol(variable, **self._get_assumptions(variable, context))
        
        # Handle both equations and expressions (expr = 0)
        if isinstance(equation.sympy_expr, sp.Equality):
            solutions = sp.solve(equation.sympy_expr, var)
        else:
            solutions = sp.solve(equation.sympy_expr, var)
        
        return [
            Expression(
                raw=str(sol),
                latex=sp.latex(sol),
                sympy_expr=sol,
                expr_type=ExpressionType.ALGEBRAIC,
            )
            for sol in solutions
        ]
    
    def substitute(
        self,
        expr: Expression,
        substitutions: dict[str, Any],
        context: MathContext | None = None,
    ) -> Expression:
        """Substitute values into an expression using SymPy."""
        if not expr.is_valid:
            return expr
        
        # Convert substitutions to SymPy format
        subs_dict = {}
        for var_name, value in substitutions.items():
            var = sp.Symbol(var_name, **self._get_assumptions(var_name, context))
            subs_dict[var] = self._to_sympy(value)
        
        result = expr.sympy_expr.subs(subs_dict)
        
        return Expression(
            raw=str(result),
            latex=sp.latex(result),
            sympy_expr=result,
            expr_type=expr.expr_type,
        )
    
    def equals(
        self,
        expr1: Expression,
        expr2: Expression,
        context: MathContext | None = None,
    ) -> bool:
        """Check if two expressions are mathematically equal."""
        if not expr1.is_valid or not expr2.is_valid:
            return False
        
        # Try simplifying the difference
        diff = sp.simplify(expr1.sympy_expr - expr2.sympy_expr)
        if diff == 0:
            return True
        
        # Try expanding and simplifying
        diff_expanded = sp.simplify(sp.expand(expr1.sympy_expr - expr2.sympy_expr))
        return diff_expanded == 0
    
    def _get_local_dict(self, context: MathContext | None) -> dict[str, Any]:
        """Get local dictionary for parsing with symbol assumptions."""
        local_dict: dict[str, Any] = {}
        
        if context and context.assumptions:
            for var_name, assumptions in context.assumptions.items():
                local_dict[var_name] = sp.Symbol(var_name, **assumptions)
        
        return local_dict
    
    def _get_assumptions(self, variable: str, context: MathContext | None) -> dict[str, bool]:
        """Get assumptions for a specific variable."""
        if context and variable in context.assumptions:
            return context.assumptions[variable]
        return {}
    
    def _to_sympy(self, value: Any) -> Any:
        """Convert a value to SymPy format."""
        if isinstance(value, str):
            return parse_expr(value, transformations=self.TRANSFORMATIONS)
        return sp.sympify(value)
    
    def _classify_expression(self, expr: Any) -> ExpressionType:
        """Classify the type of a SymPy expression."""
        if isinstance(expr, (sp.Derivative, sp.Integral)):
            return ExpressionType.CALCULUS
        if isinstance(expr, (sp.Equality, sp.Rel)):
            return ExpressionType.EQUATION
        if isinstance(expr, sp.MatrixBase):
            return ExpressionType.MATRIX
        return ExpressionType.ALGEBRAIC
