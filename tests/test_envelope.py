"""Regression tests for the uniform tool error envelope."""

import inspect
from collections.abc import Callable
from typing import Any

from nsforge_mcp.envelope import EnvelopeMCP, with_error_envelope


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_success_passes_through_unchanged() -> None:
    @with_error_envelope
    def ok(x: int) -> dict[str, Any]:
        return {"success": True, "value": x}

    assert ok(3) == {"success": True, "value": 3}


def test_unhandled_exception_becomes_structured_error() -> None:
    @with_error_envelope
    def boom() -> dict[str, Any]:
        raise ValueError("nope")

    result = boom()
    assert result["success"] is False
    assert result["error"]["type"] == "ValueError"
    assert result["error"]["message"] == "nope"
    assert result["error"]["tool"] == "boom"


def test_envelope_preserves_name_and_signature() -> None:
    def sample(expression: str, variable: str = "x") -> dict[str, Any]:
        return {"expression": expression, "variable": variable}

    wrapped = with_error_envelope(sample)
    assert wrapped.__name__ == "sample"
    # inspect.signature follows __wrapped__, so FastMCP sees the real params.
    assert list(inspect.signature(wrapped).parameters) == ["expression", "variable"]


def test_envelope_mcp_wraps_registered_tools() -> None:
    fake = _FakeMCP()
    env = EnvelopeMCP(fake)

    @env.tool()
    def crash() -> dict[str, Any]:
        raise RuntimeError("boom")

    result = fake.tools["crash"]()  # registered under its real name, enveloped
    assert result["success"] is False
    assert result["error"]["type"] == "RuntimeError"


def test_envelope_mcp_delegates_other_attributes() -> None:
    fake = _FakeMCP()
    fake.tools["seed"] = lambda: {"ok": True}  # type: ignore[assignment]
    env = EnvelopeMCP(fake)
    assert env.tools["seed"]() == {"ok": True}  # delegated attribute access
