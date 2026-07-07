"""Tests for the retrieval-augmented suggester (roadmap C).

The suggester ranks candidate next steps; retrieval is the agent's job (open
sources), ranking is ours. These verify the relevance signals: a candidate that
defines a symbol present in the current expression ranks above one that does not,
and goal-term overlap breaks ties.
"""

from __future__ import annotations

from nsforge.domain.suggester import Candidate, suggest_next


def test_candidate_defining_a_present_symbol_ranks_first() -> None:
    candidates = [
        Candidate(id="ideal_gas", expression="P = n*R*T/V", description="pressure"),
        Candidate(id="arrhenius", expression="k = A*exp(-Ea/(R*T))", description="rate constant"),
    ]
    ranked = suggest_next("temperature dependence of decay", "C = C0*exp(-k*t)", candidates)
    assert ranked[0].candidate.id == "arrhenius"  # defines k, which appears in the expression
    assert ranked[0].score > ranked[1].score
    assert "k" in ranked[0].rationale


def test_goal_terms_break_ties() -> None:
    candidates = [
        Candidate(id="drag", expression="d = c*w", description="air drag"),
        Candidate(id="friction", expression="g = mu*Fn", description="kinetic friction force"),
    ]
    ranked = suggest_next("add friction to the model", "a = F/m", candidates)
    assert ranked[0].candidate.id == "friction"  # neither resolves a symbol; goal terms decide


def test_provides_field_scores_when_no_equation() -> None:
    candidates = [
        Candidate(id="fric", expression="F - mu*Fn", description="friction term", provides=("F",)),
    ]
    ranked = suggest_next("friction", "a = F/m", candidates)
    assert ranked[0].score >= 2.0  # resolves F, which is present in the expression


def test_irrelevant_candidate_scores_zero() -> None:
    candidates = [Candidate(id="unrelated", expression="q = x*y", description="something else")]
    ranked = suggest_next("compute velocity", "a = F/m", candidates)
    assert ranked[0].score == 0.0
    assert "no direct relevance" in ranked[0].rationale
