from app.models.schemas import QAExchange, RawInput, StructuredHints
from app.providers.llm.mock_provider import MockLLMProvider

_PROVIDER = MockLLMProvider()


def test_optimize_prompt_flags_gaps_with_no_hints():
    raw_input = RawInput(mode="idea", text="Automate invoice review.", hints=StructuredHints())

    result = _PROVIDER.optimize_prompt(raw_input, [])

    assert "industry" in result.gaps
    assert "expected_scale" in result.gaps
    assert "data_sensitivity" in result.gaps


def test_hints_suppress_the_matching_gap():
    raw_input = RawInput(
        mode="idea",
        text="Automate invoice review.",
        hints=StructuredHints(industry="Finance", expected_scale="pilot", data_sensitivity="pii"),
    )

    result = _PROVIDER.optimize_prompt(raw_input, [])

    assert "industry" not in result.gaps
    assert "expected_scale" not in result.gaps
    assert "data_sensitivity" not in result.gaps


def test_prior_answers_are_folded_into_optimized_text_and_suppress_gaps():
    raw_input = RawInput(mode="idea", text="Automate invoice review.", hints=StructuredHints())
    prior_answers = [QAExchange(field="industry", question="What industry?", answer="Finance")]

    result = _PROVIDER.optimize_prompt(raw_input, prior_answers)

    assert "industry" not in result.gaps
    assert "Finance" in result.optimized_text


def test_clarifying_questions_capped_at_three():
    raw_input = RawInput(mode="idea", text="Do a thing.", hints=StructuredHints())

    result = _PROVIDER.optimize_prompt(raw_input, [])

    assert len(result.clarifying_questions) <= 3
