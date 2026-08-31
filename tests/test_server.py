"""Smoke test for server wiring + stderr logging configuration."""

import logging
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.testclient import TestClient

from nsforge_mcp import server
from nsforge_mcp.config import TransportConfig


def test_server_instance_is_configured() -> None:
    assert isinstance(server.mcp, MCPServer)
    assert isinstance(server.create_server(), MCPServer)


def test_logging_is_stderr_and_idempotent() -> None:
    server._configure_logging()
    server._configure_logging()  # calling twice must not duplicate handlers
    handlers = server.logger.handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)


def test_streamable_http_app_can_be_constructed() -> None:
    app = server.create_server().streamable_http_app(host="127.0.0.1")
    assert isinstance(app, Starlette)


def test_remote_http_rejects_unlisted_host_before_protocol_dispatch() -> None:
    config = TransportConfig(
        transport="streamable-http",
        host="0.0.0.0",
        allowed_hosts=("mcp.example.com",),
        allowed_origins=("https://app.example.com",),
    )
    app = server.create_server().streamable_http_app(
        host=config.host,
        transport_security=server._transport_security(config),
    )
    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            headers={"host": "evil.example", "content-type": "application/json"},
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
    assert response.status_code == 421


def test_main_dispatches_explicit_streamable_http(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeServer:
        def run(self, transport: str, **kwargs: Any) -> None:
            calls.append((transport, kwargs))

    monkeypatch.setattr(server, "mcp", FakeServer())
    monkeypatch.setattr(server, "_configure_logging", lambda: None)
    monkeypatch.setenv("NSFORGE_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("NSFORGE_MCP_PORT", "8765")
    server.main()

    assert len(calls) == 1
    transport, kwargs = calls[0]
    security = kwargs.pop("transport_security")
    assert transport == "streamable-http"
    assert kwargs == {
        "host": "127.0.0.1",
        "port": 8765,
        "streamable_http_path": "/mcp",
        "json_response": False,
        "stateless_http": False,
    }
    assert isinstance(security, TransportSecuritySettings)
    assert security.enable_dns_rebinding_protection is True
    assert "localhost:*" in security.allowed_hosts
