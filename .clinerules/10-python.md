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
  - Security: `uv run bandit -r src -q -lll`
  - MCP contract: `uv run python scripts/mcp_contract.py`
  - Tests: `uv run pytest`
  - Package: `uv run python scripts/package_smoke.py`

## Discipline
- Do not weaken mypy strict or add blanket `# type: ignore` to pass the gate.
- Add a regression test under `tests/` when fixing a bug.
- After adding/removing an `@mcp.tool`, regenerate the manifest:
  `python scripts/gen_capabilities.py`.
- MCP 2 sync handlers may run in worker threads. Protect shared mutable state,
  use atomic persistence, and add a concurrency regression test for stateful changes.
- Do not parse caller expressions with `eval`, `parse_expr`, or `sympify`; use
  the central allowlisted no-eval parser. Keep paths inside their declared root.
- Strict run persistence belongs behind the application `RunStore` port and an
  infrastructure Unit of Work; domain provenance objects remain I/O-free.
