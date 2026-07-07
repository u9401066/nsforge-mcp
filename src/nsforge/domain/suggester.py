"""
Retrieval-augmented suggestion ranking for the derivation loop (roadmap C).

NSForge does not own a formula catalog. The agent *retrieves* candidate next
steps from open sources (``formula_search`` over Wikidata / BioModels / SciPy,
the session's loaded formulas, or generic operations); this module *ranks* them
by relevance to the goal and the current expression — the retrieve-then-rank
pattern (cf. ReProver). Pure: no I/O, no infrastructure imports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# SymPy functions / constants that are not derivation symbols.
_NON_SYMBOLS = frozenset(
    {"exp", "log", "ln", "sqrt", "Abs", "sin", "cos", "tan", "pi", "E", "I", "oo"}
)
_IDENT = re.compile(r"[A-Za-z_]\w*")
_WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Candidate:
    """A possible next step the agent could take, from any open source."""

    id: str
    expression: str = ""
    description: str = ""
    kind: str = "formula"  # formula | modification | operation
    provides: tuple[str, ...] = ()  # symbols this candidate introduces / defines


@dataclass(frozen=True)
class ScoredCandidate:
    """A candidate with its relevance score and a human-readable rationale."""

    candidate: Candidate
    score: float
    rationale: str


def _symbols(text: str) -> set[str]:
    """Free identifiers in ``text``, excluding SymPy function/constant names."""
    return {m.group() for m in _IDENT.finditer(text)} - _NON_SYMBOLS


def _defined_symbols(candidate: Candidate) -> set[str]:
    """Symbols the candidate introduces (explicit ``provides`` or an equation LHS)."""
    if candidate.provides:
        return set(candidate.provides)
    if "=" in candidate.expression:
        return _symbols(candidate.expression.split("=", 1)[0])
    return set()


def suggest_next(
    goal: str, current_expression: str, candidates: list[Candidate]
) -> list[ScoredCandidate]:
    """Rank ``candidates`` by relevance to ``goal`` and ``current_expression``.

    A candidate is most relevant when it *defines a symbol that currently appears
    in the expression* (so substituting it in makes progress), and when its
    name/description overlaps the goal. Deterministic and stable (ties keep input
    order).
    """
    current = _symbols(current_expression)
    goal_terms = set(_WORD.findall(goal.lower()))

    scored: list[ScoredCandidate] = []
    for candidate in candidates:
        resolves = sorted(_defined_symbols(candidate) & current)  # can substitute for these
        overlap = len(_symbols(candidate.expression) & current)
        cand_terms = set(_WORD.findall(f"{candidate.id} {candidate.description}".lower()))
        goal_hits = sorted(cand_terms & goal_terms)

        score = 2.0 * len(resolves) + 1.0 * len(goal_hits) + 0.1 * overlap
        reasons: list[str] = []
        if resolves:
            reasons.append(f"defines {resolves} present in the expression")
        if goal_hits:
            reasons.append(f"matches goal terms {goal_hits}")
        if overlap and not resolves:
            reasons.append(f"shares {overlap} symbol(s) with the expression")
        rationale = "; ".join(reasons) or "no direct relevance to the current state"
        scored.append(ScoredCandidate(candidate, round(score, 3), rationale))

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored
