# NSForge Agent Harness

Workspace instructions for autonomous agents (Copilot, Cline, Codex, OpenHands,
Hermes, …) working in the **Neurosymbolic Forge (NSForge)** repository.

## Goal

Help build and operate NSForge — an MCP server that turns *concepts* into
verifiable, traceable *entities* (symbols → derivations → algorithms). The AI
orchestrates; deterministic tools reify. See
`docs/reification-ladder-direction.md` for the north star.

## North Star

> Every symbol / equation / value / line of code in a final result must have a
> tool call as its "birth certificate" (provenance). The AI must not hand-derive
> any of them.

Success = the amount the AI computes by hand approaches zero.

## Working Style

- Use Traditional Chinese unless the user asks otherwise.
- Prefer exact file paths, command output summaries, and verification results.
- Offload mechanical/deterministic steps (symbolic calculation, simplification,
  code generation) to tools — do not hand-derive formulas.
- When changing behavior, add a focused regression test under `tests/`.

## Ground Truth: one command

Before and after changes, verify against the green baseline:

```bash
python scripts/check.py            # all gates
python scripts/check.py --json     # machine-readable summary (for agents)
python scripts/check.py --gates lint,type,test   # subset
```

Gates: 14 total — lint, format, type, security, import, manifest, mcp, test,
bench, generic, provenance, package, harness, diff. Exit code 0 = green.
(bench = derivation-correctness of `benchmarks/*.json` through the L3 orchestrator;
generic = arbitrary unseen compositions derive correctly, proving NSForge is a
derivation *calculus*, not a hand-built formula library; provenance = every
benchmark derivation carries a complete tool-provenance ledger, no hand-derived leaks;
mcp = MCP 2.1.1 discovery, schemas, metadata, payloads, resources, prompts, and
legacy-client compatibility stay green;
security = executable source has no high-severity Bandit finding;
package = sdist/wheel build, isolated install, packaged assets, and installed MCP smoke stay green;
harness = the harness self-checks its own invariants — package version parity,
self-describing tools, and gate/doc parity — so agents can trust the signal.)

## Repo Layout (DDD)

- `src/nsforge/domain/`: pure domain models/value objects (no I/O)
- `src/nsforge/application/`: use-cases / orchestration
- `src/nsforge/infrastructure/`: adapters (sympy engine, formula sources, file I/O)
- `src/nsforge_mcp/`: MCP tool layer + server wiring (`server.py`, `tools/`)
- `docs/agent/capabilities.json`: machine-readable tool manifest (self-describing)

## Guardrails

- Keep `src/nsforge/domain` free of I/O and infrastructure imports.
- Do not weaken `mypy` strict or skip gates just to make checks pass.
- Prefer `uv run ...` so tools use the project venv.
- Avoid destructive git ops (`reset --hard`, `clean -fdx`) unless asked.
- Never commit secrets or generated outputs (`dist/`, `.venv/`, `data/`).
- After adding/removing an `@mcp.tool`, regenerate the manifest:
  `python scripts/gen_capabilities.py`.
- MCP runtime baseline: exact SDK 2.1.1 pin, protocol `2026-07-28`, `MCPServer`, 91 catalog
  tools. Fixed startup profiles are legacy 82 (default), workflow 17,
  scientific 35, interactive 35, and full 91. Preserve legacy schemas and
  payloads; add protocol features through the central `ToolSpec` contract and
  verify with the `mcp` gate.
- Compact profiles reject unknown inputs and enforce declared enum/range
  constraints. Strict task runs persist tenant-scoped immutable run, event,
  evidence, and artifact records in SQLite and expose them through
  `nsforge://runs/{run_id}`, `nsforge://runs/{run_id}/events`,
  `nsforge://sessions/{session_id}`, and `nsforge://artifacts/{sha256}` resources.

## Related Files

- `docs/reification-ladder-direction.md` — architecture direction
- `scripts/check.py` — verification harness (ground truth)
- `scripts/gen_capabilities.py` — capability manifest generator
- `.github/copilot-instructions.md` — Copilot rules
- `memory-bank/activeContext.md` — current focus
