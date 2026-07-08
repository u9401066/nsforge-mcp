"""Uniform error envelope for MCP tools.

A production MCP tool should never surface an unstructured crash. This wraps every
registered tool so an *unhandled* exception becomes a consistent, logged,
structured error dict — applied once at the registration boundary, without
touching any tool body or changing their success / handled-error output.

Signatures (and therefore FastMCP's generated JSON schema) are preserved via
``functools.wraps``, which sets ``__wrapped__`` for ``inspect.signature`` to
follow and copies ``__annotations__`` for ``get_type_hints``.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, cast

logger = logging.getLogger("nsforge")


def with_error_envelope(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a tool so an unhandled exception returns a structured error dict."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
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

    return wrapper


class EnvelopeMCP:
    """Proxy over a FastMCP instance that wraps every ``@tool()`` with the envelope.

    All other attribute access is delegated, so it is a drop-in for the tool
    registration functions.
    """

    def __init__(self, mcp: Any) -> None:
        self._mcp = mcp

    def tool(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        register = self._mcp.tool(*args, **kwargs)

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            return cast("Callable[..., Any]", register(with_error_envelope(fn)))

        return decorator

    def __getattr__(self, name: str) -> Any:
        return getattr(self._mcp, name)
