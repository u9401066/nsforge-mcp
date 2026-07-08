"""Composition root — the single place the object graph is wired.

In a hexagonal / DDD architecture the outermost layer owns construction: it
builds the concrete adapters and hands them to the application layer. NSForge's
ports (:class:`SymbolicEngine`, :class:`Verifier`) and its process-wide stores
(:class:`SessionManager`, :class:`DerivationRepository`) are assembled here
exactly once and shared, instead of being ``new``-ed ad hoc inside every tool
call.

Both adapters are stateless (pure request/response), so a single shared instance
is safe and avoids re-constructing them — and re-importing their transitive
machinery — on every ``task_run``. The two stores are already singletons; the
root simply references the same instances so there is one documented wiring
point for the whole server.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from nsforge.domain.derivation_session import SessionManager, get_session_manager
from nsforge.domain.services import SymbolicEngine, Verifier
from nsforge.infrastructure.derivation_repository import DerivationRepository, get_repository
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier

# Default on-disk locations. These MUST match the paths used by the stateful tool
# modules (derivation.py) so every caller shares one singleton per store.
SESSIONS_DIR = Path("derivation_sessions")
FORMULAS_DIR = Path("formulas")


@dataclass(frozen=True)
class Services:
    """The wired object graph shared across MCP tool calls."""

    engine: SymbolicEngine
    verifier: Verifier
    session_manager: SessionManager
    repository: DerivationRepository


def build_services() -> Services:
    """Construct the object graph. Invoked once by :func:`get_services`."""
    return Services(
        engine=SymPyEngine(),
        verifier=BasicVerifier(),
        session_manager=get_session_manager(SESSIONS_DIR),
        repository=get_repository(FORMULAS_DIR),
    )


_services: Services | None = None
_services_lock = threading.Lock()


def get_services() -> Services:
    """Return the process-wide :class:`Services`, building it once (thread-safe)."""
    global _services
    if _services is None:
        with _services_lock:
            if _services is None:
                _services = build_services()
    return _services
