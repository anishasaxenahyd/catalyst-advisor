"""Implementation Readiness — a deterministic composite of numbers the
engine already computed (confidence, feasibility, architecture complexity).
No new scoring dimension, no LLM involvement; just a weighted rollup banded
through the same confidence_label() scale used for Evidence & Confidence.
"""

from app.engine.confidence_bands import confidence_label
from app.models.schemas import ConfidenceScores, FeasibilityScore, ImplementationReadiness

_CONFIDENCE_WEIGHT = 0.4
_TECHNICAL_FEASIBILITY_WEIGHT = 0.3
_BUSINESS_FEASIBILITY_WEIGHT = 0.2
_COMPLEXITY_WEIGHT = 0.1


def compute_implementation_readiness(
    feasibility: FeasibilityScore, confidence_scores: ConfidenceScores, complexity_tier: int
) -> ImplementationReadiness:
    complexity_component = (5 - complexity_tier) / 4 * 100
    score = round(
        _CONFIDENCE_WEIGHT * confidence_scores.overall
        + _TECHNICAL_FEASIBILITY_WEIGHT * feasibility.technical
        + _BUSINESS_FEASIBILITY_WEIGHT * feasibility.business
        + _COMPLEXITY_WEIGHT * complexity_component
    )
    return ImplementationReadiness(score=score, label=confidence_label(score))
