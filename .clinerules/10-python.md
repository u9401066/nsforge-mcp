---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "scripts/**/*.py"
  - "pyproject.toml"
---

# Python Rules (uv / ruff / mypy / pytest)

## Environment
- Use `uv` for running tools (avoid ad-hoc `pip`).
- Prefer `uv run ...` so checks execute in the right venv and dependency set.

## Architecture Guardrails
- Keep `src/nsforge/domain` free of I/O, filesystem access, and infrastructure imports.
- Put orchestration/side-effects in `src/nsforge/application` or `src/nsforge/infrastructure`.
- MCP tool wiring lives in `src/nsforge_mcp/` (`server.py`, `tools/`).

## Validation Gates
- One command: `python scripts/check.py`
- Or individually:
  - Lint: `uv run ruff check .`
  - Format: `uv run ruff format --check .`
  - Types: `uv run mypy src --ignore-missing-imports`
  - MCP contract: `uv run python scripts/mcp_contract.py`
  - Tests: `uv run pytest`

## Discipline
- Do not weaken mypy strict or add blanket `# type: ignore` to pass the gate.
- Add a regression test under `tests/` when fixing a bug.
- After adding/removing an `@mcp.tool`, regenerate the manifest:
  `python scripts/gen_capabilities.py`.
- MCP 2 sync handlers may run in worker threads. Protect shared mutable state,
  use atomic persistence, and add a concurrency regression test for stateful changes.
