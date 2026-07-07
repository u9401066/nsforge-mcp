#!/usr/bin/env python3
"""NSForge genericity gate — proves we are a derivation *calculus*, not a library.

The risk with a formula repo is degenerating into a hand-built lookup table: a
finite catalog of formulas we authored, which cannot generalise. This gate
refutes that structurally.

It procedurally generates random compositions that were **never hand-written** —
a target formula ``y = f(x0, x1, ...)`` plus an independent definition for each
``xi`` — feeds them through the L3 orchestrator, and checks the derived result
against a reference computed by an *independent* code path (SymPy ``.subs()`` on
in-memory objects, bypassing NSForge's parse/substitute/compose entirely).

    python scripts/genericity.py            # run the property test
    python scripts/genericity.py --json     # machine-readable summary
    python scripts/genericity.py --cases 100 --seed 7

If arbitrary unseen compositions derive correctly, NSForge processes formula
*content* generically — the formulas are inputs, the operators are ours. A fixed
seed keeps the gate deterministic. Exit code 0 iff every case is correct.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import sympy as sp

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.domain.value_objects import MathContext
from nsforge.infrastructure.sympy_engine import SymPyEngine

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CASES = 40
DEFAULT_SEED = 20260707


def _rand_combo(symbols: list[sp.Symbol], rng: random.Random) -> sp.Expr:
    """A random non-degenerate combination (sum of products, positive coeffs).

    Distinct symbols and positive integer coefficients guarantee the result never
    cancels to zero, so a passing case cannot be the ``0 == 0`` false-pass that
    bit phase 1.
    """
    terms: list[sp.Expr] = []
    for _ in range(rng.randint(2, 3)):
        picks = rng.sample(symbols, rng.randint(1, min(2, len(symbols))))
        term: sp.Expr = sp.Integer(rng.randint(1, 5))
        for sym in picks:
            term = term * sym
        terms.append(term)
    return sp.Add(*terms)


def _make_case(rng: random.Random, idx: int) -> tuple[dict[str, Any], sp.Expr]:
    """Build one random DTS plus its independently-computed reference result.

    Intermediate symbols are digit-suffixed (``x0``, ``z01``) so the case also
    regression-tests the parser fix that keeps ``C0`` from splitting into ``C*0``.
    Each ``xi`` is defined over its own fresh ``z`` symbols, so the definitions
    are independent and a single substitution pass fully resolves the target.
    """
    xs = [sp.Symbol(f"x{i}") for i in range(rng.randint(2, 3))]
    target_rhs = _rand_combo(xs, rng)

    subs_map: dict[sp.Symbol, sp.Expr] = {}
    def_formulas: list[str] = []
    for i, x in enumerate(xs):
        zs = [sp.Symbol(f"z{i}{j}") for j in range(rng.randint(1, 2))]
        definition = _rand_combo(zs, rng)
        subs_map[x] = definition
        def_formulas.append(f"{x} = {definition}")

    spec_data: dict[str, Any] = {
        "name": f"generic_case_{idx}",
        "goal": "compose arbitrary, never-before-seen formulas",
        "unknowns": ["y"],
        "base_formulas": [f"y = {target_rhs}", *def_formulas],
    }
    # Reference: an independent SymPy substitution on in-memory objects — a
    # different code path from the orchestrator (no string parsing / composition).
    reference = target_rhs.subs(subs_map)
    return spec_data, reference


def run_case(rng: random.Random, idx: int, engine: SymPyEngine) -> dict[str, object]:
    spec_data, reference = _make_case(rng, idx)
    spec = DerivationTaskSpec.from_dict(spec_data)
    result = TaskOrchestrator(spec, engine=engine).run()
    derived = result.derived_expression

    if not derived:
        return {"name": spec.name, "ok": False, "detail": "derivation did not execute"}

    names = {str(s) for s in reference.free_symbols} | set(spec.symbols)
    ctx = MathContext(assumptions={name: {} for name in names})
    rhs = derived.split("=", 1)[1] if "=" in derived else derived
    ok = engine.equals(engine.parse(rhs, ctx), engine.parse(str(reference), ctx))
    return {
        "name": spec.name,
        "ok": ok,
        "detail": f"derived: {derived.strip()}  |  reference: y = {reference}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="NSForge genericity gate")
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    parser.add_argument("--cases", type=int, default=DEFAULT_CASES, help="number of random cases")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed (deterministic)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    engine = SymPyEngine()
    results = [run_case(rng, i, engine) for i in range(args.cases)]
    passed = sum(1 for r in results if r["ok"])
    summary: dict[str, object] = {
        "ok": passed == len(results),
        "passed": passed,
        "total": len(results),
        "seed": args.seed,
        "cases": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        for result in results:
            if not result["ok"]:
                print(f"[FAIL] {result['name']}: {result['detail']}")
        print(
            f"{passed}/{len(results)} arbitrary unseen compositions derived correctly "
            f"(seed={args.seed})."
        )
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
