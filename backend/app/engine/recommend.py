"""The orchestrator: signal vector in, deterministically-scored Report out.

This is the one place that calls both a `KnowledgeProvider` and an
`LLMProvider` — and it calls the LLM only at the very start (understand)
and the very end (narrate). Every decision in between is engine code.
"""

from app.engine.config_loader import get_decision_rules, get_scoring_weights
from app.engine.estimator import estimate_effort, estimate_timeline
from app.engine.matcher import rank_candidates
from app.engine.trace import build_decision_trace
from app.engine.workbench_selector import select_workbench
from app.enrichment.service import build_enrichment
from app.models.schemas import (
    ArchitectureRecommendation,
    ConfidenceScores,
    EngineOutput,
    EnterpriseReuseItem,
    FeasibilityScore,
    ModelAlternative,
    ModelRecommendation,
    RawInput,
    Report,
    StructuredHints,
    SubmissionMode,
)
from app.providers.knowledge.base import KnowledgeProvider
from app.providers.llm.base import LLMProvider
from app.validation.signal_normalizer import describe_confidence
from app.validation.signal_normalizer import missing_information as compute_missing_information


def _signal_assumptions(hints: StructuredHints) -> list[str]:
    assumptions = []
    if hints.industry is None:
        assumptions.append("Industry not specified — treated as cross-industry.")
    if hints.data_sensitivity is None:
        assumptions.append("Data sensitivity not specified — defaulted to 'none'; confirm before using real data.")
    if hints.expected_scale is None:
        assumptions.append("Expected scale not specified — defaulted to 'department'.")
    if hints.automation_level is None:
        assumptions.append("Automation level not specified — inferred heuristically from the description text.")
    return assumptions or ["All key signal fields were explicitly provided."]


def _relative_band(tier: int, bands: dict[str, list[int]]) -> str:
    for level, tiers in bands.items():
        if tier in tiers:
            return level
    return "medium"


def _known_tags(kp: KnowledgeProvider) -> list[str]:
    """The Catalog's controlled tag vocabulary — every value that
    `technical_fit` scoring can actually match a SignalVector.tags entry
    against. Passed to the LLM so it doesn't invent tags that will always
    score zero regardless of how accurately they describe the use case."""
    tags: set[str] = set()
    for model in kp.list_models():
        tags.update(model.suitable_for_tags)
    for pattern in kp.list_architecture_templates():
        tags.update(pattern.suitable_for_tags)
    for asset in kp.list_enterprise_assets():
        tags.update(asset.tags)
    return sorted(tags)


def build_report(
    mode: SubmissionMode,
    raw_text: str,
    hints: StructuredHints,
    llm: LLMProvider,
    kp: KnowledgeProvider,
) -> Report:
    weights = get_scoring_weights()
    rules = get_decision_rules()
    assumptions = _signal_assumptions(hints)

    # ---- understand (LLM) ----
    raw_input = RawInput(mode=mode, text=raw_text, hints=hints, known_tags=_known_tags(kp))
    signal_vector = llm.extract_signal_vector(raw_input)

    # Computed once from the Validation layer's output and stamped onto
    # every DecisionTrace below — architecture, model, and workbench all
    # stem from the same one signal-vector extraction, so they share the
    # same explanation of what was missing and why confidence is what it is.
    trace_enrichment = {
        "missing_information": compute_missing_information(signal_vector.field_provenance),
        "validation_warnings": [w.reason for w in signal_vector.validation_warnings],
        "confidence_rationale": describe_confidence(signal_vector.field_provenance),
    }

    # ---- score: architecture pattern ----
    ranked_patterns = rank_candidates(signal_vector, kp.list_architecture_templates(), weights, rules)
    architecture_trace = build_decision_trace(ranked_patterns, assumptions=assumptions).model_copy(
        update=trace_enrichment
    )
    top_pattern = ranked_patterns[0][0]
    architecture_recommendation = ArchitectureRecommendation(
        pattern=top_pattern, rationale=architecture_trace.why_selected, decision_trace=architecture_trace
    )

    # ---- score: model ----
    # Support-only models (embeddings, moderation) are excluded from the
    # primary/alternative ranking — they're catalog entries, not standalone
    # recommendations. See AIModel.is_primary_candidate.
    primary_candidate_models = [m for m in kp.list_models() if m.is_primary_candidate]
    ranked_models = rank_candidates(signal_vector, primary_candidate_models, weights, rules)
    model_trace = build_decision_trace(ranked_models, assumptions=assumptions).model_copy(update=trace_enrichment)
    top_model = ranked_models[0][0]
    model_alternatives = [
        ModelAlternative(
            model=item,
            rationale=f"Ranked #{idx + 2} by weighted score ({score.weighted_total}/100).",
            trade_off=next(a.why_lower for a in model_trace.alternatives_considered if a.id == item.id),
        )
        for idx, (item, score) in enumerate(ranked_models[1:3])
    ]
    model_recommendation = ModelRecommendation(
        primary=top_model,
        primary_rationale=model_trace.why_selected,
        alternatives=model_alternatives,
        relative_cost=_relative_band(top_model.cost_tier, rules["relative_cost_bands"]),
        relative_latency=_relative_band(top_model.latency_tier, rules["relative_latency_bands"]),
        suitability_rationale=(
            f"Modality '{signal_vector.data_modality}' against {top_model.name}'s supported modalities "
            f"{top_model.modality}; compliance coverage for data sensitivity "
            f"'{signal_vector.data_sensitivity}': {top_model.compliance}."
        ),
        decision_trace=model_trace,
    )

    # ---- score: enterprise assets (reuse) ----
    ranked_assets = rank_candidates(signal_vector, kp.list_enterprise_assets(), weights, rules)
    threshold = rules["enterprise_reuse_display_threshold"]
    above_threshold = [(item, score) for item, score in ranked_assets if score.weighted_total >= threshold]
    reuse_pairs = above_threshold[:5] or ranked_assets[:3]
    enterprise_reuse = [
        EnterpriseReuseItem(
            asset=item,
            rationale=f"Reuse score {item.reuse_score}/100; weighted fit for this use case {score.weighted_total}/100.",
        )
        for item, score in reuse_pairs
    ]

    # ---- workbench (rule-based, not weighted-scored) ----
    workbench_recommendation = select_workbench(
        signal_vector,
        top_model,
        kp.list_security_profiles(),
        kp.list_workspace_tiers(),
        kp.list_compute_profiles(),
        kp.list_deployment_targets(),
    )
    workbench_recommendation = workbench_recommendation.model_copy(
        update={"decision_trace": workbench_recommendation.decision_trace.model_copy(update=trace_enrichment)}
    )

    feasibility = FeasibilityScore(
        technical=round(ranked_patterns[0][1].weighted_total),
        business=round((architecture_trace.confidence + model_trace.confidence) / 2),
    )
    effort_estimate = estimate_effort(top_pattern, rules)
    timeline_estimate = estimate_timeline(top_pattern, rules)
    confidence_scores = ConfidenceScores(
        overall=round(
            (architecture_trace.confidence + model_trace.confidence + workbench_recommendation.decision_trace.confidence)
            / 3
        ),
        architecture=round(architecture_trace.confidence),
        model=round(model_trace.confidence),
        workbench=round(workbench_recommendation.decision_trace.confidence),
    )

    engine_output = EngineOutput(
        signal_vector=signal_vector,
        architecture_recommendation=architecture_recommendation,
        enterprise_reuse=enterprise_reuse,
        model_recommendation=model_recommendation,
        workbench_recommendation=workbench_recommendation,
        feasibility=feasibility,
        effort_estimate=effort_estimate,
        timeline_estimate=timeline_estimate,
        confidence_scores=confidence_scores,
    )

    # ---- narrate (LLM) ----
    narrative = llm.generate_executive_report(engine_output)

    # ---- enrich (deterministic; AI Catalog + Solution Registry + Enterprise
    # Knowledge Platform + config-driven governance/roadmap rules) ----
    enrichment = build_enrichment(
        signal_vector,
        raw_text,
        top_pattern,
        top_model,
        workbench_recommendation,
        timeline_estimate,
        confidence_scores,
        trace_enrichment["confidence_rationale"],
        trace_enrichment["missing_information"],
        trace_enrichment["validation_warnings"],
        rules,
    )

    return Report(
        mode=mode,
        signal_vector=signal_vector,
        executive_summary=narrative.executive_summary,
        feasibility=feasibility,
        architecture_recommendation=architecture_recommendation,
        enterprise_reuse=enterprise_reuse,
        model_recommendation=model_recommendation,
        workbench_recommendation=workbench_recommendation,
        effort_estimate=effort_estimate,
        timeline_estimate=timeline_estimate,
        risks=narrative.risks,
        assumptions=narrative.assumptions,
        confidence_scores=confidence_scores,
        next_best_actions=narrative.next_best_actions,
        enrichment=enrichment,
    )
