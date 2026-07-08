#!/usr/bin/env python3
"""NSForge provenance gate — the north star enforced as architecture.

Runs every benchmark through the L3 orchestrator and asserts the derived result
carries a COMPLETE provenance ledger: every entry (base formula, substitution or
solve step, final expression) names the tool call that produced it. Code is only
emitted from a complete ledger, so a derivation that reached a result without a
full provenance chain — i.e. something hand-derived slipping in — fails here.

    python scripts/provenance.py            # run all benchmarks
    python scripts/provenance.py --json     # machine-readable summary

Exit code 0 iff every benchmark's derivation is fully provenanced.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine
from nsforge.infrastructure.verifier import BasicVerifier

REPO = Path(__file__).resolve().parent.parent
BENCH_DIR = REPO / "benchmarks"


def check_provenance(path: Path, engine: SymPyEngine, verifier: BasicVerifier) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    spec = DerivationTaskSpec.from_dict(data)
    result = TaskOrchestrator(spec, engine=engine, verifier=verifier).run()
    ledger = result.provenance
    ok = bool(result.derived_expression) and ledger.is_complete
    detail = f"{len(ledger.entries)} entries, complete={ledger.is_complete}"
    leaks = ledger.unsourced()
    if leaks:
        detail += f", UN-SOURCED: {[e.entity for e in leaks]}"
    return {"name": spec.name, "ok": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="NSForge provenance gate")
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    args = parser.parse_args()

    files = sorted(BENCH_DIR.glob("*.json"))
    if not files:
        print(f"no benchmarks found in {BENCH_DIR.relative_to(REPO)}", file=sys.stderr)
        return 1

    engine = SymPyEngine()
    verifier = BasicVerifier()
    results = [check_provenance(path, engine, verifier) for path in files]
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
        print(f"\n{passed}/{len(results)} derivations fully provenanced.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
