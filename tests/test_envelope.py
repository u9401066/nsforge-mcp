"""Regression tests for the uniform tool error envelope."""

import inspect
from collections.abc import Callable
from typing import Any

import pytest
from mcp.types import CallToolResult

from nsforge_mcp.envelope import EnvelopeMCP, with_error_envelope
from nsforge_mcp.tool_contract import ToolProfile


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}
        self.options: dict[str, dict[str, Any]] = {}

    def tool(self, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            self.options[fn.__name__] = kwargs
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
    # inspect.signature follows __wrapped__, so MCPServer sees the real params.
    assert list(inspect.signature(wrapped).parameters) == ["expression", "variable"]


def test_envelope_mcp_wraps_registered_tools() -> None:
    fake = _FakeMCP()
    env = EnvelopeMCP(fake, enforce_registry=False)

    @env.tool()
    def crash() -> dict[str, Any]:
        raise RuntimeError("boom")

    result = fake.tools["crash"]()  # registered under its real name, enveloped
    assert isinstance(result, CallToolResult)
    assert result.is_error is True
    assert result.structured_content["success"] is False
    assert result.structured_content["error"]["type"] == "RuntimeError"


def test_handled_failure_uses_protocol_error_channel_without_losing_payload() -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, enforce_registry=False).tool()
    def handled_failure() -> dict[str, Any]:
        return {"success": False, "error": "expected failure", "detail": 7}

    result = fake.tools["handled_failure"]()
    assert isinstance(result, CallToolResult)
    assert result.is_error is True
    assert result.structured_content == {
        "success": False,
        "error": "expected failure",
        "detail": 7,
    }


def test_negative_verification_without_error_stays_normal_result() -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, enforce_registry=False).tool()
    def negative_verification() -> dict[str, Any]:
        return {"verified": False, "message": "not equal"}

    assert fake.tools["negative_verification"]() == {
        "verified": False,
        "message": "not equal",
    }


def test_internal_resource_link_sentinel_becomes_content_without_payload_leak() -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, enforce_registry=False).tool()
    def linked_result() -> dict[str, Any]:
        return {
            "success": True,
            "artifact_id": "abc",
            "_resource_links": [
                {
                    "name": "artifact-abc",
                    "title": "Verified artifact",
                    "uri": "nsforge://artifacts/abc",
                    "mime_type": "text/plain",
                    "size": 3,
                }
            ],
        }

    result = fake.tools["linked_result"]()
    assert isinstance(result, CallToolResult)
    assert result.is_error is False
    assert result.structured_content == {"success": True, "artifact_id": "abc"}
    assert "_resource_links" not in getattr(result.content[0], "text", "")
    link = result.content[1]
    assert link.type == "resource_link"
    assert str(link.uri) == "nsforge://artifacts/abc"
    assert link.mime_type == "text/plain"


@pytest.mark.parametrize("resource_links", [[], [{"name": "missing-uri"}]])
def test_empty_or_invalid_resource_links_never_leak_sentinel(
    resource_links: list[dict[str, str]],
) -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, enforce_registry=False).tool()
    def linked_result() -> dict[str, Any]:
        return {"success": True, "artifact_id": "abc", "_resource_links": resource_links}

    assert fake.tools["linked_result"]() == {"success": True, "artifact_id": "abc"}


@pytest.mark.parametrize("profile", ["legacy", "full"])
def test_compat_profiles_preserve_frozen_limit_parse_error(profile: ToolProfile) -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, profile=profile, enforce_registry=False).tool()
    def calculate_limit(expression: str) -> dict[str, Any]:
        _ = expression
        return {"success": False, "error": "expression has unmatched or misordered brackets"}

    result = fake.tools["calculate_limit"]("(")
    assert isinstance(result, CallToolResult)
    assert result.structured_content == {
        "success": False,
        "error": "('unexpected EOF in multi-line statement', (1, 0))",
    }


def test_compact_profile_keeps_safe_limit_parse_error() -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, profile="workflow", enforce_registry=False).tool()
    def calculate_limit(expression: str) -> dict[str, Any]:
        _ = expression
        return {"success": False, "error": "expression has unmatched or misordered brackets"}

    result = fake.tools["calculate_limit"]("(")
    assert isinstance(result, CallToolResult)
    assert result.structured_content == {
        "success": False,
        "error": "expression has unmatched or misordered brackets",
    }


def test_envelope_mcp_adds_v2_discovery_metadata() -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, enforce_registry=False).tool()
    def parse_expression() -> dict[str, Any]:
        return {"success": True}

    options = fake.options["parse_expression"]
    assert options["title"] == "Parse Expression"
    assert options["structured_output"] is True
    assert options["annotations"].read_only_hint is True
    assert options["icons"]
    assert options["meta"]["org.nsforge/responseEnvelope"] == "v1-compatible"


@pytest.mark.asyncio
async def test_async_envelope_preserves_coroutine_and_error_contract() -> None:
    fake = _FakeMCP()

    @EnvelopeMCP(fake, enforce_registry=False).tool()
    async def async_crash() -> dict[str, Any]:
        raise RuntimeError("async boom")

    registered = fake.tools["async_crash"]
    assert inspect.iscoroutinefunction(registered)
    result = await registered()
    assert isinstance(result, CallToolResult)
    assert result.is_error is True
    assert result.structured_content["error"]["message"] == "async boom"


def test_envelope_mcp_delegates_other_attributes() -> None:
    fake = _FakeMCP()
    fake.tools["seed"] = lambda: {"ok": True}  # type: ignore[assignment]
    env = EnvelopeMCP(fake)
    assert env.tools["seed"]() == {"ok": True}  # delegated attribute access
