"""Regression tests for the DI composition root."""

from nsforge.domain.derivation_session import SessionManager, get_session_manager
from nsforge.domain.services import SymbolicEngine, Verifier
from nsforge.infrastructure.derivation_repository import DerivationRepository, get_repository
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier
from nsforge_mcp.composition import Services, build_services, get_services


def test_get_services_is_singleton() -> None:
    # The object graph is wired exactly once and shared.
    assert get_services() is get_services()


def test_services_expose_the_ports() -> None:
    services = build_services()
    assert isinstance(services, Services)
    assert isinstance(services.engine, SymPyEngine)
    assert isinstance(services.verifier, BasicVerifier)
    assert isinstance(services.session_manager, SessionManager)
    assert isinstance(services.repository, DerivationRepository)


def test_engine_and_verifier_satisfy_their_ports() -> None:
    services = get_services()
    assert isinstance(services.engine, SymbolicEngine)
    assert isinstance(services.verifier, Verifier)


def test_stores_reference_the_shared_singletons() -> None:
    # The root points at the SAME store singletons the stateful tools use, so
    # there is a single wiring point for the whole server.
    services = get_services()
    assert services.session_manager is get_session_manager()
    assert services.repository is get_repository()
