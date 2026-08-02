import json

import httpx
import pytest

from app.engine.workbench_selector import select_workbench
from app.models.schemas import (
    ArchitectureRecommendation,
    BusinessUnderstanding,
    ConfidenceScores,
    DecisionTrace,
    EngineOutput,
    FeasibilityScore,
    ModelRecommendation,
    RawInput,
    SignalVector,
    StructuredHints,
)
from app.providers.knowledge.factory import get_knowledge_provider
from app.providers.llm.exceptions import LLMProviderError
from app.providers.llm.groq_provider import GROQ_API_BASE, GroqProvider

_RAW_INPUT = RawInput(mode="idea", text="a support copilot", hints=StructuredHints())


def _engine_output() -> EngineOutput:
    kp = get_knowledge_provider()
    pattern = kp.list_architecture_templates()[0]
    model = next(m for m in kp.list_models() if m.is_primary_candidate)
    trace = DecisionTrace(selected=pattern.id, why_selected="Best fit.", confidence=80.0)
    signal_vector = SignalVector(
        use_case_type="Support copilot",
        industry="Retail",
        data_sensitivity="none",
        data_modality="text",
        latency_requirement="realtime",
        expected_scale="department",
        automation_level="copilot",
    )
    workbench = select_workbench(
        signal_vector,
        model,
        kp.list_security_profiles(),
        kp.list_workspace_tiers(),
        kp.list_compute_profiles(),
        kp.list_deployment_targets(),
    )
    return EngineOutput(
        signal_vector=signal_vector,
        business_understanding=BusinessUnderstanding(
            stated_need="A support copilot.",
            problem_narrative="Support agents need faster, consistent replies.",
            industry="Retail",
            use_case_type="Support copilot",
            data_sensitivity="none",
            data_modality="text",
            latency_requirement="realtime",
            expected_scale="department",
            automation_level="copilot",
        ),
        architecture_recommendation=ArchitectureRecommendation(
            pattern=pattern, rationale="Best fit.", decision_trace=trace
        ),
        enterprise_reuse=[],
        model_recommendation=ModelRecommendation(
            primary=model,
            primary_rationale="Best fit.",
            relative_cost="low",
            relative_latency="medium",
            suitability_rationale="Fits.",
            decision_trace=trace,
        ),
        workbench_recommendation=workbench,
        feasibility=FeasibilityScore(technical=80, business=80),
        effort_estimate="3-5 weeks",
        timeline_estimate="4-7 weeks incl. governance review",
        confidence_scores=ConfidenceScores(overall=80, architecture=80, model=80, workbench=80),
    )

_VALID_SIGNAL_JSON = (
    '{"use_case_type": "support copilot", "industry": "cross-industry", '
    '"data_sensitivity": "none", "data_modality": "text", "latency_requirement": "realtime", '
    '"expected_scale": "department", "automation_level": "copilot", '
    '"integration_points": [], "tags": ["copilot"]}'
)


class _FakeResponse:
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.text = body
        self._body = body

    def json(self):
        return json.loads(self._body)


def _chat_body(content: str) -> str:
    return json.dumps({"choices": [{"message": {"content": content}}]})


def _provider(monkeypatch, responses: list[_FakeResponse], max_retries: int = 2) -> GroqProvider:
    calls = {"n": 0}

    def fake_post(self, url, json=None, headers=None, **_kwargs):
        response = responses[min(calls["n"], len(responses) - 1)]
        calls["n"] += 1
        return response

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    provider = GroqProvider(api_key="fake-key", timeout_seconds=1, max_retries=max_retries)
    provider._test_calls = calls  # type: ignore[attr-defined]
    return provider


def test_retries_on_5xx_then_succeeds(monkeypatch):
    responses = [
        _FakeResponse(500, "server error"),
        _FakeResponse(429, "rate limited"),
        _FakeResponse(200, _chat_body(_VALID_SIGNAL_JSON)),
    ]
    provider = _provider(monkeypatch, responses, max_retries=2)

    result = provider.extract_signal_vector(_RAW_INPUT)

    assert result.use_case_type == "support copilot"
    assert provider._test_calls["n"] == 3  # type: ignore[attr-defined]


def test_exhausts_retries_on_persistent_5xx(monkeypatch):
    responses = [_FakeResponse(503, "unavailable")]
    provider = _provider(monkeypatch, responses, max_retries=1)

    with pytest.raises(LLMProviderError):
        provider.extract_signal_vector(_RAW_INPUT)

    assert provider._test_calls["n"] == 2  # type: ignore[attr-defined]


def test_auth_error_does_not_retry(monkeypatch):
    responses = [_FakeResponse(401, "invalid API key")]
    provider = _provider(monkeypatch, responses, max_retries=3)

    with pytest.raises(LLMProviderError):
        provider.extract_signal_vector(_RAW_INPUT)

    assert provider._test_calls["n"] == 1  # type: ignore[attr-defined]


def test_targets_the_groq_api():
    assert GROQ_API_BASE == "https://api.groq.com/openai/v1"


def test_markdown_fenced_json_is_stripped(monkeypatch):
    fenced = "```json\n" + _VALID_SIGNAL_JSON + "\n```"
    responses = [_FakeResponse(200, _chat_body(fenced))]
    provider = _provider(monkeypatch, responses, max_retries=1)

    result = provider.extract_signal_vector(_RAW_INPUT)

    assert result.data_modality == "text"


def test_generate_executive_report_parses_the_new_narrative_shape(monkeypatch):
    narrative_json = json.dumps(
        {
            "report_title": "AI Solution Blueprint: Support Copilot",
            "one_line_summary": "A copilot to speed up support replies.",
            "executive_cards": {
                "problem": "Agents are slow to respond.",
                "opportunity": "AI can draft replies for review.",
                "recommended_pattern": "Real-time copilot pattern fits best.",
                "expected_outcome": "Faster response times.",
            },
            "risks": [
                {
                    "risk": "Draft quality may vary early on.",
                    "impact": "medium",
                    "likelihood": "medium",
                    "mitigation": "Human review before send.",
                }
            ],
            "assumptions": ["Scale assumed department-wide."],
            "next_best_actions": ["Run a two-week pilot."],
        }
    )
    responses = [_FakeResponse(200, _chat_body(narrative_json))]
    provider = _provider(monkeypatch, responses, max_retries=1)

    result = provider.generate_executive_report(_engine_output())

    assert result.report_title == "AI Solution Blueprint: Support Copilot"
    assert result.executive_cards.recommended_pattern == "Real-time copilot pattern fits best."
    assert result.risks[0].impact == "medium"
    assert result.risks[0].mitigation == "Human review before send."


def test_optimize_prompt_parses_and_normalizes_response(monkeypatch):
    raw_optimization_json = json.dumps(
        {
            "optimized_text": "Automate invoice review for accounts payable.",
            "gaps": ["industry", "not_a_real_field"],
            "questions": [
                {"field": "industry", "question": "What industry is this for?"},
                {"field": "bogus_field", "question": "This should be dropped."},
            ],
            "notes": "Tightened the phrasing.",
        }
    )
    responses = [_FakeResponse(200, _chat_body(raw_optimization_json))]
    provider = _provider(monkeypatch, responses, max_retries=1)

    result = provider.optimize_prompt(_RAW_INPUT, [])

    assert result.optimized_text == "Automate invoice review for accounts payable."
    assert result.gaps == ["industry"]  # unknown field name dropped
    assert len(result.clarifying_questions) == 1
    assert result.clarifying_questions[0].field == "industry"
    assert result.original_token_estimate > 0
    assert result.optimized_token_estimate > 0
