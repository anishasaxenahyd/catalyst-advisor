from app.engine.config_loader import get_decision_rules
from app.engine.recommend import build_report
from app.engine.workbench_selector import select_workbench
from app.enrichment.service import build_enrichment
from app.models.schemas import ConfidenceScores, SignalVector, StructuredHints
from app.providers.knowledge.factory import get_knowledge_provider
from app.providers.llm.mock_provider import MockLLMProvider


def _signal_vector(**overrides) -> SignalVector:
    defaults = dict(
        use_case_type="Agentic workflow automation",
        industry="Insurance",
        data_sensitivity="pii",
        data_modality="text",
        latency_requirement="near_realtime",
        expected_scale="department",
        automation_level="copilot",
        integration_points=["CRM"],
        tags=["agentic", "workflow", "integration-heavy"],
    )
    defaults.update(overrides)
    return SignalVector(**defaults)


def _pattern(pattern_id: str):
    kp = get_knowledge_provider()
    return next(p for p in kp.list_architecture_templates() if p.id == pattern_id)


def _model():
    kp = get_knowledge_provider()
    return next(m for m in kp.list_models() if m.is_primary_candidate)


def _workbench(signal_vector, model):
    kp = get_knowledge_provider()
    return select_workbench(
        signal_vector,
        model,
        kp.list_security_profiles(),
        kp.list_workspace_tiers(),
        kp.list_compute_profiles(),
        kp.list_deployment_targets(),
    )


def _build(signal_vector, pattern, raw_text="Automate a workflow.", **overrides):
    model = _model()
    workbench = _workbench(signal_vector, model)
    kwargs = dict(
        signal_vector=signal_vector,
        raw_text=raw_text,
        pattern=pattern,
        primary_model=model,
        workbench_recommendation=workbench,
        timeline_estimate="10-15 weeks incl. governance review",
        confidence_scores=ConfidenceScores(overall=80, architecture=80, model=80, workbench=80),
        confidence_rationale="All key fields were user-provided.",
        missing_information=[],
        validation_warnings=[],
        rules=get_decision_rules(),
    )
    kwargs.update(overrides)
    return build_enrichment(**kwargs)


def test_build_enrichment_returns_reusable_assets_for_matching_tags():
    enrichment = _build(_signal_vector(), _pattern("pattern-agentic-hitl"))
    assert len(enrichment.reusable_assets) > 0
    assert all(a.rationale for a in enrichment.reusable_assets)


def test_build_enrichment_returns_similar_solutions_matching_pattern():
    enrichment = _build(_signal_vector(), _pattern("pattern-agentic-hitl"))
    assert len(enrichment.similar_solutions) > 0


def test_build_enrichment_prioritizes_same_industry_similar_solutions():
    enrichment = _build(
        _signal_vector(industry="Insurance", tags=["agentic", "workflow"]), _pattern("pattern-agentic-hitl")
    )
    assert enrichment.similar_solutions[0].industry == "Insurance"


def test_build_enrichment_returns_best_practices_from_knowledge_platform():
    enrichment = _build(_signal_vector(), _pattern("pattern-agentic-hitl"))
    assert len(enrichment.best_practices) > 0
    assert all(bp.vendor and bp.reference for bp in enrichment.best_practices)


def test_build_enrichment_handles_no_tag_overlap_gracefully():
    enrichment = _build(_signal_vector(tags=["nonexistent-tag-xyz"]), _pattern("pattern-batch-classification"))
    assert isinstance(enrichment.reusable_assets, list)
    assert len(enrichment.similar_solutions) > 0


def test_business_understanding_reflects_signal_vector():
    sv = _signal_vector(industry="Healthcare", data_sensitivity="phi", automation_level="autonomous")
    enrichment = _build(sv, _pattern("pattern-agentic-hitl"), raw_text="Automate clinical intake.")
    bu = enrichment.business_understanding
    assert bu.stated_need == "Automate clinical intake."
    assert bu.industry == "Healthcare"
    assert "PHI" in " ".join(bu.key_signals) or "phi" in bu.problem_narrative.lower()
    assert any("autonomous" in s.lower() for s in bu.key_signals)


def test_security_summary_surfaces_relevant_controls_for_pii():
    sv = _signal_vector(data_sensitivity="pii")
    enrichment = _build(sv, _pattern("pattern-agentic-hitl"))
    sec = enrichment.security_summary
    assert sec.security_profile_name
    assert len(sec.considerations) > 0
    assert len(sec.relevant_controls) > 0
    assert all(c.category == "security_control" for c in sec.relevant_controls)


def test_security_summary_includes_matched_solution_considerations():
    sv = _signal_vector(industry="Insurance", tags=["agentic", "workflow"])
    enrichment = _build(sv, _pattern("pattern-agentic-hitl"))
    all_solution_considerations = {
        item for sol in enrichment.similar_solutions for item in sol.security_considerations
    }
    assert set(enrichment.security_summary.considerations) & all_solution_considerations


def test_governance_recommendations_include_compliance_and_policy_and_knowledge_sources():
    sv = _signal_vector(data_sensitivity="phi", automation_level="autonomous", expected_scale="enterprise")
    enrichment = _build(sv, _pattern("pattern-autonomous-multi-agent"))
    sources = {g.source for g in enrichment.governance_recommendations}
    assert "policy_rule" in sources
    assert "enterprise_knowledge" in sources
    assert any(g.framework == "HIPAA-eligible" for g in enrichment.governance_recommendations)


def test_governance_recommendations_apply_autonomy_policy_from_pattern_even_without_hint():
    sv = _signal_vector(automation_level="assist")
    enrichment = _build(sv, _pattern("pattern-autonomous-multi-agent"))
    titles = {g.title for g in enrichment.governance_recommendations}
    assert "Mandatory kill-switch and audit logging" in titles


def test_implementation_roadmap_matches_pattern_complexity_tier():
    pattern = _pattern("pattern-autonomous-multi-agent")
    enrichment = _build(_signal_vector(), pattern)
    roadmap = enrichment.implementation_roadmap
    assert len(roadmap.phases) == 5
    assert roadmap.total_timeline == "10-15 weeks incl. governance review"
    assert all(p.name and p.duration and p.goals and p.deliverables for p in roadmap.phases)


def test_implementation_roadmap_always_uses_the_canonical_five_phases():
    pattern = _pattern("pattern-batch-classification")
    enrichment = _build(_signal_vector(), pattern)
    phases = enrichment.implementation_roadmap.phases
    assert [p.name for p in phases] == ["Discovery", "Prototype", "Build", "Pilot", "Rollout"]
    assert all(p.risks for p in phases)


def test_evidence_confidence_summary_aggregates_counts():
    enrichment = _build(_signal_vector(), _pattern("pattern-agentic-hitl"))
    summary = enrichment.evidence_confidence_summary
    assert summary.overall_confidence == 80
    assert summary.dimension_confidence == {"architecture": 80, "model": 80, "workbench": 80}
    assert summary.best_practice_count == len(enrichment.best_practices)
    assert summary.similar_solution_count == len(enrichment.similar_solutions)
    assert summary.reusable_asset_count == len(enrichment.reusable_assets)
    assert str(summary.best_practice_count) in summary.evidence_strength_summary


def test_build_report_attaches_full_enrichment_without_altering_existing_fields():
    kp = get_knowledge_provider()
    llm = MockLLMProvider()
    report = build_report(
        mode="idea",
        raw_text="An agentic workflow that pulls CRM data and routes contract redlines for human approval.",
        hints=StructuredHints(industry="Legal Services"),
        llm=llm,
        kp=kp,
    )
    assert report.enrichment is not None
    assert report.architecture_recommendation.pattern.id
    assert report.model_recommendation.primary.id
    assert report.enrichment.business_understanding.industry == "Legal Services"
    assert report.enrichment.implementation_roadmap.phases
    assert report.enrichment.evidence_confidence_summary.overall_confidence == report.confidence_scores.overall
    assert report.report_title
    assert report.one_line_summary
    assert report.executive_cards.recommended_pattern
    assert 0 <= report.implementation_readiness.score <= 100
    assert report.implementation_readiness.label in ("Very High", "High", "Good", "Needs More Information")
    assert report.business_value.cost_savings_estimate
    assert report.business_value.roi_estimate
    assert all(r.status == "Open" for r in report.risks)
    assert report.model_recommendation.alternatives[0].relative_cost in ("low", "medium", "high")
