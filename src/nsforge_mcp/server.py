"""NSForge MCP 2.x server and transport entry point."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from mcp.server import CacheHint, MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Icon

from nsforge import __version__
from nsforge_mcp.composition import Services, get_services
from nsforge_mcp.config import OPTIONAL_MODULES, TransportConfig, module_enabled, transport_config
from nsforge_mcp.introspection import health_payload
from nsforge_mcp.primitives import register_primitives
from nsforge_mcp.tool_contract import NSFORGE_ICON_URL
from nsforge_mcp.tools import register_all_tools

logger = logging.getLogger("nsforge")


@asynccontextmanager
async def _lifespan(_: MCPServer[Services]) -> AsyncIterator[Services]:
    """Warm and expose the process-wide composition root to MCP contexts."""
    yield get_services()


def create_server() -> MCPServer[Services]:
    """Build a fully registered server from the current module environment."""
    module_state = {module: module_enabled(module) for module in OPTIONAL_MODULES}
    instance_health = partial(health_payload, module_state=module_state)
    server = MCPServer[Services](
        name="nsforge",
        title="Neurosymbolic Forge",
        description=(
            "Turn concepts into verifiable, provenance-tracked symbols, derivations, "
            "algorithms, and generated code."
        ),
        version=__version__,
        instructions=(
            f"Neurosymbolic Forge v{__version__}. Use deterministic tools for every "
            "symbol, equation, value, verification, and generated line of code; each "
            "result must retain a complete tool-provenance birth certificate. Read "
            "nsforge://manifest or call nsforge_manifest for live capabilities."
        ),
        website_url="https://github.com/u9401066/nsforge-mcp",
        icons=[Icon(src=NSFORGE_ICON_URL, mime_type="image/svg+xml")],
        lifespan=_lifespan,
        cache_hints={
            "tools/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/templates/list": CacheHint(ttl_ms=300_000, scope="public"),
            "prompts/list": CacheHint(ttl_ms=300_000, scope="public"),
            "server/discover": CacheHint(ttl_ms=300_000, scope="public"),
        },
    )
    register_all_tools(server, module_state=module_state, health_factory=instance_health)
    register_primitives(server, health_factory=instance_health)
    return server


# Import-time instance retained for existing Python integrations and the CLI.
mcp = create_server()


def _configure_logging() -> None:
    """Send logs to stderr; stdout is reserved for the stdio protocol."""
    logger.setLevel(os.environ.get("NSFORGE_LOG_LEVEL", "INFO").upper())
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False


def _transport_security(config: TransportConfig) -> TransportSecuritySettings:
    """Build mandatory Host/Origin validation for every HTTP bind."""
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(config.allowed_hosts),
        allowed_origins=list(config.allowed_origins),
    )


def main() -> None:
    """Run stdio by default or explicitly opted-in Streamable HTTP."""
    _configure_logging()
    config = transport_config()
    logger.info(
        "NSForge MCP v%s starting (%s) — music %s",
        __version__,
        config.transport,
        "enabled" if module_enabled("music") else "opt-in (disabled)",
    )
    if config.transport == "stdio":
        mcp.run("stdio")
        return
    logger.info("Streamable HTTP listening on %s:%s%s", config.host, config.port, config.path)
    mcp.run(
        "streamable-http",
        host=config.host,
        port=config.port,
        streamable_http_path=config.path,
        json_response=config.json_response,
        stateless_http=config.stateless_http,
        transport_security=_transport_security(config),
    )


if __name__ == "__main__":
    main()
