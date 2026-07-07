"""
Retrieval-augmented suggestion tool (roadmap C) — the MCP surface.

``derivation_suggest_next`` ranks candidate next steps by relevance to the goal
and the current expression. Retrieval stays open: the agent supplies candidates
from ``formula_search`` (Wikidata / BioModels / SciPy), the session's formulas,
or generic operations; this tool ranks them. NSForge owns the ranking, not a
formula catalog.
"""

from typing import Any

from nsforge.domain.suggester import Candidate, suggest_next


def register_suggest_tools(mcp: Any) -> None:
    """Register the retrieval-augmented suggester tool with the MCP server."""

    @mcp.tool()
    def derivation_suggest_next(
        goal: str,
        current_expression: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Rank candidate next steps for a derivation by relevance.

        Retrieval-augmented: you supply ``candidates`` retrieved from open sources
        (``formula_search`` over Wikidata/BioModels/SciPy, the session's formulas,
        or generic operations); this tool ranks them by how well they advance the
        derivation. A candidate scores highest when it defines a symbol currently
        in ``current_expression`` (so it can be substituted in) and matches the
        goal's terms.

        Args:
            goal: What the derivation is trying to reach (natural language).
            current_expression: The expression derived so far, e.g. "C0*exp(-k*t)".
            candidates: Each ``{"id", "expression"?, "description"?, "kind"?,
                "provides"?}`` — a formula, modification, or operation.

        Returns:
            ``{"success", "goal", "suggestions": [{"id", "score", "kind",
            "expression", "rationale"}]}`` ordered best-first.
        """
        pool = [
            Candidate(
                id=str(c.get("id", "")),
                expression=str(c.get("expression", "")),
                description=str(c.get("description", "")),
                kind=str(c.get("kind", "formula")),
                provides=tuple(str(p) for p in c.get("provides", [])),
            )
            for c in candidates
        ]
        ranked = suggest_next(goal, current_expression, pool)
        return {
            "success": True,
            "goal": goal,
            "suggestions": [
                {
                    "id": s.candidate.id,
                    "score": s.score,
                    "kind": s.candidate.kind,
                    "expression": s.candidate.expression,
                    "rationale": s.rationale,
                }
                for s in ranked
            ],
        }
