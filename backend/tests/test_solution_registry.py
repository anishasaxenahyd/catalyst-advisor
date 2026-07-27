from app.solution_registry.factory import load_solution_registry

_VALID_PATTERN_IDS = {
    "pattern-rag-enterprise-docs",
    "pattern-agentic-hitl",
    "pattern-realtime-copilot",
    "pattern-batch-classification",
    "pattern-autonomous-multi-agent",
}


def test_solution_registry_loads_between_20_and_30_entries():
    solutions = load_solution_registry()
    assert 20 <= len(solutions) <= 30


def test_solution_ids_are_unique():
    solutions = load_solution_registry()
    ids = [s.id for s in solutions]
    assert len(ids) == len(set(ids))


def test_every_solution_references_a_known_architecture_pattern():
    solutions = load_solution_registry()
    assert all(s.architecture_pattern_id in _VALID_PATTERN_IDS for s in solutions)


def test_every_solution_has_all_required_narrative_fields():
    solutions = load_solution_registry()
    for s in solutions:
        assert s.business_problem
        assert s.industry
        assert s.business_outcome
        assert len(s.ai_models) > 0
        assert len(s.security_considerations) > 0
        assert len(s.lessons_learned) > 0


def test_solution_registry_spans_multiple_industries_and_patterns():
    solutions = load_solution_registry()
    assert len({s.industry for s in solutions}) >= 10
    assert len({s.architecture_pattern_id for s in solutions}) == len(_VALID_PATTERN_IDS)


def test_load_solution_registry_is_cached():
    assert load_solution_registry() is load_solution_registry()
