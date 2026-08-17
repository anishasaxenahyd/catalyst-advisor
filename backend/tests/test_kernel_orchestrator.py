import os

os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient

from app.kernel.orchestrator import orchestrate
from app.main import app
from app.models.schemas import StructuredHints
from app.providers.knowledge.factory import get_knowledge_provider
from app.providers.llm.factory import get_llm_provider

client = TestClient(app)

_PHI_BENEFITS_REQUEST = (
    "Build an AI assistant that answers employee health benefits questions using private enterprise "
    "data, provides citations, protects PHI/PII, reuses existing enterprise capabilities, and "
    "eventually supports actions through tools."
)


def setup_function():
    get_llm_provider.cache_clear()


def _report():
    return orchestrate(
        mode="idea",
        raw_text=_PHI_BENEFITS_REQUEST,
        hints=StructuredHints(data_sensitivity="phi"),
        llm=get_llm_provider(),
        kp=get_knowledge_provider(),
    )


def test_recommendation_route_returns_a_decision_kernel_section():
    response = client.post(
        "/api/recommendations",
        json={"mode": "idea", "description": _PHI_BENEFITS_REQUEST, "hints": {"data_sensitivity": "phi"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["decision_kernel"] is not None
    assert body["decision_kernel"]["solution_class_id"]
    assert len(body["decision_kernel"]["pattern_verdicts"]) > 0


def test_recommended_candidate_was_never_eliminated():
    report = _report()
    dk = report.decision_kernel
    eliminated_ids = {e.candidate_id for e in dk.elimination_record}
    assert dk.recommended_candidate_id not in eliminated_ids


def test_phi_scenario_recommends_grounded_rag_with_required_assurance_patterns():
    report = _report()
    dk = report.decision_kernel
    required = {v.pattern_id for v in dk.pattern_verdicts if v.verdict == "REQUIRED"}
    assert "pattern-rag-enterprise-docs" in required
    assert "pattern-guardrails" in required
    assert "pattern-eval-harness" in required
    assert "pattern-observability" in required


def test_graphrag_and_multiagent_are_rejected_with_reasons():
    report = _report()
    rejected = {v.pattern_id: v.reason for v in report.decision_kernel.rejected_patterns}
    assert "pattern-graphrag" in rejected
    assert "pattern-autonomous-multi-agent" in rejected
    assert all(rejected.values()), "every rejection must carry a reason"


def test_phi_obligations_are_present_and_drive_model_approved_capability():
    report = _report()
    obligation_ids = {o.id for o in report.decision_kernel.obligations}
    assert "OBL-PHI-BOUNDARY" in obligation_ids
    assert "OBL-PER-USER-AUTHZ" in obligation_ids


def test_every_enterprise_reuse_item_references_a_real_catalog_asset():
    report = _report()
    kp = get_knowledge_provider()
    known_ids = {a.id for a in kp.list_enterprise_assets()}
    for item in report.enterprise_reuse:
        assert item.asset.id in known_ids


def test_grounding_validator_would_reject_an_unresolvable_reference():
    from app.kernel.schemas import KernelResult
    from app.kernel.validation import KernelValidationError, validate

    report = _report()
    dk = report.decision_kernel
    result = KernelResult(
        sufficiency=dk.sufficiency,
        obligations=dk.obligations,
        solution_class_id=dk.solution_class_id,
        solution_class_name=dk.solution_class_name,
        capability_requirements=[],
        pattern_verdicts=dk.pattern_verdicts,
        precedent_findings=dk.precedent_findings,
        asset_resolutions=[],
        sourcing_decisions=dk.sourcing_decisions,
        candidates=dk.candidates,
        surviving_candidate_ids=[],
        elimination_record=dk.elimination_record,
        recommended_candidate_id=dk.recommended_candidate_id,
        alternatives=dk.alternatives,
        rejected_patterns=dk.rejected_patterns,
        assumptions=dk.kernel_assumptions,
        counterfactuals=dk.counterfactuals,
        decision_record=dk.decision_record,
    )
    result.obligations = [*result.obligations, dk.obligations[0].model_copy(update={"id": "OBL-DOES-NOT-EXIST"})]
    try:
        validate(result, known_asset_ids=set())
        assert False, "expected validation to reject an unresolvable obligation ID"
    except KernelValidationError as exc:
        assert "OBL-DOES-NOT-EXIST" in str(exc)


def test_sufficiency_halts_when_data_sensitivity_is_unspecified():
    report = orchestrate(
        mode="idea",
        raw_text="Build something to help the team with documents.",
        hints=StructuredHints(),
        llm=get_llm_provider(),
        kp=get_knowledge_provider(),
    )
    assert report.decision_kernel.sufficiency.status == "HALT_CLARIFY"
    assert any(q.field_or_signature == "data_sensitivity" for q in report.decision_kernel.sufficiency.blocking_questions)
