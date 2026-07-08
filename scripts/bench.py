#!/usr/bin/env python3
"""NSForge derivation benchmark gate — measures derivation *correctness*.

Runs each benchmark spec in ``benchmarks/*.json`` through the L3 orchestrator and
checks the derived expression against the benchmark's ``expected`` form using
symbolic equality. This upgrades the harness from "code is green" to
"derivations are correct" (roadmap phase 2 — see
docs/general-formula-exploration-roadmap.md).

    python scripts/bench.py            # run all benchmarks
    python scripts/bench.py --json     # machine-readable summary

Exit code 0 iff every benchmark derives its expected result.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.safe_parse import SYMPY_RESERVED_NAMES
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.domain.value_objects import MathContext
from nsforge.infrastructure.sympy_engine import SymPyEngine

REPO = Path(__file__).resolve().parent.parent
BENCH_DIR = REPO / "benchmarks"

# SymPy functions / constants that must NOT be declared as plain symbols.
_FUNCTION_NAMES = SYMPY_RESERVED_NAMES


def _symbol_assumptions(spec: DerivationTaskSpec) -> dict[str, dict[str, bool]]:
    """Declare every identifier so digit-suffixed names (C0, V1) survive parsing."""
    names = set(spec.given) | set(spec.unknowns)
    texts = [*spec.base_formulas, *(m.expression for m in spec.modifications)]
    for text in texts:
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
            if token not in _FUNCTION_NAMES:
                names.add(token)
    return {name: {} for name in names}


def run_benchmark(path: Path, engine: SymPyEngine) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = str(data.get("expected", ""))
    spec = DerivationTaskSpec.from_dict(data)
    result = TaskOrchestrator(spec, engine=engine).run()
    derived = result.derived_expression

    if not result.ok:
        return {"name": spec.name, "ok": False, "detail": "orchestrator did not complete"}
    if not derived:
        return {"name": spec.name, "ok": False, "detail": "derivation was PLANNED (no result)"}
    if not expected:
        return {"name": spec.name, "ok": False, "detail": "benchmark has no 'expected' field"}

    ctx = MathContext(assumptions=_symbol_assumptions(spec))
    rhs = derived.split("=", 1)[1] if "=" in derived else derived
    ok = engine.equals(engine.parse(rhs, ctx), engine.parse(expected, ctx))
    return {"name": spec.name, "ok": ok, "detail": f"derived: {derived}  |  expected: {expected}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="NSForge derivation benchmark gate")
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    args = parser.parse_args()

    files = sorted(BENCH_DIR.glob("*.json"))
    if not files:
        print(f"no benchmarks found in {BENCH_DIR.relative_to(REPO)}", file=sys.stderr)
        return 1

    engine = SymPyEngine()
    results = [run_benchmark(path, engine) for path in files]
    passed = sum(1 for r in results if r["ok"])
    summary: dict[str, object] = {
        "ok": passed == len(results),
        "passed": passed,
        "total": len(results),
        "benchmarks": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        for result in results:
            mark = "PASS" if result["ok"] else "FAIL"
            print(f"[{mark}] {result['name']}: {result['detail']}")
        print(f"\n{passed}/{len(results)} derivations correct.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
