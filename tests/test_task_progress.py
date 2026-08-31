"""Protocol progress must describe completed work, including cancellation."""

from __future__ import annotations

import asyncio
import threading
from typing import Any, cast

import pytest
from mcp.server.mcpserver import Context

from nsforge_mcp.tools.task import _run_with_progress


class _RecordingContext:
    def __init__(self) -> None:
        self.events: list[tuple[float, float | None, str | None]] = []

    async def report_progress(
        self,
        progress: float,
        total: float | None = None,
        message: str | None = None,
    ) -> None:
        self.events.append((progress, total, message))


@pytest.mark.asyncio
async def test_cancellation_does_not_report_worker_as_finished() -> None:
    started = threading.Event()
    release = threading.Event()

    def blocking_operation(spec: dict[str, Any]) -> dict[str, Any]:
        started.set()
        if not release.wait(timeout=2):
            raise TimeoutError(spec)
        return {"success": True}

    recorder = _RecordingContext()
    ctx = cast("Context[Any, Any]", recorder)
    task = asyncio.create_task(
        _run_with_progress(ctx, blocking_operation, {"name": "cancel"}, None, "test task")
    )
    assert await asyncio.to_thread(started.wait, 1)
    task.cancel()
    try:
        with pytest.raises(asyncio.CancelledError):
            await task
        assert recorder.events == [(0.0, 1.0, "Starting test task")]
    finally:
        release.set()
