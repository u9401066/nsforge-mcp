"""Hard wall-clock timeout for runaway symbolic computation.

``safe_parse`` rejects the worst pathological *inputs*, but a perfectly
well-formed input can still send SymPy into an intractable ``simplify`` / ``solve``.
CPython threads cannot be force-killed, so the only robust cap is a separate
process we are free to terminate. This runs a callable in a fresh *spawned*
process and kills it if it overruns its budget.

Constraints (``spawn`` semantics): ``func``, its arguments, and its return value
must be picklable — pass a module-level function and plain data (e.g. the task
spec dict), never a closure or a live SymPy object. Results are shipped back over
a pipe, so keep them modest in size.
"""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable
from multiprocessing.connection import Connection
from typing import Any, cast


class ComputationTimeout(Exception):
    """Raised when a computation exceeds its wall-clock budget and is killed."""


class WorkerError(RuntimeError):
    """Raised when the worker process fails before producing a result."""


def _entrypoint(
    conn: Connection,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    """Child-process body: run ``func`` and ship the outcome back over ``conn``."""
    try:
        conn.send(("ok", func(*args, **kwargs)))
    except Exception as exc:  # relay any failure to the parent as a message
        conn.send(("err", f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


def run_with_timeout[T](
    func: Callable[..., T],
    *args: Any,
    timeout: float,
    **kwargs: Any,
) -> T:
    """Run ``func(*args, **kwargs)`` in a spawned process, killing it on overrun.

    Args:
        func: A picklable, module-level callable (not a closure/lambda).
        *args: Positional arguments (must be picklable).
        timeout: Wall-clock budget in seconds; must be positive.
        **kwargs: Keyword arguments (must be picklable).

    Returns:
        Whatever ``func`` returns (must be picklable).

    Raises:
        ValueError: ``timeout`` is not positive.
        ComputationTimeout: the call ran longer than ``timeout`` and was killed.
        WorkerError: the child crashed or raised before returning a result.
    """
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    ctx = mp.get_context("spawn")
    recv_conn, send_conn = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_entrypoint, args=(send_conn, func, args, kwargs))
    proc.start()
    send_conn.close()  # only the child writes; the parent keeps the read end

    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        recv_conn.close()
        raise ComputationTimeout(f"computation exceeded {timeout:.3f}s and was terminated")

    try:
        if not recv_conn.poll():
            raise WorkerError(f"worker exited (code {proc.exitcode}) without a result")
        status, payload = recv_conn.recv()
    finally:
        recv_conn.close()

    if status == "err":
        raise WorkerError(str(payload))
    return cast("T", payload)
