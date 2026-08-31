"""Every task_plan execution reference must resolve or declare its namespace."""

from __future__ import annotations

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge_mcp.tool_contract import profile_tool_names


def test_task_plan_has_no_phantom_local_tool_references() -> None:
    spec = DerivationTaskSpec.from_dict(
        {
            "name": "resolvable-plan",
            "goal": "derive y",
            "given": {"x": "scalar"},
            "unknowns": ["y"],
            "base_formulas": ["y = x + 1"],
            "acceptance": [
                {"kind": "equivalence", "params": {"reference": "x + 1"}},
                {
                    "kind": "boundary",
                    "params": {"variable": "x", "at": "0", "expected": "1"},
                },
                {"kind": "limit", "params": {"variable": "x", "to": "0", "expected": "1"}},
                {
                    "kind": "dimensional",
                    "params": {"units": {"x": "1"}, "expected_units": "1"},
                },
            ],
        }
    )

    plan = TaskOrchestrator(spec).plan()
    assert "generate_pseudocode" not in {step.tool for step in plan}
    workflow_tools = profile_tool_names("workflow")
    for step in plan:
        if step.executor == "local":
            assert step.tool in workflow_tools
        elif step.executor == "internal":
            assert step.tool.startswith("internal:")
        else:
            assert step.executor == "external"
            assert ":" in step.tool
