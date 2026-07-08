"""Explicit session_id addressing for derivation tools (multi-agent Tier 0).

Every stateful tool now accepts ``session_id``: with it, a caller addresses its
own session directly (safe when many agents share the server); without it, the
process-current session is used (single-client back-compatibility).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

import nsforge_mcp.tools.derivation as derivation
from nsforge.domain.derivation_session import SessionManager
from nsforge_mcp.tools.derivation import register_derivation_tools


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.fixture
def tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[dict[str, Callable[..., Any]]]:
    # Inject a temp-dir session manager at the seam the tools call (_get_manager),
    # isolating the test from the real composition-root singleton.
    manager = SessionManager(sessions_dir=tmp_path)
    monkeypatch.setattr(derivation, "_get_manager", lambda: manager)
    saved_current = derivation._current_session
    derivation._set_current_session(None)
    mcp = _FakeMCP()
    register_derivation_tools(mcp)
    try:
        yield mcp.tools
    finally:
        derivation._set_current_session(saved_current)


def test_session_id_targets_its_own_session(tools: dict[str, Callable[..., Any]]) -> None:
    alpha = tools["derivation_start"](name="alpha")["session_id"]
    beta = tools["derivation_start"](name="beta")["session_id"]  # beta becomes "current"
    assert alpha != beta

    # Address session alpha explicitly even though beta is the current session.
    tools["derivation_load_formula"]("x + 1", session_id=alpha)

    shown_alpha = tools["derivation_show"](session_id=alpha)
    shown_beta = tools["derivation_show"](session_id=beta)
    assert "x" in shown_alpha.get("sympy", "")  # alpha got the formula
    assert shown_beta.get("sympy", "") == ""  # beta is untouched (no cross-talk)


def test_omitted_session_id_falls_back_to_current(tools: dict[str, Callable[..., Any]]) -> None:
    tools["derivation_start"](name="only")  # becomes the current session
    tools["derivation_load_formula"]("y + 2")  # no session_id -> current
    shown = tools["derivation_show"]()  # no session_id -> current
    assert "y" in shown.get("sympy", "")
