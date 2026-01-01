"""
NSForge - Neurosymbolic Forge Core Library

Where Neural Meets Symbolic.

This is the core domain library for symbolic reasoning,
independent of the MCP transport layer.
"""

__version__ = "0.1.0"

from nsforge.domain.entities import Expression, Derivation, DerivationStep
from nsforge.domain.value_objects import MathContext, VerificationResult
from nsforge.application.use_cases import (
    CalculateUseCase,
    SimplifyUseCase,
    DeriveUseCase,
    VerifyUseCase,
)

__all__ = [
    # Entities
    "Expression",
    "Derivation",
    "DerivationStep",
    # Value Objects
    "MathContext",
    "VerificationResult",
    # Use Cases
    "CalculateUseCase",
    "SimplifyUseCase", 
    "DeriveUseCase",
    "VerifyUseCase",
]
