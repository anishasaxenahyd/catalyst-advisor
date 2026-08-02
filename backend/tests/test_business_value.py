from app.engine.business_value import compute_business_value
from app.engine.config_loader import get_decision_rules
from app.models.schemas import ConfidenceScores, DecisionTrace, ModelRecommendation, SignalVector
from app.providers.knowledge.factory import get_knowledge_provider


def _signal_vector(**overrides) -> SignalVector:
    defaults = dict(
        use_case_type="Invoice review automation",
        industry="Finance",
        data_sensitivity="pii",
        data_modality="text",
        latency_requirement="near_realtime",
        expected_scale="department",
        automation_level="copilot",
    )
    defaults.update(overrides)
    return SignalVector(**defaults)


def _model_recommendation(relative_cost: str) -> ModelRecommendation:
    kp = get_knowledge_provider()
    model = next(m for m in kp.list_models() if m.is_primary_candidate)
    trace = DecisionTrace(selected=model.id, why_selected="Best fit.", confidence=80.0)
    return ModelRecommendation(
        primary=model,
        primary_rationale="Best fit.",
        relative_cost=relative_cost,
        relative_latency="medium",
        suitability_rationale="Fits the use case.",
        decision_trace=trace,
    )


def _pattern(pattern_id: str = "pattern-rag-enterprise-docs"):
    kp = get_knowledge_provider()
    return next(p for p in kp.list_architecture_templates() if p.id == pattern_id)


def test_business_value_fields_are_grounded_in_config_tables():
    rules = get_decision_rules()
    confidence = ConfidenceScores(overall=85, architecture=85, model=85, workbench=85)
    value = compute_business_value(
        _model_recommendation("low"),
        _signal_vector(automation_level="copilot"),
        confidence,
        _pattern(),
        "7-10 weeks incl. governance review",
        rules,
    )
    assert value.cost_savings_estimate == rules["cost_savings_estimate_by_relative_cost"]["low"]
    assert value.productivity_estimate == rules["productivity_estimate_by_automation_level"]["copilot"]
    assert value.roi_estimate == rules["roi_estimate_by_complexity_tier"][str(_pattern().complexity_tier)]
    assert value.timeline_estimate == "7-10 weeks incl. governance review"
    assert "confidence" in value.accuracy_confidence_label.lower()


def test_higher_relative_cost_yields_lower_cost_savings_estimate():
    rules = get_decision_rules()
    confidence = ConfidenceScores(overall=85, architecture=85, model=85, workbench=85)
    low_cost = compute_business_value(
        _model_recommendation("low"), _signal_vector(), confidence, _pattern(), "x", rules
    )
    high_cost = compute_business_value(
        _model_recommendation("high"), _signal_vector(), confidence, _pattern(), "x", rules
    )
    assert low_cost.cost_savings_estimate != high_cost.cost_savings_estimate
