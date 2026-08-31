"""Regression tests for worker-thread access to stateful derivation services."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import sympy as sp
import yaml
from pytest import MonkeyPatch

import nsforge.infrastructure.derivation_repository as repository_module
import nsforge_mcp.tools.derivation as derivation_tools
from nsforge.domain.derivation_session import DerivationSession, OperationType
from nsforge.infrastructure.derivation_repository import DerivationRepository, DerivationResult


def test_legacy_current_session_compare_and_clear_does_not_drop_new_session() -> None:
    old = DerivationSession(session_id="old", name="Old")
    new = DerivationSession(session_id="new", name="New")
    derivation_tools._set_current_session(old)
    try:
        derivation_tools._set_current_session(new)
        derivation_tools._clear_current_session_if(old)
        assert derivation_tools._get_current_session() is new
    finally:
        derivation_tools._set_current_session(None)


def test_same_session_mutations_are_serialized_and_persist_complete_json(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session = DerivationSession(session_id="concurrent", name="Concurrent session")
    persist_path = tmp_path / "session_concurrent.json"
    session.save(persist_path)
    assert session.load_formula("x**10", formula_id="base")["success"]

    symbol = sp.Symbol("x")
    initial = sp.sympify("x**10")
    original_diff = sp.diff
    expected = original_diff(original_diff(initial, symbol), symbol)

    first_in_diff = threading.Event()
    second_in_diff = threading.Event()
    release_first = threading.Event()
    call_lock = threading.Lock()
    call_count = 0

    def controlled_diff(expr: sp.Basic, variable: sp.Symbol, order: int) -> sp.Basic:
        nonlocal call_count
        with call_lock:
            call_count += 1
            current_call = call_count
        if current_call == 1:
            first_in_diff.set()
            if not release_first.wait(timeout=2):
                raise TimeoutError("first differentiation was not released")
        else:
            second_in_diff.set()
        return original_diff(expr, variable, order)

    monkeypatch.setattr(sp, "diff", controlled_diff)
    errors: list[Exception] = []

    def differentiate() -> None:
        try:
            result = session.differentiate("x")
            if not result["success"]:
                raise AssertionError(result)
        except Exception as exc:
            errors.append(exc)

    first = threading.Thread(target=differentiate)
    second = threading.Thread(target=differentiate)
    first.start()
    try:
        assert first_in_diff.wait(timeout=1)
        second.start()
        # Without a session-wide lock the second call reaches SymPy while the
        # first still holds a stale state snapshot, losing one differentiation.
        second_in_diff.wait(timeout=0.2)
    finally:
        release_first.set()

    first.join(timeout=2)
    second.join(timeout=2)
    assert not first.is_alive()
    assert not second.is_alive()
    assert not errors

    snapshot = session.to_dict()
    assert session.current_expression == expected
    assert [step["step_number"] for step in snapshot["steps"]] == [1, 2, 3]

    persisted = json.loads(persist_path.read_text(encoding="utf-8"))
    assert persisted["current_expression"] == str(expected)
    assert persisted["steps"] == snapshot["steps"]
    assert not list(tmp_path.glob(".session_concurrent_*.tmp"))


def test_completion_returns_a_detached_point_in_time_snapshot() -> None:
    session = DerivationSession(session_id="complete", name="Completion snapshot")
    assert session.load_formula("x**3", formula_id="base")["success"]

    completed = session.complete()
    assert completed["success"] is True
    assert session.differentiate("x")["success"] is True  # retained legacy behavior

    assert completed["final_expression"] == "x**3"
    assert completed["total_steps"] == 1
    assert len(completed["steps"]) == 1
    assert session.to_dict()["current_expression"] == "3*x**2"


def test_external_record_write_failure_rolls_back_the_compound_mutation(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session = DerivationSession(session_id="rollback", name="Atomic record")
    path = session.save(tmp_path / "session_rollback.json")
    baseline_memory = session.to_dict()
    baseline_disk = path.read_text(encoding="utf-8")

    def fail_replace(source: str, destination: str | Path) -> None:
        raise OSError(f"cannot replace {destination} from {source}")

    monkeypatch.setattr("nsforge.domain.derivation_session.os.replace", fail_replace)
    try:
        session.record_external_step(
            operation=OperationType.CUSTOM,
            description="external result",
            input_expressions={"source": "test"},
            output_expr=sp.sympify("x + 1"),
            sympy_command="external()",
        )
    except OSError:
        pass
    else:  # pragma: no cover - the injected write failure must propagate
        raise AssertionError("expected atomic persistence failure")

    assert session.to_dict() == baseline_memory
    assert path.read_text(encoding="utf-8") == baseline_disk
    assert not list(tmp_path.glob(".session_rollback_*.tmp"))


def test_concurrent_repository_saves_are_atomic_and_leave_no_temp_files(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    repository = DerivationRepository(tmp_path)
    repository.register(
        DerivationResult(
            id="shared",
            name="Shared result",
            expression="x + 1",
            category="concurrent",
        )
    )
    result_path = repository.save("shared")
    baseline = result_path.read_text(encoding="utf-8")

    original_dump = repository_module.yaml.dump
    first_mid_write = threading.Event()
    second_in_dump = threading.Event()
    release_first = threading.Event()
    dump_lock = threading.Lock()
    dump_count = 0

    def controlled_dump(data: Any, stream: Any = None, **kwargs: Any) -> Any:
        nonlocal dump_count
        with dump_lock:
            dump_count += 1
            current_dump = dump_count
        if current_dump != 1:
            second_in_dump.set()
            return original_dump(data, stream, **kwargs)

        rendered = original_dump(data, None, **kwargs)
        if not isinstance(rendered, str) or stream is None:
            raise AssertionError("expected YAML text and a writable stream")
        midpoint = len(rendered) // 2
        stream.write(rendered[:midpoint])
        stream.flush()
        first_mid_write.set()
        if not release_first.wait(timeout=2):
            raise TimeoutError("first YAML save was not released")
        stream.write(rendered[midpoint:])
        return None

    monkeypatch.setattr(repository_module.yaml, "dump", controlled_dump)
    errors: list[Exception] = []

    def save() -> None:
        try:
            repository.save("shared")
        except Exception as exc:
            errors.append(exc)

    first = threading.Thread(target=save)
    second = threading.Thread(target=save)
    first.start()
    observed_during_save = ""
    try:
        assert first_mid_write.wait(timeout=1)
        observed_during_save = result_path.read_text(encoding="utf-8")
        second.start()
        assert not second_in_dump.wait(timeout=0.2)
    finally:
        release_first.set()

    first.join(timeout=2)
    second.join(timeout=2)
    assert not first.is_alive()
    assert not second.is_alive()
    assert not errors
    assert second_in_dump.is_set()

    # A reader continues to see the previous complete file until os.replace.
    assert observed_during_save == baseline
    persisted = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    assert persisted["id"] == "shared"
    assert not list(result_path.parent.glob(".shared_*.tmp"))


def test_repository_transaction_hides_partial_update_from_snapshot_reader(
    tmp_path: Path,
) -> None:
    repository = DerivationRepository(tmp_path)
    repository.register(DerivationResult(id="txn", name="Before", expression="x"))
    repository.save("txn")

    updated_inside_transaction = threading.Event()
    release_writer = threading.Event()
    reader_returned = threading.Event()
    observed: list[dict[str, Any] | None] = []

    def writer() -> None:
        with repository.transaction():
            repository.update("txn", name="After")
            updated_inside_transaction.set()
            if not release_writer.wait(timeout=2):
                raise TimeoutError("writer was not released")
            repository.save("txn")

    def reader() -> None:
        observed.append(repository.snapshot("txn"))
        reader_returned.set()

    write_thread = threading.Thread(target=writer)
    read_thread = threading.Thread(target=reader)
    write_thread.start()
    try:
        assert updated_inside_transaction.wait(timeout=1)
        read_thread.start()
        assert not reader_returned.wait(timeout=0.2)
    finally:
        release_writer.set()

    write_thread.join(timeout=2)
    read_thread.join(timeout=2)
    assert not write_thread.is_alive() and not read_thread.is_alive()
    assert observed[0] is not None and observed[0]["name"] == "After"
    persisted = yaml.safe_load((tmp_path / "txn.yaml").read_text(encoding="utf-8"))
    assert persisted["name"] == "After"
