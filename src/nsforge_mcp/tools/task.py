"""
Task orchestration tools (L2 DTS + L3 orchestrator) — the MCP surface.

Turns a declarative Derivation Task Spec (DTS) into a provenance-tagged plan of
tool calls, and runs the deterministic phases of the reification ladder. This is
how a general agent runs a large derivation task from a single declarative spec.

See docs/reification-ladder-direction.md.
"""

from typing import Any

from nsforge.application.task_orchestrator import TaskOrchestrator
from nsforge.domain.task_spec import DerivationTaskSpec
from nsforge.infrastructure.sympy_engine import SymPyEngine


def register_task_tools(mcp: Any) -> None:
    """Register the L2/L3 task orchestration tools with the MCP server."""

    @mcp.tool()
    def task_plan(spec: dict[str, Any]) -> dict[str, Any]:
        """
        Reify a Derivation Task Spec (DTS) into an ordered plan of tool calls.

        Each planned step names the tool that would produce it (provenance),
        spanning the reification ladder: symbol -> derivation -> algorithm.

        Args:
            spec: A DTS dict with keys: name, goal, given, unknowns, assumptions,
                  base_formulas, modifications, acceptance, metadata.

        Returns:
            {"success": bool, "spec": str, "total": int, "steps": [...]}.
        """
        try:
            dts = DerivationTaskSpec.from_dict(spec)
        except (KeyError, ValueError) as exc:
            return {"success": False, "error": f"invalid spec: {exc}"}

        plan = TaskOrchestrator(dts).plan()
        return {
            "success": True,
            "spec": dts.name,
            "total": len(plan),
            "steps": [
                {
                    "phase": step.phase.value,
                    "tool": step.tool,
                    "purpose": step.purpose,
                    "args": step.args,
                }
                for step in plan
            ],
        }

    @mcp.tool()
    def task_run(spec: dict[str, Any]) -> dict[str, Any]:
        """
        Run the DTS through the reification ladder.

        Concept (validation), symbol (registry), and derivation (composing base
        formulas via substitution + solving on the SymPy engine) rungs execute
        deterministically; when a derivation is produced, the algorithm rung
        reifies it into a Python function. The composed formula is returned in
        "derived_expression" and the code in "generated_code".

        Args:
            spec: A DTS dict (see task_plan).

        Returns:
            {"success", "spec", "derived_expression", "generated_code", "phases"}.
        """
        try:
            dts = DerivationTaskSpec.from_dict(spec)
        except (KeyError, ValueError) as exc:
            return {"success": False, "error": f"invalid spec: {exc}"}

        result = TaskOrchestrator(dts, engine=SymPyEngine()).run()
        return {
            "success": result.ok,
            "spec": result.spec_name,
            "derived_expression": result.derived_expression,
            "generated_code": result.generated_code,
            "phases": [
                {
                    "phase": phase.phase.value,
                    "status": phase.status.value,
                    "detail": phase.detail,
                    "steps": [
                        {"phase": s.phase.value, "tool": s.tool, "purpose": s.purpose}
                        for s in phase.steps
                    ],
                }
                for phase in result.phases
            ],
        }
