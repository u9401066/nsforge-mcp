"""Uniform error envelope for MCP tools.

A production MCP tool should never surface an unstructured crash. This wraps every
registered tool so an *unhandled* exception becomes a consistent, logged,
structured error dict — applied once at the registration boundary, without
touching any tool body or changing their success / handled-error output.

Signatures (and therefore MCPServer's generated JSON schema) are preserved via
``functools.wraps``, which sets ``__wrapped__`` for ``inspect.signature`` to
follow and copies ``__annotations__`` for ``get_type_hints``.
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
from collections.abc import Callable
from typing import Any, cast

from mcp.types import CallToolResult, Icon, TextContent, ToolAnnotations

from nsforge_mcp.tool_contract import NSFORGE_ICON_URL, contract_for, tool_meta

logger = logging.getLogger("nsforge")


def with_error_envelope(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a sync or async tool with the legacy-compatible error envelope."""

    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:
                return _unexpected_error(fn, exc)

        return async_wrapper

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            return _unexpected_error(fn, exc)

    return wrapper


def _unexpected_error(fn: Callable[..., Any], exc: Exception) -> dict[str, Any]:
    """Log and serialize a crash exactly as the v1 server did."""
    name = getattr(fn, "__name__", "?")
    logger.exception("tool %s raised", name)
    return {
        "success": False,
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
            "tool": name,
        },
    }


def _protocol_result(result: Any) -> Any:
    """Mark an application error on MCP's error channel without changing its body.

    NSForge historically returned handled failures as JSON dictionaries.  MCP 2
    can additionally flag them for hosts via ``isError``.  The original text and
    ``structuredContent`` remain available verbatim for older integrations.
    A negative mathematical/verification result without an ``error`` field is a
    valid tool outcome and deliberately stays on the success channel.
    """
    if not isinstance(result, dict) or "error" not in result:
        return result
    failed = result.get("success") is False or result.get("verified") is False
    if not failed:
        return result
    text = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=result,
        is_error=True,
    )


def _with_protocol_envelope(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Compose the historical Python envelope with MCP's error channel."""
    enveloped = with_error_envelope(fn)
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _protocol_result(await enveloped(*args, **kwargs))

        return async_wrapper

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return _protocol_result(enveloped(*args, **kwargs))

    return wrapper


class EnvelopeMCP:
    """Proxy over an MCPServer that wraps and describes every ``@tool()``.

    All other attribute access is delegated, so it is a drop-in for the tool
    registration functions.
    """

    def __init__(self, mcp: Any) -> None:
        self._mcp = mcp

    def tool(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            module = fn.__module__.rsplit(".", maxsplit=1)[-1]
            name = str(kwargs.get("name") or fn.__name__)
            contract = contract_for(name, module)
            options = {
                "title": contract.title,
                "annotations": ToolAnnotations(
                    title=contract.title,
                    read_only_hint=contract.read_only_hint,
                    destructive_hint=contract.destructive_hint,
                    idempotent_hint=contract.idempotent_hint,
                    open_world_hint=contract.open_world_hint,
                ),
                "icons": [Icon(src=NSFORGE_ICON_URL, mime_type="image/svg+xml")],
                "meta": tool_meta(module),
                "structured_output": True,
                **kwargs,
            }
            register = self._mcp.tool(*args, **options)
            return cast("Callable[..., Any]", register(_with_protocol_envelope(fn)))

        return decorator

    def __getattr__(self, name: str) -> Any:
        return getattr(self._mcp, name)
