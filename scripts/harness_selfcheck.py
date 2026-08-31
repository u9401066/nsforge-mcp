#!/usr/bin/env python3
"""Harness self-check — the gate that guards the harness itself.

An agent harness is only trustworthy if it can detect its own rot. This gate
asserts the invariants that keep NSForge's self-description honest, so an agent
can rely on it:

  1. version parity — pyproject and both package literals agree
  2. gate parity — the manifest is schema v4 and its advertised gate list
     matches check.py (the live source of truth)
  3. self-describing tools — every tool has typed inputs, profiles, and MCP 2 metadata
  4. dependency parity — pyproject, runtime constant, and manifest agree on MCP
  5. no doc drift — AGENTS.md's "Gates:" paragraph documents every gate

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

from nsforge_mcp.tool_contract import MCP_SDK_REQUIREMENT  # noqa: E402


def _pyproject_version() -> str:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _pyproject_mcp_requirement() -> str:
    """Return the specifier portion of the direct MCP dependency."""
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    for dependency in data["project"]["dependencies"]:
        if dependency == "mcp":
            return ""
        if dependency.startswith("mcp") and dependency[3:4] in "<>=!~":
            return dependency[3:]
    raise AssertionError("direct mcp dependency not found in pyproject.toml")


def _module_version(init_path: Path) -> str:
    tree = ast.parse(init_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets
        ):
            return str(ast.literal_eval(node.value))
    raise AssertionError(f"__version__ not found in {init_path}")


def main() -> int:
    problems: list[str] = []

    # 1. version parity (pyproject drives every package release)
    py_v = _pyproject_version()
    for pkg in ("nsforge", "nsforge_mcp"):
        pkg_v = _module_version(SRC / pkg / "__init__.py")
        if pkg_v != py_v:
            problems.append(f"version drift: pyproject {py_v!r} != {pkg}.__version__ {pkg_v!r}")

    if not MANIFEST.exists():
        print("FAIL harness: manifest missing (run: python scripts/gen_capabilities.py)")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # 2. gate parity
    if manifest.get("schema") != "nsforge.capabilities/v4":
        problems.append(f"manifest schema {manifest.get('schema')!r} != nsforge.capabilities/v4")
    manifest_gates = [g["gate"] for g in manifest.get("harness", [])]
    if manifest_gates != check.DEFAULT_ORDER:
        problems.append(f"manifest gates {manifest_gates} != check.py {check.DEFAULT_ORDER}")
    missing_docs = [g for g in check.DEFAULT_ORDER if not check.GATE_DOC.get(g)]
    if missing_docs:
        problems.append(f"gates missing a GATE_DOC description: {missing_docs}")

    optional = manifest.get("optional_modules")
    if optional is None:
        problems.append("manifest missing 'optional_modules'")
    elif not set(optional).issubset(manifest.get("modules", [])):
        problems.append(f"optional_modules {optional} not a subset of modules")

    mcp_contract = manifest.get("mcp", {})
    if mcp_contract.get("protocol_revision") != "2026-07-28":
        problems.append("manifest MCP protocol revision is not 2026-07-28")
    for key in ("sdk_requirement", "transports", "resources", "prompts", "features"):
        if not mcp_contract.get(key):
            problems.append(f"manifest MCP contract missing {key!r}")
    required_features = {
        "tool_profiles",
        "strict_input_validation",
        "resource_links",
        "resource_subscriptions",
        "resolve_injection",
        "immutable_run_artifact_resources",
        "opentelemetry_correlation",
    }
    missing_features = required_features - set(mcp_contract.get("features", []))
    if missing_features:
        problems.append(f"manifest MCP contract missing features: {sorted(missing_features)}")

    expected_profile_counts = {
        "legacy": 82,
        "workflow": 17,
        "scientific": 35,
        "interactive": 35,
        "full": 91,
    }
    actual_profile_counts = {
        name: profile.get("tool_count") for name, profile in manifest.get("profiles", {}).items()
    }
    if actual_profile_counts != expected_profile_counts:
        problems.append(
            f"manifest profile counts {actual_profile_counts} != {expected_profile_counts}"
        )

    # The manifest generator uses a runtime constant for import-safe discovery;
    # guard that duplicate against the packaging source of truth.
    project_mcp = _pyproject_mcp_requirement()
    manifest_mcp = mcp_contract.get("sdk_requirement")
    if project_mcp != MCP_SDK_REQUIREMENT or manifest_mcp != project_mcp:
        problems.append(
            "MCP dependency drift: "
            f"pyproject={project_mcp!r}, constant={MCP_SDK_REQUIREMENT!r}, "
            f"manifest={manifest_mcp!r}"
        )

    # 3. self-describing tools
    tools = manifest.get("tools", [])
    if manifest.get("tool_count") != len(tools):
        problems.append(f"tool_count {manifest.get('tool_count')} != len(tools) {len(tools)}")
    for tool in tools:
        if not tool.get("summary"):
            problems.append(f"tool {tool.get('name')!r} has no summary")
        if not tool.get("title"):
            problems.append(f"tool {tool.get('name')!r} has no MCP title")
        if tool.get("structured_output") is not True:
            problems.append(f"tool {tool.get('name')!r} does not require structured output")
        annotations = tool.get("annotations", {})
        for hint in (
            "readOnlyHint",
            "destructiveHint",
            "idempotentHint",
            "openWorldHint",
        ):
            if not isinstance(annotations.get(hint), bool):
                problems.append(f"tool {tool.get('name')!r} has no boolean {hint}")
        if tool.get("meta", {}).get("org.nsforge/protocolRevision") != "2026-07-28":
            problems.append(f"tool {tool.get('name')!r} has stale MCP _meta")
        if not tool.get("profiles"):
            problems.append(f"tool {tool.get('name')!r} has no tool-profile membership")
        if not tool.get("provenance_mode"):
            problems.append(f"tool {tool.get('name')!r} has no provenance mode")
        for param in tool.get("params", []):
            if not param.get("type"):
                problems.append(f"tool {tool.get('name')!r} param {param.get('name')!r} is untyped")

    # 5. no doc drift — AGENTS.md documents every gate in its "Gates:" paragraph
    agents_text = AGENTS.read_text(encoding="utf-8") if AGENTS.exists() else ""
    gate_lines: list[str] = []
    collecting = False
    for line in agents_text.splitlines():
        if line.strip().startswith("Gates:"):
            collecting = True
        if collecting:
            if not line.strip():
                break
            gate_lines.append(line.strip())
    gate_line = " ".join(gate_lines)
    for gate in check.DEFAULT_ORDER:
        if gate not in gate_line:
            problems.append(f"AGENTS.md 'Gates:' paragraph does not list {gate!r}")

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
