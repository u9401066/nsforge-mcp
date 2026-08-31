"""Safe OpenTelemetry correlation metadata at the MCP tool boundary."""

from __future__ import annotations

from typing import Any

from mcp.types import CallToolResult, TextContent

from nsforge_mcp.config import SurfaceConfig
from nsforge_mcp.server import _annotate_result_span, _annotate_tool_span


class _RecordingSpan:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def set_attribute(self, name: str, value: object) -> None:
        self.attributes[name] = value


def _surface(tmp_path: Any) -> SurfaceConfig:
    return SurfaceConfig(
        profile="workflow",
        legacy_music=False,
        tenant_id="tenant-a",
        tenant_scope_mode="configured",
        artifact_root=tmp_path / "artifacts",
        run_store_path=tmp_path / "runs.sqlite3",
    )


def test_tool_span_correlates_opaque_ids_without_sensitive_arguments(tmp_path: Any) -> None:
    span = _RecordingSpan()
    _annotate_tool_span(
        span,
        name="derivation_show",
        arguments={
            "session_id": "session-123",
            "expression": "secret-expression",
            "code": "secret-code",
            "token": "secret-token",
        },
        surface=_surface(tmp_path),
    )

    assert span.attributes == {
        "nsforge.tool.name": "derivation_show",
        "nsforge.profile": "workflow",
        "nsforge.tenant_id": "tenant-a",
        "nsforge.session_id": "session-123",
    }
    assert "secret" not in repr(span.attributes)


def test_result_span_accepts_only_safe_kernel_correlation_ids() -> None:
    span = _RecordingSpan()
    result = CallToolResult(
        content=[TextContent(type="text", text="{}")],
        structured_content={
            "run_id": "run-123",
            "correlation_id": "correlation-456",
            "generated_code": "secret-code",
        },
        is_error=False,
    )
    _annotate_result_span(span, result)

    assert span.attributes == {
        "nsforge.run_id": "run-123",
        "nsforge.correlation_id": "correlation-456",
    }


def test_caller_payload_cannot_inject_unbounded_span_values(tmp_path: Any) -> None:
    span = _RecordingSpan()
    _annotate_tool_span(
        span,
        name="derivation_show",
        arguments={"session_id": "not/a/safe/id"},
        surface=_surface(tmp_path),
    )
    _annotate_result_span(
        span,
        CallToolResult(
            content=[TextContent(type="text", text="{}")],
            structured_content={"run_id": "x" * 1000, "correlation_id": "bad value"},
        ),
    )

    assert "nsforge.session_id" not in span.attributes
    assert "nsforge.run_id" not in span.attributes
    assert "nsforge.correlation_id" not in span.attributes
