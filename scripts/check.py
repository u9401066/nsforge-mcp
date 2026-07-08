#!/usr/bin/env python3
"""NSForge verification harness — the single ground-truth entrypoint.

Humans, CI, and autonomous agents (OpenHands / Hermes / Cline / Copilot) all run
ONE command to get an objective pass/fail signal before and after changes:

    python scripts/check.py                 # run all gates
    python scripts/check.py --gates lint,type
    python scripts/check.py --json          # machine-readable summary for agents

Exit code 0 = all selected gates passed. Nonzero = at least one failed.

This replaces the inherited asset-aware-mcp `full-check` workflow, whose Steps
1.1-4 reference paths that do not exist in NSForge (scripts/audit_*.py,
vscode-extension/, src/presentation/server, Docker smoke). Those produce phantom
failures that make autonomous execution unsafe. This harness targets ONLY what
NSForge actually has.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Prefer `uv run` if uv is available (repo convention); else run bare.
_UV = shutil.which("uv")
_WRAPPABLE = {"ruff", "mypy", "pytest", "python"}


def _wrap(cmd: list[str]) -> list[str]:
    """Wrap python-tool invocations with `uv run` when uv is present."""
    if _UV and cmd and cmd[0] in _WRAPPABLE:
        return ["uv", "run", *cmd]
    return cmd


# gate name -> command (relative to repo root)
GATES: dict[str, list[str]] = {
    "lint": ["ruff", "check", "."],
    "format": ["ruff", "format", "--check", "."],
    "type": ["mypy", "src", "--ignore-missing-imports"],
    "import": ["python", "-c", "import nsforge_mcp.server; print('server import ok')"],
    "manifest": ["python", "scripts/gen_capabilities.py", "--check"],
    "test": ["pytest", "-q"],
    "bench": ["python", "scripts/bench.py"],
    "generic": ["python", "scripts/genericity.py"],
    "provenance": ["python", "scripts/provenance.py"],
    "harness": ["python", "scripts/harness_selfcheck.py"],
    "diff": ["git", "diff", "--check"],
}

# Order chosen so cheap/fast gates fail first.
DEFAULT_ORDER = [
    "lint",
    "format",
    "type",
    "import",
    "manifest",
    "test",
    "bench",
    "generic",
    "provenance",
    "harness",
    "diff",
]

# Human/agent-readable description of what each gate verifies. Kept next to GATES
# so the manifest (docs/agent/capabilities.json) can advertise the live gate list.
GATE_DOC: dict[str, str] = {
    "lint": "ruff lint across src/, tests/, scripts/",
    "format": "ruff format --check (style is enforced, not merely suggested)",
    "type": "mypy strict on src/",
    "import": "the MCP server imports cleanly",
    "manifest": "docs/agent/capabilities.json is in sync with the @mcp.tool set",
    "test": "the pytest suite passes",
    "bench": "known derivations reproduce correctly (benchmarks/*.json)",
    "generic": "unseen, randomly-composed formulas derive correctly (a calculus, not a library)",
    "provenance": "every benchmark derivation carries a complete tool-provenance ledger",
    "harness": "the harness guards its own invariants (version, self-description, gate/doc parity)",
    "diff": "no whitespace errors or leftover conflict markers",
}


def run_gate(name: str) -> dict:
    cmd = _wrap(GATES[name])
    start = time.time()
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)  # noqa: S603
    return {
        "gate": name,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "seconds": round(time.time() - start, 2),
        "cmd": " ".join(cmd),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="NSForge verification harness")
    ap.add_argument("--gates", default="", help="comma-separated subset (default: all)")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON summary")
    args = ap.parse_args()

    selected = (
        [g.strip() for g in args.gates.split(",") if g.strip()] if args.gates else DEFAULT_ORDER
    )
    unknown = [g for g in selected if g not in GATES]
    if unknown:
        print(f"unknown gates: {unknown}; available: {list(GATES)}", file=sys.stderr)
        return 2

    results = []
    for name in selected:
        res = run_gate(name)
        results.append(res)
        if not args.json:
            mark = "PASS" if res["ok"] else "FAIL"
            print(f"[{mark}] {name} ({res['seconds']}s)  $ {res['cmd']}")
            if not res["ok"]:
                sys.stdout.write(res["stdout_tail"])
                sys.stderr.write(res["stderr_tail"])

    passed = sum(1 for r in results if r["ok"])
    summary = {
        "ok": all(r["ok"] for r in results),
        "passed": passed,
        "total": len(results),
        "gates": results,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\n{passed}/{len(results)} gates passed.")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
