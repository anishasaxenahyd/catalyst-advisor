"""Business Value KPIs — every field traces to a config table (same
band/tier-lookup pattern as `estimator.py`/`relative_cost_bands`) or an
existing scoring value. Nothing here is a free-invented number; ranges are
directional estimates, and the UI labels them as such.
"""

from app.engine.confidence_bands import confidence_label
from app.models.schemas import (
    ArchitecturePattern,
    BusinessValueSummary,
    ConfidenceScores,
    ModelRecommendation,
    SignalVector,
)


def compute_business_value(
    model_recommendation: ModelRecommendation,
    signal_vector: SignalVector,
    confidence_scores: ConfidenceScores,
    pattern: ArchitecturePattern,
    timeline_estimate: str,
    rules: dict,
) -> BusinessValueSummary:
    cost_savings_estimate = rules["cost_savings_estimate_by_relative_cost"][model_recommendation.relative_cost]
    productivity_estimate = rules["productivity_estimate_by_automation_level"][signal_vector.automation_level]
    accuracy_confidence_label = f"{confidence_label(confidence_scores.model)} confidence (pending pilot validation)"
    roi_estimate = rules["roi_estimate_by_complexity_tier"][str(pattern.complexity_tier)]

    return BusinessValueSummary(
        cost_savings_estimate=cost_savings_estimate,
        productivity_estimate=productivity_estimate,
        accuracy_confidence_label=accuracy_confidence_label,
        timeline_estimate=timeline_estimate,
        roi_estimate=roi_estimate,
    )
