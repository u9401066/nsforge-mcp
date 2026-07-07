---
paths:
  - "pyproject.toml"
  - "CHANGELOG.md"
  - "uv.lock"
  - ".github/workflows/ci.yml"
---

# Release Rules

NSForge ships as a Python package (`nsforge-mcp`). No VSIX / Docker / extension.

## Version Sources (keep in sync)
- Python package version: `pyproject.toml`
- Changelog: `CHANGELOG.md` (add a dated section)
- Lockfile: `uv.lock` (regenerate with `uv lock` when needed)

## Pre-Tag Verification
- `python scripts/check.py` (must be all green)
- `uv build`

## Tag Format
- Annotated tags: `vX.Y.Z`
- Push the commit first, then push the tag.
