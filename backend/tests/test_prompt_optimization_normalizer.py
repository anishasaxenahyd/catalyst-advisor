from app.models.schemas import RawPromptOptimization
from app.validation.prompt_optimization_normalizer import normalize_optimization


def test_empty_optimized_text_falls_back_to_original():
    result = normalize_optimization(RawPromptOptimization(optimized_text="   "), original_text="original idea")
    assert result.optimized_text == "original idea"


def test_unknown_gap_and_question_fields_are_dropped():
    raw = RawPromptOptimization(
        optimized_text="tightened text",
        gaps=["industry", "made_up_field"],
        questions=[
            {"field": "industry", "question": "What industry?"},
            {"field": "made_up_field", "question": "Should be dropped"},
        ],
    )
    result = normalize_optimization(raw, original_text="original idea")

    assert result.gaps == ["industry"]
    assert len(result.clarifying_questions) == 1
    assert result.clarifying_questions[0].field == "industry"


def test_questions_are_capped_and_deduped():
    raw = RawPromptOptimization(
        optimized_text="tightened text",
        questions=[
            {"field": "industry", "question": "Q1"},
            {"field": "industry", "question": "duplicate field, should be dropped"},
            {"field": "data_sensitivity", "question": "Q2"},
            {"field": "expected_scale", "question": "Q3"},
            {"field": "automation_level", "question": "Q4 — should be cut, over the cap"},
        ],
    )
    result = normalize_optimization(raw, original_text="original idea")

    assert len(result.clarifying_questions) == 3
    fields = [q.field for q in result.clarifying_questions]
    assert fields == ["industry", "data_sensitivity", "expected_scale"]


def test_token_estimates_are_computed_locally_not_trusted_from_llm():
    raw = RawPromptOptimization(optimized_text="short")
    result = normalize_optimization(raw, original_text="a much longer original description of the idea")

    assert result.original_token_estimate > result.optimized_token_estimate
