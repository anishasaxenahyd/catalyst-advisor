from app.kernel.catalog_resolution import resolve_capabilities
from app.kernel.schemas import CapabilityRequirement
from app.kernel.sourcing import decide_sourcing
from app.models.schemas import SignalVector
from app.providers.knowledge.factory import get_knowledge_provider

_SIGNAL_NONE = SignalVector(
    use_case_type="test", industry="cross-industry", data_sensitivity="none", data_modality="text",
    latency_requirement="near_realtime", expected_scale="department", automation_level="assist",
)
_SIGNAL_PHI = _SIGNAL_NONE.model_copy(update={"data_sensitivity": "phi"})


def test_reuse_when_a_compliant_asset_provides_the_capability():
    kp = get_knowledge_provider()
    reqs = [CapabilityRequirement(id="CAP-CHUNK-INDEX", name="CAP-CHUNK-INDEX", status="mandatory")]
    resolutions = resolve_capabilities(reqs, _SIGNAL_NONE, kp)
    decisions = decide_sourcing(reqs, {r.capability_id: r for r in resolutions})
    assert decisions[0].decision == "reuse"
    assert decisions[0].asset_ref is not None


def test_build_when_compliance_fit_fails_for_phi():
    """Every catalog asset providing CAP-CHUNK-INDEX in this prototype's
    seed data lacks HIPAA-eligible compliance — under a PHI signal this
    must fall through to build/buy, never a silent reuse."""
    kp = get_knowledge_provider()
    reqs = [CapabilityRequirement(id="CAP-CHUNK-INDEX", name="CAP-CHUNK-INDEX", status="mandatory")]
    resolutions = resolve_capabilities(reqs, _SIGNAL_PHI, kp)
    assert resolutions[0].overall == "gap"
    decisions = decide_sourcing(reqs, {r.capability_id: r for r in resolutions})
    assert decisions[0].decision in ("buy", "build")
    assert decisions[0].asset_ref is None


def test_gap_on_commodity_capability_prefers_buy():
    kp = get_knowledge_provider()
    resolutions = resolve_capabilities(
        [CapabilityRequirement(id="CAP-EVAL-HARNESS", name="CAP-EVAL-HARNESS", status="mandatory")], _SIGNAL_PHI, kp
    )
    # skill-eval-harness-basic has no HIPAA-eligible compliance either -> gap under PHI.
    assert resolutions[0].overall == "gap"
    decisions = decide_sourcing(
        [CapabilityRequirement(id="CAP-EVAL-HARNESS", name="CAP-EVAL-HARNESS", status="mandatory")],
        {r.capability_id: r for r in resolutions},
    )
    assert decisions[0].decision == "buy"


def test_deferred_capability_is_never_sourced():
    reqs = [CapabilityRequirement(id="CAP-TOOL-INVOCATION-GATEWAY", name="x", status="deferred")]
    decisions = decide_sourcing(reqs, {})
    assert decisions[0].decision == "defer"


def test_every_sourcing_decision_names_a_rejected_alternative_unless_reuse():
    kp = get_knowledge_provider()
    reqs = [CapabilityRequirement(id="CAP-CHUNK-INDEX", name="CAP-CHUNK-INDEX", status="mandatory")]
    resolutions = resolve_capabilities(reqs, _SIGNAL_PHI, kp)
    decisions = decide_sourcing(reqs, {r.capability_id: r for r in resolutions})
    for d in decisions:
        if d.decision != "reuse":
            assert d.rejected_alternatives, f"{d.decision} decision should name what it rejected"
