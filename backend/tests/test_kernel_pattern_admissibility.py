from app.kernel.pattern_admissibility import evaluate_patterns


def test_contra_indication_beats_indication():
    """Fine-tuning has ATTRIBUTION_REQUIRED as a contra-indication and no
    indication that would otherwise apply here — must be CONTRA_INDICATED,
    never REQUIRED, regardless of what else is present."""
    verdicts, _ = evaluate_patterns({"ATTRIBUTION_REQUIRED", "ENTERPRISE_PRIVATE_DATA"}, set())
    fine_tuning = next(v for v in verdicts if v.pattern_id == "pattern-fine-tuning-knowledge-injection")
    assert fine_tuning.verdict == "CONTRA_INDICATED"


def test_unnecessary_when_no_indication_present():
    verdicts, _ = evaluate_patterns(set(), set())
    graphrag = next(v for v in verdicts if v.pattern_id == "pattern-graphrag")
    assert graphrag.verdict == "UNNECESSARY"


def test_required_when_indication_present():
    verdicts, _ = evaluate_patterns({"ENTERPRISE_PRIVATE_DATA"}, set())
    rag = next(v for v in verdicts if v.pattern_id == "pattern-rag-enterprise-docs")
    assert rag.verdict == "REQUIRED"


def test_subsumption_downgrades_the_lower_tier_pattern():
    """Agentic RAG subsumes single-pass RAG — when both would independently
    verdict REQUIRED, the subsumed one demotes to APPLICABLE so the output
    doesn't list both (Part 6.2)."""
    verdicts, _ = evaluate_patterns({"ENTERPRISE_PRIVATE_DATA", "MULTI_HOP_QUERIES"}, set())
    rag = next(v for v in verdicts if v.pattern_id == "pattern-rag-enterprise-docs")
    agentic_rag = next(v for v in verdicts if v.pattern_id == "pattern-agentic-rag")
    assert agentic_rag.verdict == "REQUIRED"
    assert rag.verdict == "APPLICABLE"


def test_assurance_pattern_required_only_when_capability_mandated():
    verdicts, _ = evaluate_patterns(set(), {"CAP-INPUT-OUTPUT-GUARDRAILS"})
    guardrails = next(v for v in verdicts if v.pattern_id == "pattern-guardrails")
    eval_harness = next(v for v in verdicts if v.pattern_id == "pattern-eval-harness")
    assert guardrails.verdict == "REQUIRED"
    assert eval_harness.verdict == "UNNECESSARY"


def test_deferred_action_signature_yields_conditional_not_unnecessary():
    verdicts, _ = evaluate_patterns({"ACTION_REQUIRED_DEFERRED"}, set())
    agentic_hitl = next(v for v in verdicts if v.pattern_id == "pattern-agentic-hitl")
    assert agentic_hitl.verdict == "CONDITIONAL"


def test_capability_requirements_only_derived_from_required_and_conditional_patterns():
    _, cap_reqs = evaluate_patterns({"ENTERPRISE_PRIVATE_DATA"}, set())
    cap_ids = {c.id for c in cap_reqs}
    assert "CAP-RETRIEVAL-PERMISSION-AWARE" in cap_ids
    for c in cap_reqs:
        assert c.status in ("mandatory", "deferred")
