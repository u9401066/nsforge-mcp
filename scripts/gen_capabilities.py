#!/usr/bin/env python3
"""Generate a machine-readable capability manifest for NSForge MCP tools.

This makes the repo SELF-DESCRIBING: any autonomous agent can read
`docs/agent/capabilities.json` to discover every tool, its signature, and
one-line summary — without importing the server, running it, or scraping prose.

Single source of truth = the `@mcp.tool()`-decorated functions in
`src/nsforge_mcp/tools/*.py`, parsed via the `ast` module (no runtime import,
so it stays deterministic and dependency-free).

Usage:
    python scripts/gen_capabilities.py            # write the manifest
    python scripts/gen_capabilities.py --check     # exit 1 if manifest is stale
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "src" / "nsforge_mcp" / "tools"
OUT = REPO / "docs" / "agent" / "capabilities.json"

# check.py is the single source of truth for the harness gate list; import it so
# the manifest always advertises the live gates (scripts/ is not a package).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

NORTH_STAR = (
    "Every symbol, equation, value, and line of code in a result has a tool call "
    "as its birth certificate; the AI hand-derives nothing."
)

COMMANDS = {
    "verify": "python scripts/check.py",
    "verify_json": "python scripts/check.py --json",
    "verify_subset": "python scripts/check.py --gates lint,type,test",
    "regen_manifest": "python scripts/gen_capabilities.py",
    "test": "uv run pytest",
    "serve": "uv run nsforge-mcp",
}

MODULE_SUMMARIES = {
    "derivation": "Stateful derivation sessions: compose, step, track, store",
    "task": "Declarative task spec to reification-ladder run/explore (L2/L3)",
    "suggest": "Retrieval-augmented next-step ranking",
    "calculate": "Limits, series, sums, inequalities, probability, numerics",
    "simplify": "Advanced algebra (expand/factor/apart) plus Laplace/Fourier transforms",
    "verify": "Equality, derivative, integral, solution, dimensions",
    "expression": "Parse, validate, extract symbols",
    "codegen": "Python function, LaTeX, report, standalone script",
    "formula": "Formula search: Wikidata, BioModels, SciPy constants",
    "music": "Symbolic tones to waveform, spectrum, WAV",
    "meta": "Runtime self-description: health, manifest",
}


def _project_version() -> str:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _optional_modules() -> list[str]:
    """Read OPTIONAL_MODULES from config.py statically (single source of truth)."""
    config = REPO / "src" / "nsforge_mcp" / "config.py"
    tree = ast.parse(config.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
            value = node.value
        else:
            continue
        if "OPTIONAL_MODULES" in names and value is not None:
            return list(ast.literal_eval(value))
    return []


def _is_mcp_tool(dec: ast.expr) -> bool:
    """Match both `@mcp.tool()` and `@mcp.tool`."""
    node = dec.func if isinstance(dec, ast.Call) else dec
    return isinstance(node, ast.Attribute) and node.attr == "tool"


def _params(fn: ast.FunctionDef) -> list[dict]:
    out = []
    for arg in fn.args.args:
        if arg.arg in {"self", "cls"}:
            continue
        out.append(
            {
                "name": arg.arg,
                "type": ast.unparse(arg.annotation) if arg.annotation else None,
            }
        )
    return out


def collect() -> list[dict]:
    tools: list[dict] = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and any(
                _is_mcp_tool(d) for d in node.decorator_list
            ):
                doc = ast.get_docstring(node) or ""
                summary = next((ln.strip() for ln in doc.splitlines() if ln.strip()), "")
                tools.append(
                    {
                        "name": node.name,
                        "module": path.stem,
                        "params": _params(node),
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "summary": summary,
                    }
                )
    tools.sort(key=lambda t: (t["module"], t["name"]))
    return tools


def build() -> dict:
    tools = collect()
    modules = sorted({t["module"] for t in tools})
    optional = _optional_modules()
    default_tools = [t for t in tools if t["module"] not in optional]
    return {
        "schema": "nsforge.capabilities/v2",
        "version": _project_version(),
        "north_star": NORTH_STAR,
        "tool_count": len(tools),
        "default_tool_count": len(default_tools),
        "modules": modules,
        "optional_modules": optional,
        "module_summaries": {m: MODULE_SUMMARIES.get(m, "") for m in modules},
        "harness": [
            {
                "gate": g,
                "verifies": check.GATE_DOC.get(g, ""),
                "command": " ".join(check.GATES[g]),
            }
            for g in check.DEFAULT_ORDER
        ],
        "commands": COMMANDS,
        "tools": tools,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if manifest is stale")
    args = ap.parse_args()

    manifest = build()
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(
                f"manifest missing: {OUT.relative_to(REPO)} "
                "(run: python scripts/gen_capabilities.py)",
                file=sys.stderr,
            )
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(
                "capability manifest is STALE — regenerate: python scripts/gen_capabilities.py",
                file=sys.stderr,
            )
            return 1
        print(f"manifest up to date ({manifest['tool_count']} tools)")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(REPO)} "
        f"({manifest['tool_count']} tools, {len(manifest['modules'])} modules)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
