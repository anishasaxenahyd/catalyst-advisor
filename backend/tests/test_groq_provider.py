import json

import httpx
import pytest

from app.models.schemas import RawInput, StructuredHints
from app.providers.llm.exceptions import LLMProviderError
from app.providers.llm.groq_provider import GROQ_API_BASE, GroqProvider

_RAW_INPUT = RawInput(mode="idea", text="a support copilot", hints=StructuredHints())

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
