"""Builds a DecisionTrace from a ranked candidate list.

Every field is derived from the ScoringResult objects the engine already
computed — nothing here re-decides anything or asks an LLM for an opinion.
The same function is reused for architecture patterns, models, enterprise
assets, and each Workbench axis, so the frontend can render all of them
with one component.
"""

from app.models.schemas import AlternativeConsidered, DecisionTrace
from app.engine.matcher import Ranked


def _strongest_dimensions(dimension_scores: dict[str, float], top_n: int = 2) -> list[str]:
    ranked = sorted(dimension_scores.items(), key=lambda pair: pair[1], reverse=True)
    return [name for name, _ in ranked[:top_n]]


def _weakest_dimension_gap(
    winner_dims: dict[str, float], other_dims: dict[str, float]
) -> tuple[str, float, float] | None:
    shared = set(winner_dims) & set(other_dims)
    if not shared:
        return None
    dim = min(shared, key=lambda d: other_dims[d] - winner_dims[d])
    return dim, other_dims[dim], winner_dims[dim]


def build_decision_trace(
    ranked: Ranked,
    *,
    assumptions: list[str],
    max_alternatives: int = 3,
) -> DecisionTrace:
    if not ranked:
        raise ValueError("Cannot build a decision trace from an empty ranking.")

    winner, winner_score = ranked[0]
    strongest = _strongest_dimensions(winner_score.dimension_scores)
    why_selected = (
        f"Highest weighted score ({winner_score.weighted_total}/100), "
        f"strongest on {', '.join(strongest) if strongest else 'overall fit'}."
    )

    alternatives: list[AlternativeConsidered] = []
    for item, score in ranked[1 : 1 + max_alternatives]:
        gap = _weakest_dimension_gap(winner_score.dimension_scores, score.dimension_scores)
        if gap:
            dim, their_score, our_score = gap
            why_lower = f"Scored {score.weighted_total}/100 (vs {winner_score.weighted_total}) — weakest on {dim} ({their_score} vs {our_score})."
        else:
            why_lower = f"Scored {score.weighted_total}/100 (vs {winner_score.weighted_total})."
        alternatives.append(
            AlternativeConsidered(id=item.id, name=item.name, score=score.weighted_total, why_lower=why_lower)
        )

    evidence = [
        f"{dim}={value}/100"
        for dim, value in sorted(winner_score.dimension_scores.items(), key=lambda p: p[1], reverse=True)
    ]

    return DecisionTrace(
        selected=winner.id,
        why_selected=why_selected,
        alternatives_considered=alternatives,
        assumptions=assumptions,
        confidence=winner_score.confidence,
        evidence=evidence,
    )
