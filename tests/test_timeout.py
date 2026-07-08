"""Regression tests for the process-pool hard-timeout utility."""

import time

import pytest

from nsforge.infrastructure.timeout import ComputationTimeout, WorkerError, run_with_timeout


def test_returns_result_within_budget() -> None:
    # A picklable module-level callable runs in the child and returns normally.
    assert run_with_timeout(pow, 2, 10, timeout=15) == 1024


def test_kills_overrunning_computation() -> None:
    start = time.perf_counter()
    with pytest.raises(ComputationTimeout):
        run_with_timeout(time.sleep, 30, timeout=0.5)
    # Killed promptly — not after the full 30s the callable asked to sleep.
    assert time.perf_counter() - start < 15


def test_relays_worker_failure() -> None:
    # int("not-a-number") raises in the child; the failure surfaces as WorkerError.
    with pytest.raises(WorkerError):
        run_with_timeout(int, "not-a-number", timeout=15)


def test_rejects_nonpositive_timeout() -> None:
    with pytest.raises(ValueError, match="positive"):
        run_with_timeout(pow, 2, 3, timeout=0)
