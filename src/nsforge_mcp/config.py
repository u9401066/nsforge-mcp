"""Runtime configuration for the NSForge MCP server.

Some tool modules are mission-tangential (a demo of the symbolic core rather than
part of the derivation forge). They are **opt-in**, so the default surface an MCP
client loads stays lean and focused — fewer tools means better tool selection by
the model. Enable one by setting ``NSFORGE_ENABLE_<MODULE>=1``, e.g.
``NSFORGE_ENABLE_MUSIC=1``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from nsforge_mcp.tool_contract import TOOL_PROFILES, ToolProfile

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
TenantScopeMode = Literal["local", "configured"]

_TENANT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


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


@dataclass(frozen=True, slots=True)
class SurfaceConfig:
    """Validated, immutable process scope captured when a server is built."""

    profile: ToolProfile
    legacy_music: bool
    tenant_id: str
    tenant_scope_mode: TenantScopeMode
    artifact_root: Path
    run_store_path: Path | Literal[":memory:"]


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


def tool_profile() -> ToolProfile:
    """Return the fixed startup tool profile; unknown values fail closed."""
    raw = os.environ.get("NSFORGE_TOOL_PROFILE")
    value = "legacy" if raw is None else raw.strip().lower()
    if value not in TOOL_PROFILES:
        allowed = ", ".join(TOOL_PROFILES)
        raise ValueError(f"NSFORGE_TOOL_PROFILE must be one of: {allowed}")
    return cast("ToolProfile", value)


def tenant_id() -> str:
    """Return an opaque tenant slug that can never be interpreted as a path."""
    raw = os.environ.get("NSFORGE_TENANT_ID", "local")
    value = raw.strip()
    if raw != value or value in {"", ".", ".."} or _TENANT_ID_RE.fullmatch(value) is None:
        raise ValueError(
            "NSFORGE_TENANT_ID must be a 1-128 character opaque slug using only "
            "letters, digits, '.', '_' or '-' and no path separators"
        )
    return value


def artifact_root() -> Path:
    """Resolve the process artifact root once without creating or writing it."""
    raw = os.environ.get("NSFORGE_ARTIFACT_ROOT")
    candidate = Path(raw) if raw is not None and raw.strip() else Path.cwd() / "artifacts"
    resolved = candidate.resolve(strict=False)
    if resolved.exists() and not resolved.is_dir():
        raise ValueError("NSFORGE_ARTIFACT_ROOT must resolve to a directory")
    return resolved


def run_store_path() -> Path | Literal[":memory:"]:
    """Resolve the process run database once, preserving SQLite's memory sentinel."""
    raw = os.environ.get("NSFORGE_RUN_DB", "data/nsforge-strict.sqlite3")
    value = raw.strip() or "data/nsforge-strict.sqlite3"
    if value == ":memory:":
        return ":memory:"
    resolved = Path(value).resolve(strict=False)
    if resolved.exists() and resolved.is_dir():
        raise ValueError("NSFORGE_RUN_DB must resolve to a database file, not a directory")
    return resolved


def surface_config() -> SurfaceConfig:
    """Capture profile, tenant scope, and artifact boundary for one server instance."""
    profile = tool_profile()
    resolved_tenant = tenant_id()
    scope_mode: TenantScopeMode = "local" if resolved_tenant == "local" else "configured"
    return SurfaceConfig(
        profile=profile,
        legacy_music=profile == "legacy" and module_enabled("music"),
        tenant_id=resolved_tenant,
        tenant_scope_mode=scope_mode,
        artifact_root=artifact_root(),
        run_store_path=run_store_path(),
    )


def module_enabled(module: str) -> bool:
    """Return whether a tool module should be registered in this process.

    Core modules are always enabled; optional ones require ``NSFORGE_ENABLE_<M>``.
    """
    if module not in OPTIONAL_MODULES:
        return True
    return os.environ.get(f"NSFORGE_ENABLE_{module.upper()}", "").strip().lower() in _TRUTHY
