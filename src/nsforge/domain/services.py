"""
NSForge Domain Services

Domain services encapsulate domain logic that doesn't naturally
fit within a single entity or value object.
"""

from abc import ABC, abstractmethod
from typing import Any

from nsforge.domain.entities import Derivation, Expression
from nsforge.domain.value_objects import MathContext, VerificationResult


class SymbolicEngine(ABC):
    """
    Abstract interface for symbolic computation engine.

    This is a domain service interface - the actual implementation
    lives in the infrastructure layer (e.g., SymPyEngine).
    """

    @abstractmethod
    def parse(self, expr_str: str, context: MathContext | None = None) -> Expression:
        """Parse a string into an Expression."""
        ...

    @abstractmethod
    def simplify(self, expr: Expression, context: MathContext | None = None) -> Expression:
        """Simplify an expression."""
        ...

    @abstractmethod
    def differentiate(
        self,
        expr: Expression,
        variable: str,
        order: int = 1,
        context: MathContext | None = None
    ) -> Expression:
        """Differentiate an expression."""
        ...

    @abstractmethod
    def integrate(
        self,
        expr: Expression,
        variable: str,
        lower: Any = None,
        upper: Any = None,
        context: MathContext | None = None
    ) -> Expression:
        """Integrate an expression."""
        ...

    @abstractmethod
    def solve(
        self,
        equation: Expression,
        variable: str,
        context: MathContext | None = None
    ) -> list[Expression]:
        """Solve an equation for a variable."""
        ...

    @abstractmethod
    def substitute(
        self,
        expr: Expression,
        substitutions: dict[str, Any],
        context: MathContext | None = None
    ) -> Expression:
        """Substitute values into an expression."""
        ...

    @abstractmethod
    def equals(
        self,
        expr1: Expression,
        expr2: Expression,
        context: MathContext | None = None
    ) -> bool:
        """Check if two expressions are mathematically equal."""
        ...


class Verifier(ABC):
    """
    Abstract interface for derivation verification.

    Verifies that mathematical derivations are correct.
    """

    @abstractmethod
    def verify_step(
        self,
        step_input: Expression,
        step_output: Expression,
        operation: str,
        context: MathContext | None = None
    ) -> VerificationResult:
        """Verify a single derivation step."""
        ...

    @abstractmethod
    def verify_derivation(
        self,
        derivation: Derivation,
        context: MathContext | None = None
    ) -> VerificationResult:
        """Verify an entire derivation."""
        ...

    @abstractmethod
    def check_dimensions(
        self,
        expr: Expression,
        expected_dimension: str | None = None
    ) -> VerificationResult:
        """Check dimensional consistency."""
        ...


class FormulaRepository(ABC):
    """
    Abstract interface for formula knowledge base.

    Provides access to known formulas and their derivations.
    """

    @abstractmethod
    def find_formula(
        self,
        name: str,
        domain: str | None = None
    ) -> dict[str, Any] | None:
        """Find a formula by name."""
        ...

    @abstractmethod
    def list_formulas(
        self,
        domain: str | None = None,
        tags: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """List available formulas."""
        ...

    @abstractmethod
    def get_derivation(
        self,
        formula_name: str
    ) -> Derivation | None:
        """Get the derivation of a formula if available."""
        ...
