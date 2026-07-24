"""Ranks catalog candidates against a signal vector using `scoring.score_item`.

Returns items paired with their ScoringResult, sorted best-first. Callers
(`recommend.py`) decide how many alternates to keep and how to turn the
ranking into a DecisionTrace — this module only ranks.
"""

from app.models.schemas import ScoringResult, SignalVector

Ranked = list[tuple[object, ScoringResult]]


def rank_candidates(
    signal: SignalVector, candidates: list, weights: dict[str, float], rules: dict
) -> Ranked:
    from app.engine.scoring import score_item

    scored = [(item, score_item(signal, item, weights, rules)) for item in candidates]
    scored.sort(key=lambda pair: pair[1].weighted_total, reverse=True)
    return scored
