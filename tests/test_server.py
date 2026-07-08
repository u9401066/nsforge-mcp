"""Smoke test for server wiring + stderr logging configuration."""

import logging

from mcp.server.fastmcp import FastMCP

from nsforge_mcp import server


def test_server_instance_is_configured() -> None:
    assert isinstance(server.mcp, FastMCP)


def test_logging_is_stderr_and_idempotent() -> None:
    server._configure_logging()
    server._configure_logging()  # calling twice must not duplicate handlers
    handlers = server.logger.handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)
