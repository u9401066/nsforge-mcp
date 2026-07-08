#!/usr/bin/env python3
"""Harness self-check — the gate that guards the harness itself.

An agent harness is only trustworthy if it can detect its own rot. This gate
asserts the invariants that keep NSForge's self-description honest, so an agent
can rely on it:

  1. version single-source — pyproject [project].version == nsforge.__version__
  2. gate parity — the manifest is schema v2 and its advertised gate list
     matches check.py (the live source of truth)
  3. self-describing tools — every tool has a summary and every parameter is typed
  4. no doc drift — AGENTS.md's "Gates:" line documents every gate

Exit 0 = all invariants hold; nonzero prints the specific violations.
"""

from __future__ import annotations

import ast
import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
MANIFEST = REPO / "docs" / "agent" / "capabilities.json"
AGENTS = REPO / "AGENTS.md"

# check.py is the single source of truth for the gate list (scripts/ is not a package).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


def _pyproject_version() -> str:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _package_version() -> str:
    tree = ast.parse((SRC / "nsforge" / "__init__.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets
        ):
            return str(ast.literal_eval(node.value))
    raise AssertionError("nsforge.__version__ not found in src/nsforge/__init__.py")


def main() -> int:
    problems: list[str] = []

    # 1. version single-source
    py_v, pkg_v = _pyproject_version(), _package_version()
    if py_v != pkg_v:
        problems.append(f"version drift: pyproject {py_v!r} != nsforge.__version__ {pkg_v!r}")

    if not MANIFEST.exists():
        print("FAIL harness: manifest missing (run: python scripts/gen_capabilities.py)")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # 2. gate parity
    if manifest.get("schema") != "nsforge.capabilities/v2":
        problems.append(f"manifest schema {manifest.get('schema')!r} != nsforge.capabilities/v2")
    manifest_gates = [g["gate"] for g in manifest.get("harness", [])]
    if manifest_gates != check.DEFAULT_ORDER:
        problems.append(f"manifest gates {manifest_gates} != check.py {check.DEFAULT_ORDER}")
    missing_docs = [g for g in check.DEFAULT_ORDER if not check.GATE_DOC.get(g)]
    if missing_docs:
        problems.append(f"gates missing a GATE_DOC description: {missing_docs}")

    # 3. self-describing tools
    tools = manifest.get("tools", [])
    if manifest.get("tool_count") != len(tools):
        problems.append(f"tool_count {manifest.get('tool_count')} != len(tools) {len(tools)}")
    for tool in tools:
        if not tool.get("summary"):
            problems.append(f"tool {tool.get('name')!r} has no summary")
        for param in tool.get("params", []):
            if not param.get("type"):
                problems.append(f"tool {tool.get('name')!r} param {param.get('name')!r} is untyped")

    # 4. no doc drift — AGENTS.md documents every gate on its "Gates:" line
    agents_text = AGENTS.read_text(encoding="utf-8") if AGENTS.exists() else ""
    gate_line = next((ln for ln in agents_text.splitlines() if ln.strip().startswith("Gates:")), "")
    for gate in check.DEFAULT_ORDER:
        if gate not in gate_line:
            problems.append(f"AGENTS.md 'Gates:' line does not list {gate!r}")

    if problems:
        print("FAIL harness self-check:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        f"harness ok: v{py_v}, {len(tools)} self-describing tools, "
        f"{len(check.DEFAULT_ORDER)} gates in sync with the manifest and AGENTS.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
