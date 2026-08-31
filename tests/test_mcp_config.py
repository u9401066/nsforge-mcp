"""Transport safety and opt-in behavior for MCP 2 Streamable HTTP."""

from __future__ import annotations

import pytest

from nsforge_mcp.config import transport_config


def test_transport_defaults_to_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NSFORGE_MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("NSFORGE_MCP_PORT", "not-an-http-port")
    config = transport_config()
    assert config.transport == "stdio"
    assert config.host == "127.0.0.1"
    assert config.path == "/mcp"


def test_streamable_http_loopback_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NSFORGE_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("NSFORGE_MCP_PORT", "8765")
    config = transport_config()
    assert config.transport == "streamable-http"
    assert config.port == 8765


def test_remote_http_requires_explicit_acknowledgement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NSFORGE_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("NSFORGE_MCP_HOST", "0.0.0.0")
    monkeypatch.delenv("NSFORGE_MCP_ALLOW_REMOTE", raising=False)
    with pytest.raises(ValueError, match="authentication boundary"):
        transport_config()

    monkeypatch.setenv("NSFORGE_MCP_ALLOW_REMOTE", "1")
    with pytest.raises(ValueError, match="NSFORGE_MCP_ALLOWED_HOSTS"):
        transport_config()

    monkeypatch.setenv("NSFORGE_MCP_ALLOWED_HOSTS", "mcp.example.com,mcp.example.com:*")
    monkeypatch.setenv("NSFORGE_MCP_ALLOWED_ORIGINS", "https://app.example.com")
    config = transport_config()
    assert config.host == "0.0.0.0"
    assert config.allowed_hosts == ("mcp.example.com", "mcp.example.com:*")
    assert config.allowed_origins == ("https://app.example.com",)


@pytest.mark.parametrize("value", ["sse", "http", "bogus"])
def test_deprecated_or_unknown_transport_is_rejected(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("NSFORGE_MCP_TRANSPORT", value)
    with pytest.raises(ValueError, match="stdio.*streamable-http"):
        transport_config()
