"""Security and transaction regressions for filesystem-backed legacy adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from nsforge.infrastructure.derivation_repository import (
    DerivationRepository,
    DerivationResult,
)
from nsforge.infrastructure.storage_paths import (
    UnsafeStoragePath,
    contained_output_path,
)


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
