"""The Decision Kernel orchestrator — replaces `app.engine.recommend.build_report`.

Runs the fifteen stages in order, appending to a `KernelResult`, then
projects it into the existing `Report` shape so the current frontend keeps
working unchanged, plus a new `Report.decision_kernel` section carrying the
staged trail (pattern verdicts, sourcing decisions, elimination record,
alternatives, precedents, counterfactuals) for the new report sections.

Two LLM calls only, both schema-bound, both narrating/interpreting already-
decided or extracted facts — never deciding anything:
  1. `extract_signal_vector` (unchanged, existing) — Stage 1-2 interpretation.
  2. `generate_executive_report` (unchanged, existing) — final narration.
  3. `narrate_kernel_findings` (new) — narrates rejections/sourcing/alternatives.
Everything else in this file is deterministic.
"""

from app.engine.business_value import compute_business_value
from app.engine.config_loader import get_decision_rules
from app.engine.estimator import estimate_effort, estimate_timeline
from app.engine.readiness import compute_implementation_readiness
from app.engine.workbench_selector import select_workbench
from app.enrichment.business import build_business_understanding
from app.enrichment.service import build_enrichment
from app.kernel import candidates as candidates_stage
from app.kernel import capabilities as capabilities_stage
from app.kernel import catalog_resolution, elimination, framing, obligations as obligations_stage
from app.kernel import pattern_admissibility, precedent as precedent_stage, selection, sourcing
from app.kernel import solution_class as solution_class_stage
from app.kernel import sufficiency as sufficiency_stage
from app.kernel import validation
from app.kernel.counterfactuals import compute_counterfactuals
from app.kernel.loaders import get_pattern_by_id
from app.kernel.schemas import (
    Candidate,
    DecisionNode,
    DecisionRecord,
    KernelNarrationInput,
    KernelResult,
    PatternRecord,
)
from app.models.schemas import (
    AlternativeConsidered,
    ArchitecturePattern,
    ArchitectureRecommendation,
    ConfidenceScores,
    DecisionTrace,
    EnterpriseReuseItem,
    FeasibilityScore,
    KernelReport,
    ModelAlternative,
    ModelRecommendation,
    RawInput,
    Report,
    Risk,
    StructuredHints,
    SubmissionMode,
)
from app.providers.knowledge.base import KnowledgeProvider
from app.providers.llm.base import LLMProvider
from app.validation.signal_normalizer import describe_confidence, missing_information

_CONFIDENCE_NUMBER = {"established": 92, "reasoned": 75, "provisional": 55, "uncertain": 35}


def _architecture_confidence_class(sufficiency_status: str, precedent_findings: list) -> str:
    if sufficiency_status == "HALT_CLARIFY":
        return "provisional"
    if any(f.usage == "transferable_decision_evidence" for f in precedent_findings):
        return "established"
    if sufficiency_status == "PROCEED_WITH_QUESTIONS":
        return "provisional"
    return "reasoned"


def _headline_pattern(candidate: Candidate) -> PatternRecord:
    by_id = get_pattern_by_id()
    solution_patterns = [by_id[pid] for pid in candidate.pattern_ids if by_id[pid].pattern_type == "solution"]
    if not solution_patterns:
        raise validation.KernelValidationError(f"Candidate '{candidate.id}' has no solution pattern.")
    return max(solution_patterns, key=lambda p: p.complexity_tier)


def _to_architecture_pattern(pattern: PatternRecord) -> ArchitecturePattern:
    return ArchitecturePattern(
        id=pattern.id,
        name=pattern.name,
        description=pattern.description,
        complexity_tier=pattern.complexity_tier,
        suitable_for_tags=pattern.indications,
        scale_ceiling=pattern.scale_ceiling,
        mermaid_template=pattern.mermaid_template,
    )


def _relative_band(tier: int, bands: dict[str, list[int]]) -> str:
    for level, tiers in bands.items():
        if tier in tiers:
            return level
    return "medium"


def _select_model(signal, signature_ids: set[str], kp: KnowledgeProvider):
    """Deterministic eligibility + cheapest-fit selection over
    CAP-MODEL-SERVING-APPROVED-tagged models — same style as
    `workbench_selector`, not a weighted score."""
    candidates_ = [m for m in kp.list_models() if m.is_primary_candidate and "CAP-MODEL-SERVING-APPROVED" in m.capabilities]
    pool = candidates_ or [m for m in kp.list_models() if m.is_primary_candidate]

    required_compliance = get_decision_rules()["data_sensitivity_required_compliance"].get(signal.data_sensitivity, [])
    compliant = [m for m in pool if not required_compliance or any(f in m.compliance for f in required_compliance)]
    pool = compliant or pool

    if "IMAGE_MODALITY" in signature_ids:
        image_capable = [m for m in pool if "CAP-IMAGE-DOCUMENT-UNDERSTANDING" in m.capabilities or "image" in m.modality]
        pool = image_capable or pool

    ranked = sorted(pool, key=lambda m: (m.cost_tier, m.latency_tier))
    return ranked[0], ranked[1:3]


def _build_decision_record(result_parts: dict) -> DecisionRecord:
    """Lightweight evidence chain — not a full traversal engine, enough to
    project 'why was this recommended' as node/edge derivation, per Part 10."""
    record = DecisionRecord()
    for ob in result_parts["obligations"]:
        record.add_node(DecisionNode(id=ob.id, type="Obligation", statement=ob.title, provenance="policy_rule", stage="obligations"))
    for entry in result_parts["pattern_verdicts"]:
        if entry.verdict not in ("REQUIRED", "CONDITIONAL"):
            continue
        node = record.add_node(
            DecisionNode(
                id=f"PATTERN:{entry.pattern_id}",
                type="PatternVerdict",
                statement=f"{entry.pattern_name}: {entry.verdict}",
                provenance="pattern_contract",
                stage="pattern_admissibility",
            )
        )
        for sig in entry.matched_indications:
            record.add_edge(f"SIGNATURE:{sig}", node.id, "mandates")
    for sd in result_parts["sourcing_decisions"]:
        node = record.add_node(
            DecisionNode(
                id=f"SOURCING:{sd.capability_id}",
                type="SourcingDecision",
                statement=f"{sd.capability_id} -> {sd.decision}" + (f" ({sd.asset_ref})" if sd.asset_ref else ""),
                provenance="catalog_fact" if sd.asset_ref else "model_inference",
                stage="sourcing",
            )
        )
        record.add_edge(f"CAP:{sd.capability_id}", node.id, "resolves")
    for finding in result_parts["precedent_findings"]:
        record.add_node(
            DecisionNode(
                id=f"PRECEDENT:{finding.solution_id}",
                type="PrecedentFinding",
                statement=f"{finding.title} ({finding.evidence_class}, {finding.usage})",
                provenance="precedent",
                stage="precedent",
            )
        )
    return record


def run_kernel(signal, raw_text: str, kp: KnowledgeProvider) -> tuple[KernelResult, Candidate]:
    """Stages 3-15 over an already-extracted SignalVector. Stages 1-2 are
    the caller's `llm.extract_signal_vector()` call (see `orchestrate`)."""
    solution_assumptions = framing.detect_solution_assumptions(raw_text)
    signature_instances = framing.derive_requirement_signatures(signal, raw_text)
    signature_ids = {s.id for s in signature_instances}
    kernel_assumptions = framing.build_assumptions(signal, solution_assumptions)

    sufficiency = sufficiency_stage.evaluate_sufficiency(signal)

    obligations = obligations_stage.resolve_obligations(signal, signature_ids)
    obligation_ids = {o.id for o in obligations}

    solution_class, _ranked_classes = solution_class_stage.determine_solution_class(signature_ids)

    cap_reqs_from_obligations = capabilities_stage.derive_from_obligations(obligations)
    mandatory_cap_ids = {c.id for c in cap_reqs_from_obligations}

    pattern_verdicts, cap_reqs_from_patterns = pattern_admissibility.evaluate_patterns(signature_ids, mandatory_cap_ids)

    merged_caps: dict[str, object] = {c.id: c for c in cap_reqs_from_obligations}
    for c in cap_reqs_from_patterns:
        if c.id not in merged_caps or (merged_caps[c.id].status != "mandatory" and c.status == "mandatory"):
            merged_caps[c.id] = c
    capability_requirements = list(merged_caps.values())

    admissible_pattern_ids = {v.pattern_id for v in pattern_verdicts if v.verdict in ("REQUIRED", "CONDITIONAL", "APPLICABLE")}
    precedent_findings = precedent_stage.find_precedents(obligation_ids, signature_ids, admissible_pattern_ids, signal)

    asset_resolutions = catalog_resolution.resolve_capabilities(capability_requirements, signal, kp)
    resolutions_by_cap = {r.capability_id: r for r in asset_resolutions}
    sourcing_decisions = sourcing.decide_sourcing(capability_requirements, resolutions_by_cap)

    candidates_list = candidates_stage.construct_candidates(pattern_verdicts)
    survivors, elimination_record = elimination.eliminate(candidates_list)
    recommended, alternatives = selection.select(survivors)

    rejected_patterns = [v for v in pattern_verdicts if v.verdict in ("UNNECESSARY", "CONTRA_INDICATED")]
    counterfactuals = compute_counterfactuals(pattern_verdicts, obligations)

    decision_record = _build_decision_record(
        {"obligations": obligations, "pattern_verdicts": pattern_verdicts, "sourcing_decisions": sourcing_decisions, "precedent_findings": precedent_findings}
    )

    result = KernelResult(
        sufficiency=sufficiency,
        obligations=obligations,
        solution_class_id=solution_class.id,
        solution_class_name=solution_class.name,
        capability_requirements=capability_requirements,
        pattern_verdicts=pattern_verdicts,
        precedent_findings=precedent_findings,
        asset_resolutions=asset_resolutions,
        sourcing_decisions=sourcing_decisions,
        candidates=candidates_list,
        surviving_candidate_ids=[c.id for c in survivors],
        elimination_record=elimination_record,
        recommended_candidate_id=recommended.id,
        alternatives=alternatives,
        rejected_patterns=rejected_patterns,
        assumptions=kernel_assumptions,
        counterfactuals=counterfactuals,
        decision_record=decision_record,
    )

    known_asset_ids = {a.id for a in kp.list_enterprise_assets()} | {m.id for m in kp.list_models()}
    validation.validate(result, known_asset_ids)

    return result, recommended


def orchestrate(mode: SubmissionMode, raw_text: str, hints: StructuredHints, llm: LLMProvider, kp: KnowledgeProvider) -> Report:
    rules = get_decision_rules()

    known_tags = sorted({tag for m in kp.list_models() for tag in m.suitable_for_tags} | {tag for a in kp.list_enterprise_assets() for tag in a.tags})
    raw_input = RawInput(mode=mode, text=raw_text, hints=hints, known_tags=known_tags)
    signal = llm.extract_signal_vector(raw_input)

    kernel_result, recommended_candidate = run_kernel(signal, raw_text, kp)
    signature_ids = {s.id for s in framing.derive_requirement_signatures(signal, raw_text)}

    headline_pattern = _headline_pattern(recommended_candidate)
    architecture_pattern = _to_architecture_pattern(headline_pattern)

    top_verdict = next(v for v in kernel_result.pattern_verdicts if v.pattern_id == headline_pattern.id)
    confidence_class = _architecture_confidence_class(kernel_result.sufficiency.status, kernel_result.precedent_findings)
    architecture_confidence = _CONFIDENCE_NUMBER[confidence_class]

    sourcing_for_headline = [
        s for s in kernel_result.sourcing_decisions
        if s.capability_id in headline_pattern.required_capabilities
    ]
    sourcing_summary = "; ".join(f"{s.capability_name}: {s.decision}" for s in sourcing_for_headline) or "No catalog-resolvable capabilities beyond the pattern itself."
    architecture_trace = DecisionTrace(
        selected=headline_pattern.name,
        why_selected=f"{top_verdict.reason} Sourcing: {sourcing_summary}",
        alternatives_considered=[
            AlternativeConsidered(id=v.pattern_id, name=v.pattern_name, score=0.0, why_lower=v.reason)
            for v in kernel_result.rejected_patterns[:3]
        ],
        assumptions=[a.statement for a in kernel_result.assumptions],
        confidence=architecture_confidence,
        evidence=[f"verdict={top_verdict.verdict}", f"solution_class={kernel_result.solution_class_name}"],
        missing_information=missing_information(signal.field_provenance),
        validation_warnings=[w.reason for w in signal.validation_warnings],
        confidence_rationale=describe_confidence(signal.field_provenance),
    )
    architecture_recommendation = ArchitectureRecommendation(
        pattern=architecture_pattern, rationale=architecture_trace.why_selected, decision_trace=architecture_trace
    )

    top_model, alt_models = _select_model(signal, signature_ids, kp)
    model_confidence = 90 if top_model.compliance and signal.data_sensitivity != "none" else 78
    model_trace = DecisionTrace(
        selected=top_model.name,
        why_selected=f"Cheapest approved model meeting compliance and modality requirements (cost_tier={top_model.cost_tier}, latency_tier={top_model.latency_tier}).",
        alternatives_considered=[
            AlternativeConsidered(id=m.id, name=m.name, score=0.0, why_lower=f"Higher cost_tier ({m.cost_tier}) or latency_tier ({m.latency_tier}) than the selected model.")
            for m in alt_models
        ],
        assumptions=[a.statement for a in kernel_result.assumptions],
        confidence=model_confidence,
        evidence=[f"cost_tier={top_model.cost_tier}", f"compliance={top_model.compliance}"],
        missing_information=missing_information(signal.field_provenance),
        validation_warnings=[w.reason for w in signal.validation_warnings],
        confidence_rationale=describe_confidence(signal.field_provenance),
    )
    model_alternatives = [
        ModelAlternative(
            model=m,
            rationale=f"Eligible alternative (cost_tier={m.cost_tier}).",
            trade_off=f"Higher cost_tier ({m.cost_tier}) or latency_tier ({m.latency_tier}) than {top_model.name}.",
            relative_cost=_relative_band(m.cost_tier, rules["relative_cost_bands"]),
        )
        for m in alt_models
    ]
    model_recommendation = ModelRecommendation(
        primary=top_model,
        primary_rationale=model_trace.why_selected,
        alternatives=model_alternatives,
        relative_cost=_relative_band(top_model.cost_tier, rules["relative_cost_bands"]),
        relative_latency=_relative_band(top_model.latency_tier, rules["relative_latency_bands"]),
        suitability_rationale=f"Modality '{signal.data_modality}' against {top_model.name}'s supported modalities {top_model.modality}; compliance coverage for '{signal.data_sensitivity}': {top_model.compliance}.",
        decision_trace=model_trace,
    )

    workbench_recommendation = select_workbench(
        signal, top_model, kp.list_security_profiles(), kp.list_workspace_tiers(), kp.list_compute_profiles(), kp.list_deployment_targets()
    )

    enterprise_reuse = [
        EnterpriseReuseItem(asset=asset, rationale=sd.justification)
        for sd in kernel_result.sourcing_decisions
        if sd.decision in ("reuse", "extend") and sd.asset_ref
        for asset in kp.list_enterprise_assets()
        if asset.id == sd.asset_ref
    ]

    feasibility = FeasibilityScore(technical=architecture_confidence, business=round((architecture_confidence + model_confidence) / 2))
    effort_estimate = estimate_effort(architecture_pattern, rules)
    timeline_estimate = estimate_timeline(architecture_pattern, rules)
    confidence_scores = ConfidenceScores(
        overall=round((architecture_confidence + model_confidence + workbench_recommendation.decision_trace.confidence) / 3),
        architecture=architecture_confidence,
        model=model_confidence,
        workbench=round(workbench_recommendation.decision_trace.confidence),
    )

    business_understanding = build_business_understanding(signal, raw_text)
    engine_output = _engine_output_for_narrative(
        signal, business_understanding, architecture_recommendation, enterprise_reuse,
        model_recommendation, workbench_recommendation, feasibility, effort_estimate,
        timeline_estimate, confidence_scores,
    )
    narrative = llm.generate_executive_report(engine_output)

    narration_input = KernelNarrationInput(
        solution_class_name=kernel_result.solution_class_name,
        pattern_verdicts=kernel_result.pattern_verdicts,
        sourcing_decisions=kernel_result.sourcing_decisions,
        candidates=kernel_result.candidates,
        elimination_record=kernel_result.elimination_record,
        recommended_candidate_label=recommended_candidate.label,
        alternatives=kernel_result.alternatives,
        precedent_findings=kernel_result.precedent_findings,
    )
    narrative_extras = llm.narrate_kernel_findings(narration_input)

    implementation_readiness = compute_implementation_readiness(feasibility, confidence_scores, architecture_pattern.complexity_tier)
    business_value = compute_business_value(model_recommendation, signal, confidence_scores, architecture_pattern, timeline_estimate, rules)
    risks = [Risk(**r.model_dump(), status="Open") for r in narrative.risks]

    enrichment = build_enrichment(
        signal, raw_text, architecture_pattern, top_model, workbench_recommendation, timeline_estimate,
        confidence_scores, architecture_trace.confidence_rationale, architecture_trace.missing_information,
        architecture_trace.validation_warnings, rules,
    )

    combined_assumptions = [a.statement for a in kernel_result.assumptions] + [
        a for a in narrative.assumptions if a not in [k.statement for k in kernel_result.assumptions]
    ]

    kernel_report = KernelReport(
        solution_class_id=kernel_result.solution_class_id,
        solution_class_name=kernel_result.solution_class_name,
        sufficiency=kernel_result.sufficiency,
        obligations=kernel_result.obligations,
        pattern_verdicts=kernel_result.pattern_verdicts,
        rejected_patterns=kernel_result.rejected_patterns,
        precedent_findings=kernel_result.precedent_findings,
        sourcing_decisions=kernel_result.sourcing_decisions,
        candidates=kernel_result.candidates,
        elimination_record=kernel_result.elimination_record,
        recommended_candidate_id=kernel_result.recommended_candidate_id,
        alternatives=kernel_result.alternatives,
        kernel_assumptions=kernel_result.assumptions,
        counterfactuals=kernel_result.counterfactuals,
        narrative_extras=narrative_extras,
        decision_record=kernel_result.decision_record,
    )

    return Report(
        mode=mode,
        signal_vector=signal,
        report_title=narrative.report_title,
        one_line_summary=narrative.one_line_summary,
        executive_cards=narrative.executive_cards,
        feasibility=feasibility,
        implementation_readiness=implementation_readiness,
        architecture_recommendation=architecture_recommendation,
        enterprise_reuse=enterprise_reuse,
        model_recommendation=model_recommendation,
        workbench_recommendation=workbench_recommendation,
        effort_estimate=effort_estimate,
        timeline_estimate=timeline_estimate,
        risks=risks,
        assumptions=combined_assumptions,
        confidence_scores=confidence_scores,
        next_best_actions=narrative.next_best_actions,
        business_value=business_value,
        enrichment=enrichment,
        decision_kernel=kernel_report,
    )


def _engine_output_for_narrative(
    signal, business_understanding, architecture_recommendation, enterprise_reuse,
    model_recommendation, workbench_recommendation, feasibility, effort_estimate,
    timeline_estimate, confidence_scores,
):
    from app.models.schemas import EngineOutput

    return EngineOutput(
        signal_vector=signal,
        business_understanding=business_understanding,
        architecture_recommendation=architecture_recommendation,
        enterprise_reuse=enterprise_reuse,
        model_recommendation=model_recommendation,
        workbench_recommendation=workbench_recommendation,
        feasibility=feasibility,
        effort_estimate=effort_estimate,
        timeline_estimate=timeline_estimate,
        confidence_scores=confidence_scores,
    )
