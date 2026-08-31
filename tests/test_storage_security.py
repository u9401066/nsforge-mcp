"""Security and transaction regressions for filesystem-backed legacy adapters."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from nsforge.infrastructure.derivation_repository import (
    DerivationRepository,
    DerivationResult,
)
from nsforge.infrastructure.storage_paths import (
    UnsafeStoragePath,
    contained_output_path,
)
from nsforge_mcp.tools.music import register_music_tools


class _FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.fixture
def music_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Callable[..., Any]]:
    monkeypatch.setenv("NSFORGE_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    mcp = _FakeMCP()
    register_music_tools(mcp)
    return mcp.tools


@pytest.mark.parametrize("category", ["../escape", "/tmp/escape", "a/b", ".."])
def test_repository_rejects_category_path_traversal(tmp_path: Path, category: str) -> None:
    repository = DerivationRepository(tmp_path)
    repository.register(
        DerivationResult(id="safe-id", name="Unsafe category", expression="x", category=category)
    )

    with pytest.raises(UnsafeStoragePath):
        repository.save("safe-id")


def test_repository_rejects_identifier_path_traversal(tmp_path: Path) -> None:
    repository = DerivationRepository(tmp_path)
    repository.register(DerivationResult(id="../outside", name="Unsafe id", expression="x"))

    with pytest.raises(UnsafeStoragePath):
        repository.save("../outside")

    with pytest.raises(UnsafeStoragePath):
        repository.delete("../outside")
    assert repository.get("../outside") is not None


def test_output_path_rejects_parent_and_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    with pytest.raises(UnsafeStoragePath):
        contained_output_path(root, "../outside/result.png", suffixes=frozenset({".png"}))

    (root / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(UnsafeStoragePath):
        contained_output_path(root, "linked/result.png", suffixes=frozenset({".png"}))


def test_music_output_rejects_parent_escape(
    music_tools: dict[str, Callable[..., Any]], tmp_path: Path
) -> None:
    result = music_tools["music_plot_waveform"](
        "sin(2*pi*t)", duration=0.005, output_path="../escape.png"
    )

    assert result["success"] is False
    assert "stay within" in result["error"]
    assert not (tmp_path / "escape.png").exists()


def test_music_output_rejects_absolute_escape(
    music_tools: dict[str, Callable[..., Any]], tmp_path: Path
) -> None:
    outside = tmp_path / "outside.png"
    result = music_tools["music_plot_spectrum"](
        "sin(2*pi*t)", duration=0.005, output_path=str(outside)
    )

    assert result["success"] is False
    assert "stay within" in result["error"]
    assert not outside.exists()


def test_music_output_rejects_symlink_escape(
    music_tools: dict[str, Callable[..., Any]], tmp_path: Path
) -> None:
    root = tmp_path / "artifacts"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    result = music_tools["music_generate_wav"](
        "sin(2*pi*t)", duration=0.005, output_path="linked/escape.wav"
    )

    assert result["success"] is False
    assert "stay within" in result["error"]
    assert not (outside / "escape.wav").exists()


@pytest.mark.parametrize(
    ("tool_name", "output_path"),
    [
        ("music_plot_waveform", "waveform.wav"),
        ("music_plot_spectrum", "spectrum.txt"),
        ("music_generate_wav", "tone.png"),
    ],
)
def test_music_output_rejects_wrong_suffix(
    music_tools: dict[str, Callable[..., Any]], tool_name: str, output_path: str
) -> None:
    result = music_tools[tool_name]("sin(2*pi*t)", duration=0.005, output_path=output_path)

    assert result["success"] is False
    assert "must use one of" in result["error"]


def test_music_export_root_is_frozen_when_tools_are_registered(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    monkeypatch.setenv("NSFORGE_ARTIFACT_ROOT", str(first_root))
    mcp = _FakeMCP()
    register_music_tools(mcp)

    monkeypatch.setenv("NSFORGE_ARTIFACT_ROOT", str(second_root))
    result = mcp.tools["music_generate_wav"](
        expression="sin(2*pi*440*t)",
        duration=0.01,
        sample_rate=8000,
        output_path="frozen.wav",
    )

    assert result["success"] is True
    assert Path(result["file_path"]) == (first_root / "frozen.wav").resolve()
    assert not second_root.exists()


def test_repository_update_rolls_back_memory_when_save_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = DerivationRepository(tmp_path)
    repository.register(DerivationResult(id="rollback", name="Before", expression="x"))
    repository.save("rollback")

    def fail_replace(_source: str, _destination: str | Path) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr("nsforge.infrastructure.derivation_repository.os.replace", fail_replace)
    with pytest.raises(OSError, match="disk unavailable"):
        repository.update_and_save("rollback", name="After")

    snapshot = repository.snapshot("rollback")
    assert snapshot is not None
    assert snapshot["name"] == "Before"


def test_legacy_verified_update_is_explicitly_untrusted(tmp_path: Path) -> None:
    repository = DerivationRepository(tmp_path)
    repository.register(DerivationResult(id="asserted", name="Asserted", expression="x"))

    repository.update_and_save(
        "asserted",
        verified=True,
        verification_method="caller says so",
    )

    snapshot = repository.snapshot("asserted")
    assert snapshot is not None
    assert snapshot["verified"] is True
    assert snapshot["verification_trust"] == "caller_asserted"
