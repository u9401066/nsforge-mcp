"""Smoke test: music plotting uses the object-oriented Agg figure.

The plotting tools were switched off pyplot (global, non-thread-safe) to a
per-call ``Figure`` + ``FigureCanvasAgg``. This exercises that path end to end so
the refactor can't silently break rendering.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nsforge_mcp.tools.music import register_music_tools


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _tools() -> dict[str, Callable[..., Any]]:
    mcp = _FakeMCP()
    register_music_tools(mcp)
    return mcp.tools


def test_plot_waveform_renders_png_via_oo_figure() -> None:
    result = _tools()["music_plot_waveform"]("sin(2*pi*440*t)", duration=0.005)
    assert result["success"] is True
    assert result["format"] == "png"
    assert result.get("image_base64")


def test_plot_spectrum_renders_png_via_oo_figure() -> None:
    result = _tools()["music_plot_spectrum"]("sin(2*pi*440*t)")
    assert result["success"] is True
    assert result.get("image_base64")
