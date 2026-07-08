"""Regression tests for optional-module gating (lean default surface)."""

import pytest

from nsforge_mcp.config import OPTIONAL_MODULES, module_enabled


def test_core_modules_are_always_enabled() -> None:
    assert module_enabled("derivation")
    assert module_enabled("verify")
    assert module_enabled("task")


def test_music_is_opt_in_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert "music" in OPTIONAL_MODULES
    monkeypatch.delenv("NSFORGE_ENABLE_MUSIC", raising=False)
    assert module_enabled("music") is False


def test_music_can_be_enabled_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for truthy in ("1", "true", "YES", "on"):
        monkeypatch.setenv("NSFORGE_ENABLE_MUSIC", truthy)
        assert module_enabled("music") is True
    monkeypatch.setenv("NSFORGE_ENABLE_MUSIC", "0")
    assert module_enabled("music") is False
