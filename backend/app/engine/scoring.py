"""The six-dimension deterministic scorer.

One function, `score_item`, is reused for architecture patterns, models,
and enterprise assets. A dimension is only scored for an item if the item
actually carries the field that dimension needs (e.g. an EnterpriseAsset
has no `complexity_tier`, so implementation_complexity is skipped for it);
the remaining dimensions' weights are renormalized so the total is always
out of 100. Nothing here imports a provider implementation or an LLM —
this module is pure functions over plain data, config-injected.
"""

from app.models.schemas import ScoringResult, SignalVector
from app.validation.signal_normalizer import TRACKED_FIELDS

DIMENSIONS = (
    "technical_fit",
    "enterprise_reuse",
    "security_compliance",
    "cost_efficiency",
    "implementation_complexity",
    "scalability",
)


def _technical_fit(signal: SignalVector, item) -> float | None:
    # ArchitecturePattern/AIModel use `suitable_for_tags`; EnterpriseAsset uses `tags`.
    item_tags = getattr(item, "suitable_for_tags", None) or getattr(item, "tags", None)
    if not item_tags:
        return None
    overlap = len(set(signal.tags) & set(item_tags))
    return min(100.0, (overlap / len(item_tags)) * 100)


def _enterprise_reuse(item) -> float | None:
    return float(item.reuse_score) if hasattr(item, "reuse_score") else None


def _security_compliance(signal: SignalVector, item, rules: dict) -> float | None:
    if not hasattr(item, "compliance"):
        return None
    required = rules["data_sensitivity_required_compliance"].get(signal.data_sensitivity, [])
    if not required:
        return 100.0
    return 100.0 if any(r in item.compliance for r in required) else 20.0


def _cost_efficiency(signal: SignalVector, item, rules: dict) -> float | None:
    if not hasattr(item, "cost_tier"):
        return None
    table = rules["cost_efficiency_by_scale"][signal.expected_scale]
    return float(table[str(item.cost_tier)])


def _implementation_complexity(signal: SignalVector, item, rules: dict) -> float | None:
    if not hasattr(item, "complexity_tier"):
        return None
    ceiling = rules["automation_complexity_ceiling"][signal.automation_level]
    if item.complexity_tier <= ceiling:
        return 100.0
    over = item.complexity_tier - ceiling
    penalty = over * rules["complexity_penalty_per_tier_over"]
    return max(float(rules["complexity_min_score"]), 100.0 - penalty)


def _scalability(signal: SignalVector, item, rules: dict) -> float | None:
    if not hasattr(item, "scale_ceiling"):
        return None
    rank = rules["scale_rank"]
    gap = rank[item.scale_ceiling] - rank[signal.expected_scale]
    bands = rules["scalability_score_by_rank_gap"]
    if gap >= 0:
        return float(bands["0_or_better"])
    if gap == -1:
        return float(bands["minus_1"])
    return float(bands["minus_2_or_worse"])


def _completeness(signal: SignalVector, rules: dict) -> float:
    """Provenance-weighted completeness: a signal built entirely from
    user-supplied hints should read as more trustworthy than one the LLM
    inferred, which in turn should outrank one that fell through to a
    default. Weights are config-driven (`provenance_confidence_weight`);
    this function only knows how to average them across the tracked
    fields, using `SignalVector.field_provenance` recorded by the
    Validation layer — not a heuristic guess at which fields "seem"
    populated, as it was before that layer existed.
    """
    provenance_weight = rules["provenance_confidence_weight"]
    per_field = [
        provenance_weight.get(signal.field_provenance.get(field, "default"), provenance_weight["default"])
        for field in TRACKED_FIELDS
    ]
    fraction = sum(per_field) / len(per_field)
    floor = rules["confidence_completeness_floor"]
    return floor + fraction * (1 - floor)


def score_item(signal: SignalVector, item, weights: dict[str, float], rules: dict) -> ScoringResult:
    raw_scores: dict[str, float] = {}

    technical_fit = _technical_fit(signal, item)
    if technical_fit is not None:
        raw_scores["technical_fit"] = technical_fit

    enterprise_reuse = _enterprise_reuse(item)
    if enterprise_reuse is not None:
        raw_scores["enterprise_reuse"] = enterprise_reuse

    security_compliance = _security_compliance(signal, item, rules)
    if security_compliance is not None:
        raw_scores["security_compliance"] = security_compliance

    cost_efficiency = _cost_efficiency(signal, item, rules)
    if cost_efficiency is not None:
        raw_scores["cost_efficiency"] = cost_efficiency

    implementation_complexity = _implementation_complexity(signal, item, rules)
    if implementation_complexity is not None:
        raw_scores["implementation_complexity"] = implementation_complexity

    scalability = _scalability(signal, item, rules)
    if scalability is not None:
        raw_scores["scalability"] = scalability

    available_weight = sum(weights[d] for d in raw_scores)
    if available_weight == 0:
        weighted_total = 0.0
    else:
        weighted_total = sum(raw_scores[d] * weights[d] for d in raw_scores) / available_weight

    confidence = round(weighted_total * _completeness(signal, rules), 1)

    return ScoringResult(
        dimension_scores={d: round(v, 1) for d, v in raw_scores.items()},
        weighted_total=round(weighted_total, 1),
        confidence=confidence,
    )
