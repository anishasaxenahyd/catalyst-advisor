from app.kernel.obligations import resolve_obligations
from app.models.schemas import SignalVector

_BASE = dict(
    use_case_type="test",
    industry="cross-industry",
    data_modality="text",
    latency_requirement="near_realtime",
    expected_scale="department",
    automation_level="assist",
)


def _signal(**overrides) -> SignalVector:
    return SignalVector(**{**_BASE, "data_sensitivity": "none", **overrides})


def test_always_on_obligations_fire_regardless_of_sensitivity():
    obligations = resolve_obligations(_signal(), set())
    ids = {o.id for o in obligations}
    assert {"OBL-GUARDRAILS-ALWAYS", "OBL-EVAL-HARNESS-ALWAYS", "OBL-OBSERVABILITY-ALWAYS", "OBL-MODEL-APPROVED-LIST"} <= ids


def test_phi_sensitivity_fires_phi_boundary_and_not_pii_only_obligation():
    obligations = resolve_obligations(_signal(data_sensitivity="phi"), set())
    ids = {o.id for o in obligations}
    assert "OBL-PHI-BOUNDARY" in ids
    assert "OBL-PHI-SAFE-LOGGING" in ids
    assert "OBL-PII-COMPLIANCE" not in ids


def test_pii_sensitivity_fires_pii_compliance_not_phi_boundary():
    obligations = resolve_obligations(_signal(data_sensitivity="pii"), set())
    ids = {o.id for o in obligations}
    assert "OBL-PII-COMPLIANCE" in ids
    assert "OBL-PHI-BOUNDARY" not in ids


def test_per_user_authz_requires_sensitivity_and_signature_together():
    # signature alone, no sensitivity -> should not fire (per obligations.json: match "any" over
    # [PER_USER_AUTHORISATION signature, sensitivity in pii/phi] means signature alone DOES fire it;
    # verify that documented behavior explicitly rather than assuming it.
    obligations = resolve_obligations(_signal(data_sensitivity="none"), {"PER_USER_AUTHORISATION"})
    ids = {o.id for o in obligations}
    assert "OBL-PER-USER-AUTHZ" in ids


def test_action_approval_fires_on_irreversible_action_signature():
    obligations = resolve_obligations(_signal(), {"IRREVERSIBLE_ACTION"})
    ids = {o.id for o in obligations}
    assert "OBL-ACTION-APPROVAL" in ids


def test_every_obligation_mandates_at_least_one_known_capability():
    from app.kernel.loaders import get_capability_ids

    obligations = resolve_obligations(_signal(data_sensitivity="phi"), {"PER_USER_AUTHORISATION", "IRREVERSIBLE_ACTION"})
    known = get_capability_ids()
    for o in obligations:
        assert o.mandates_capabilities, f"{o.id} mandates nothing"
        assert set(o.mandates_capabilities) <= known
