"""Runtime configuration for the NSForge MCP server.

Some tool modules are mission-tangential (a demo of the symbolic core rather than
part of the derivation forge). They are **opt-in**, so the default surface an MCP
client loads stays lean and focused — fewer tools means better tool selection by
the model. Enable one by setting ``NSFORGE_ENABLE_<MODULE>=1``, e.g.
``NSFORGE_ENABLE_MUSIC=1``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

# Tool modules registered only when explicitly enabled (kept out of the default
# production surface). Kept as a plain tuple so tooling can read it statically.
OPTIONAL_MODULES: tuple[str, ...] = ("music",)

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_LOOPBACK_ALLOWED_HOSTS = ("127.0.0.1:*", "localhost:*", "[::1]:*")
_LOOPBACK_ALLOWED_ORIGINS = (
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
)

Transport = Literal["stdio", "streamable-http"]


@dataclass(frozen=True, slots=True)
class TransportConfig:
    """Validated MCP transport configuration sourced from the environment."""

    transport: Transport = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    json_response: bool = False
    stateless_http: bool = False
    allowed_hosts: tuple[str, ...] = _LOOPBACK_ALLOWED_HOSTS
    allowed_origins: tuple[str, ...] = _LOOPBACK_ALLOWED_ORIGINS


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def _csv_env(name: str) -> tuple[str, ...]:
    """Parse a comma-separated allowlist without accepting empty entries."""
    return tuple(part.strip() for part in os.environ.get(name, "").split(",") if part.strip())


def transport_config() -> TransportConfig:
    """Parse the stdio-default, explicitly opt-in Streamable HTTP settings.

    Remote binds require a separate acknowledgement because NSForge does not
    fabricate an OAuth provider.  Deployments that expose HTTP should put a
    real authentication boundary in front of the server.
    """
    raw_transport = os.environ.get("NSFORGE_MCP_TRANSPORT", "stdio").strip().lower()
    if raw_transport not in {"stdio", "streamable-http"}:
        raise ValueError("NSFORGE_MCP_TRANSPORT must be 'stdio' or 'streamable-http'")
    transport: Transport = raw_transport  # type: ignore[assignment]
    if transport == "stdio":
        # HTTP-only settings must never make the default stdio server fail.
        return TransportConfig()

    host = os.environ.get("NSFORGE_MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        port = int(os.environ.get("NSFORGE_MCP_PORT", "8000"))
    except ValueError as exc:
        raise ValueError("NSFORGE_MCP_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("NSFORGE_MCP_PORT must be between 1 and 65535")

    path = os.environ.get("NSFORGE_MCP_PATH", "/mcp").strip() or "/mcp"
    if not path.startswith("/"):
        raise ValueError("NSFORGE_MCP_PATH must start with '/'")

    allowed_hosts: tuple[str, ...] = _LOOPBACK_ALLOWED_HOSTS
    allowed_origins: tuple[str, ...] = _LOOPBACK_ALLOWED_ORIGINS
    if host not in _LOOPBACK_HOSTS:
        if not _truthy_env("NSFORGE_MCP_ALLOW_REMOTE"):
            raise ValueError(
                "non-loopback MCP HTTP requires NSFORGE_MCP_ALLOW_REMOTE=1, an explicit "
                "Host allowlist, and an external authentication boundary"
            )
        allowed_hosts = _csv_env("NSFORGE_MCP_ALLOWED_HOSTS")
        if not allowed_hosts:
            raise ValueError(
                "non-loopback MCP HTTP requires NSFORGE_MCP_ALLOWED_HOSTS "
                "(for example, mcp.example.com or mcp.example.com:*)"
            )
        # An empty Origin allowlist is intentionally safe for non-browser MCP
        # clients: requests without Origin are accepted, any supplied Origin is
        # denied. Browser clients must opt their exact HTTPS origins in.
        allowed_origins = _csv_env("NSFORGE_MCP_ALLOWED_ORIGINS")

    return TransportConfig(
        transport=transport,
        host=host,
        port=port,
        path=path,
        json_response=_truthy_env("NSFORGE_MCP_HTTP_JSON_RESPONSE"),
        stateless_http=_truthy_env("NSFORGE_MCP_STATELESS_HTTP"),
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def module_enabled(module: str) -> bool:
    """Return whether a tool module should be registered in this process.

    Core modules are always enabled; optional ones require ``NSFORGE_ENABLE_<M>``.
    """
    if module not in OPTIONAL_MODULES:
        return True
    return os.environ.get(f"NSFORGE_ENABLE_{module.upper()}", "").strip().lower() in _TRUTHY
