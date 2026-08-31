"""Session persistence hardening (multi-agent): atomic writes + thread-safe manager.

Under concurrent callers the session store must not (a) leave half-written JSON on
disk, nor (b) corrupt the in-memory session dict. These verify the atomic
temp+replace write and the RLock-guarded manager.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from nsforge.domain.derivation_session import DerivationSession, SessionManager, SessionStatus


def test_atomic_save_writes_complete_json(tmp_path: Path) -> None:
    manager = SessionManager(sessions_dir=tmp_path)
    session = manager.create(name="t", description="d")

    files = list(tmp_path.glob("session_*.json"))
    assert files, "session file should be persisted"
    data = json.loads(files[0].read_text(encoding="utf-8"))  # complete, parseable JSON
    assert data["session_id"] == session.session_id
    assert data["status"] == session.status.value
    assert not list(tmp_path.glob(".*.tmp")), "no leftover temp files after atomic replace"


def test_temp_allocation_failure_does_not_change_session_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DerivationSession(session_id="no-temp", name="Allocation failure")

    def fail_mkstemp(**kwargs: object) -> tuple[int, str]:
        raise OSError(f"cannot allocate temp file: {kwargs}")

    monkeypatch.setattr("nsforge.domain.derivation_session.tempfile.mkstemp", fail_mkstemp)
    with pytest.raises(OSError, match="cannot allocate"):
        session.save(tmp_path / "session_no-temp.json")

    assert session.status is SessionStatus.ACTIVE


def test_concurrent_creates_are_thread_safe(tmp_path: Path) -> None:
    manager = SessionManager(sessions_dir=tmp_path)
    errors: list[Exception] = []

    def worker(i: int) -> None:
        try:
            manager.create(name=f"s{i}", description="")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    assert len(manager.list_sessions()) == 20  # no lost updates to the shared dict
