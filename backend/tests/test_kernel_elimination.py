from app.kernel.candidates import construct_candidates
from app.kernel.elimination import eliminate
from app.kernel.pattern_admissibility import evaluate_patterns


def test_escalated_candidate_is_always_eliminated_by_complexity_budget():
    """CAND-ESCALATED exists specifically to demonstrate the complexity
    budget gate — it must never survive elimination."""
    verdicts, _ = evaluate_patterns({"ENTERPRISE_PRIVATE_DATA"}, {"CAP-INPUT-OUTPUT-GUARDRAILS"})
    candidates = construct_candidates(verdicts)
    escalated = next((c for c in candidates if c.id == "CAND-ESCALATED"), None)
    assert escalated is not None, "expected CAND-ESCALATED to be constructed for this scenario"

    survivors, eliminations = eliminate(candidates)

    assert "CAND-ESCALATED" not in {c.id for c in survivors}
    escalated_elimination = next(e for e in eliminations if e.candidate_id == "CAND-ESCALATED")
    assert escalated_elimination.rule_id == "CPX-BUDGET-01"


def test_base_candidate_always_survives():
    verdicts, _ = evaluate_patterns({"ENTERPRISE_PRIVATE_DATA"}, set())
    candidates = construct_candidates(verdicts)
    survivors, _ = eliminate(candidates)
    assert "CAND-BASE" in {c.id for c in survivors}


def test_elimination_record_carries_evidence_for_every_eliminated_candidate():
    verdicts, _ = evaluate_patterns({"ENTERPRISE_PRIVATE_DATA"}, set())
    candidates = construct_candidates(verdicts)
    _, eliminations = eliminate(candidates)
    for e in eliminations:
        assert e.evidence
        assert e.rule_id
