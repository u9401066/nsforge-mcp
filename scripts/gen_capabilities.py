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
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "src" / "nsforge_mcp" / "tools"
OUT = REPO / "docs" / "agent" / "capabilities.json"


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
    return {
        "schema": "nsforge.capabilities/v1",
        "tool_count": len(tools),
        "modules": sorted({t["module"] for t in tools}),
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
