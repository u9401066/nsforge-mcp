# NSForge: Project Rules

Rules for Cline (and other agents) in the Neurosymbolic Forge repository.

## Goals
- Build an MCP server that reifies concepts into verifiable, traceable entities
  (symbols → derivations → algorithms). The AI orchestrates; tools reify.
- Prefer correctness and reproducibility: deterministic outputs, clear error
  paths, and regression tests.

## Repo Layout (DDD)
- `src/nsforge/domain/`: pure domain models/value objects (no I/O)
- `src/nsforge/application/`: use-cases / orchestration
- `src/nsforge/infrastructure/`: adapters (sympy engine, formula sources, file I/O)
- `src/nsforge_mcp/`: MCP tool layer + server wiring (`server.py`, `tools/`)

## Canonical Commands
- One-shot verification: `python scripts/check.py`
  (14 gates: lint / format / type / security / import / manifest / mcp / test /
  bench / generic / provenance / package / harness / diff)
- Individual gates: `uv run ruff check .`, `uv run mypy src --ignore-missing-imports`, `uv run pytest`
- Regenerate tool manifest: `python scripts/gen_capabilities.py`

## Safety / Hygiene
- Avoid editing or committing generated/ignored outputs: `dist/`, `data/`, `.venv/`.
- Never print or commit secrets from `.env` or key files.
- Avoid destructive git operations (`reset --hard`, `clean -fdx`) unless explicitly asked.

## Prefer Existing Patterns
- Keep MCP tool outputs backward-compatible when possible.
- MCP baseline is exact SDK 2.1.1 / protocol `2026-07-28` / `MCPServer`; catalog 91,
  with fixed profiles legacy 82 (default), workflow 17, scientific 35,
  interactive 35, and full 91. Preserve legacy schemas and response payloads,
  and run the `mcp` gate.
- Compact profiles are resource-first and strict-input. Strict runs use the
  tenant-scoped immutable SQLite run/artifact store; legacy JSON/YAML remains a
  compatibility adapter, not the strict workflow's authority.
- Add focused tests with fixes; keep changes minimal and scoped.
- Do not weaken mypy strict or skip gates to make checks pass.
- For product/architecture context, start with `memory-bank/activeContext.md`,
  `docs/reification-ladder-direction.md`, and `ARCHITECTURE.md`.

## Repo Defaults
- Default branch: `master`.
