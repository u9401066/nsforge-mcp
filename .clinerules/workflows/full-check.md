# Full Check (NSForge)

Run the verification harness — the single ground-truth gate for this repo.

<execute_command>
<command>uv run python scripts/check.py</command>
</execute_command>

This runs all 14 gates: lint, format, type, security, import, manifest, mcp,
test, bench, generic, provenance, package, harness, diff.
Exit code 0 means green; nonzero means at least one gate failed.

For a machine-readable summary (agents):
<execute_command>
<command>uv run python scripts/check.py --json</command>
</execute_command>

To run a subset of gates:
<execute_command>
<command>uv run python scripts/check.py --gates lint,type,test</command>
</execute_command>

If any gate fails, stop and report the failures before proceeding.
