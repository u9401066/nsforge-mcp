"""Regression tests for optional-module gating (lean default surface)."""

from pathlib import Path

import pytest

from nsforge_mcp.config import (
    OPTIONAL_MODULES,
    artifact_root,
    module_enabled,
    run_store_path,
    surface_config,
    tenant_id,
    tool_profile,
)
from nsforge_mcp.tool_contract import TOOL_PROFILES


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


def test_tool_profile_defaults_and_exact_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NSFORGE_TOOL_PROFILE", raising=False)
    assert tool_profile() == "legacy"
    for profile in TOOL_PROFILES:
        monkeypatch.setenv("NSFORGE_TOOL_PROFILE", profile.upper())
        assert tool_profile() == profile


def test_unknown_or_empty_tool_profile_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    for value in ("unknown", "", "legacy/full"):
        monkeypatch.setenv("NSFORGE_TOOL_PROFILE", value)
        with pytest.raises(ValueError, match="NSFORGE_TOOL_PROFILE"):
            tool_profile()


def test_tenant_id_is_opaque_and_never_a_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NSFORGE_TENANT_ID", raising=False)
    assert tenant_id() == "local"
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant_01.eu")
    assert tenant_id() == "tenant_01.eu"
    for invalid in ("", ".", "..", "a/b", "a\\b", " space"):
        monkeypatch.setenv("NSFORGE_TENANT_ID", invalid)
        with pytest.raises(ValueError, match="opaque slug"):
            tenant_id()


def test_artifact_root_is_resolved_and_surface_is_frozen(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "relative-root"
    monkeypatch.setenv("NSFORGE_ARTIFACT_ROOT", str(root))
    monkeypatch.setenv("NSFORGE_TENANT_ID", "tenant-a")
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "workflow")
    monkeypatch.setenv("NSFORGE_RUN_DB", "relative-runs.sqlite3")
    captured = surface_config()
    assert captured.artifact_root == root.resolve()
    assert artifact_root() == root.resolve()
    assert captured.tenant_scope_mode == "configured"
    assert captured.run_store_path == (Path.cwd() / "relative-runs.sqlite3").resolve()
    monkeypatch.setenv("NSFORGE_TOOL_PROFILE", "full")
    monkeypatch.setenv("NSFORGE_RUN_DB", ":memory:")
    assert captured.profile == "workflow"
    assert captured.run_store_path != run_store_path()


def test_run_store_path_resolves_files_and_preserves_memory_sentinel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NSFORGE_RUN_DB", raising=False)
    assert run_store_path() == (tmp_path / "data/nsforge-strict.sqlite3").resolve()
    monkeypatch.setenv("NSFORGE_RUN_DB", ":memory:")
    assert run_store_path() == ":memory:"
    monkeypatch.setenv("NSFORGE_RUN_DB", str(tmp_path))
    with pytest.raises(ValueError, match="database file"):
        run_store_path()
