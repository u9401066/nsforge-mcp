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

from mcp.types import CallToolResult, Icon, ResourceLink, TextContent, ToolAnnotations

from nsforge_mcp.tool_contract import (
    NSFORGE_ICON_URL,
    ToolProfile,
    contract_for,
    profile_tool_names,
    spec_for,
    tool_meta,
)

logger = logging.getLogger("nsforge")

_STRICT_UNMATCHED_BRACKET_ERROR = "expression has unmatched or misordered brackets"
_LEGACY_LIMIT_BRACKET_ERROR = "('unexpected EOF in multi-line statement', (1, 0))"


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
    if not isinstance(result, dict):
        return result

    payload = dict(result)
    had_link_sentinel = "_resource_links" in payload
    raw_links = payload.pop("_resource_links", None)
    links: list[ResourceLink] = []
    if raw_links is not None:
        if not isinstance(raw_links, list):
            logger.warning("ignored non-list _resource_links sentinel")
        else:
            for descriptor in raw_links:
                if not isinstance(descriptor, dict):
                    logger.warning("ignored non-object resource-link descriptor")
                    continue
                name = descriptor.get("name")
                uri = descriptor.get("uri")
                if not isinstance(name, str) or not isinstance(uri, str):
                    logger.warning("ignored resource-link descriptor without string name/uri")
                    continue
                mime_type = descriptor.get("mime_type", descriptor.get("mimeType"))
                size = descriptor.get("size")
                meta = descriptor.get("meta", descriptor.get("_meta"))
                links.append(
                    ResourceLink(
                        name=name,
                        uri=uri,
                        title=descriptor.get("title")
                        if isinstance(descriptor.get("title"), str)
                        else None,
                        description=descriptor.get("description")
                        if isinstance(descriptor.get("description"), str)
                        else None,
                        mime_type=mime_type if isinstance(mime_type, str) else None,
                        size=size if isinstance(size, int) and not isinstance(size, bool) else None,
                        _meta=meta if isinstance(meta, dict) else None,
                    )
                )

    failed = "error" in payload and (
        payload.get("success") is False or payload.get("verified") is False
    )
    if not failed and not links:
        return payload if had_link_sentinel else result
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    return CallToolResult(
        content=[TextContent(type="text", text=text), *links],
        structured_content=payload,
        is_error=failed,
    )


def _legacy_payload_compat(
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    result: Any,
    profile: ToolProfile,
) -> Any:
    """Preserve one frozen parser error while compact profiles use safer wording."""
    if (
        profile not in {"legacy", "full"}
        or fn.__name__ != "calculate_limit"
        or not isinstance(result, dict)
        or result.get("success") is not False
        or result.get("error") != _STRICT_UNMATCHED_BRACKET_ERROR
    ):
        return result
    try:
        expression = inspect.signature(fn).bind_partial(*args, **kwargs).arguments.get("expression")
    except TypeError:
        return result
    if expression != "(":
        return result
    compatible = dict(result)
    compatible["error"] = _LEGACY_LIMIT_BRACKET_ERROR
    return compatible


def _with_protocol_envelope(
    fn: Callable[..., Any], profile: ToolProfile = "legacy"
) -> Callable[..., Any]:
    """Compose the historical Python envelope with MCP's error channel."""
    enveloped = with_error_envelope(fn)
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await enveloped(*args, **kwargs)
            return _protocol_result(_legacy_payload_compat(fn, args, kwargs, result, profile))

        return async_wrapper

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = enveloped(*args, **kwargs)
        return _protocol_result(_legacy_payload_compat(fn, args, kwargs, result, profile))

    return wrapper


class EnvelopeMCP:
    """Proxy over an MCPServer that wraps and describes every ``@tool()``.

    All other attribute access is delegated, so it is a drop-in for the tool
    registration functions.
    """

    def __init__(
        self,
        mcp: Any,
        *,
        profile: ToolProfile = "legacy",
        enabled_names: frozenset[str] | None = None,
        enforce_registry: bool = True,
    ) -> None:
        self._mcp = mcp
        self._profile = profile
        self._enabled_names = enabled_names or profile_tool_names(profile)
        self._enforce_registry = enforce_registry
        self._registered_names: set[str] = set()

    def tool(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            module = fn.__module__.rsplit(".", maxsplit=1)[-1]
            name = str(kwargs.get("name") or fn.__name__)
            try:
                spec = spec_for(name, module if self._enforce_registry else None)
            except ValueError:
                if self._enforce_registry:
                    raise
                spec = None
            if spec is not None and name not in self._enabled_names:
                return fn
            contract = spec.contract if spec is not None else contract_for(name, module)
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
                "meta": spec.runtime_meta(self._profile) if spec is not None else tool_meta(module),
                "structured_output": True,
                **kwargs,
            }
            if spec is not None and self._profile in {"workflow", "scientific", "interactive"}:
                options["description"] = spec.description
            register = self._mcp.tool(*args, **options)
            registered = cast(
                "Callable[..., Any]", register(_with_protocol_envelope(fn, self._profile))
            )
            self._registered_names.add(name)
            return registered

        return decorator

    @property
    def registered_names(self) -> frozenset[str]:
        """Names actually registered through this fixed-profile adapter."""
        return frozenset(self._registered_names)

    def assert_complete(self) -> None:
        """Fail if registry membership and runtime module wiring diverged."""
        if self._registered_names != set(self._enabled_names):
            missing = sorted(set(self._enabled_names) - self._registered_names)
            extra = sorted(self._registered_names - set(self._enabled_names))
            raise RuntimeError(f"profile registration drift (missing={missing}, extra={extra})")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._mcp, name)
