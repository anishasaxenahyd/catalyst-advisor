"""Groq implementation of LLMProvider — the only production vendor provider
in this POC (api.groq.com; not to be confused with Grok / x.ai, which was
tried and removed — see the POC Cleanup notes). `MockLLMProvider` is the
fallback when Groq is unavailable, wired up by `factory.py` via
`FallbackLLMProvider`.

Failure handling:
  1. Network errors (timeout, connection failure) and HTTP 429/5xx are
     treated as transient and retried with exponential backoff.
  2. A response that isn't valid JSON at all is also retried — asking again
     sometimes yields well-formed output from a probabilistic model. A
     response that IS valid JSON but has a bad enum value, casing issue, or
     unrecognized tag is NOT retried — it goes to the Validation layer
     (`app.validation.signal_normalizer`) instead, which corrects or
     defaults what it can rather than burning a retry on fixable input.
  3. Any other HTTP error (400 bad request, 401/403 auth, 404) is
     non-retryable and raised immediately.

Every exit path raises `LLMProviderError` so the caller (FallbackLLMProvider)
doesn't need to know anything about Groq's specific failure shapes.
"""

import json
import logging
import os

import httpx
from pydantic import ValidationError

from app.models.schemas import (
    BusinessUnderstanding,
    EngineOutput,
    ExecutiveNarrative,
    PromptOptimizationResult,
    QAExchange,
    RawExtractedSignal,
    RawInput,
    RawPromptOptimization,
    SignalVector,
)
from app.providers.llm.base import LLMProvider
from app.providers.llm.exceptions import LLMProviderError
from app.providers.llm.prompts import NARRATIVE_PROMPT, PROMPT_OPTIMIZER_PROMPT, SIGNAL_VECTOR_PROMPT
from app.providers.llm.retry import RetryConfig, call_with_retries
from app.providers.llm.utils import strip_json_fences
from app.validation.prompt_optimization_normalizer import format_tracked_fields, normalize_optimization
from app.validation.signal_normalizer import normalize_signal

logger = logging.getLogger("catalyst.llm.groq")

GROQ_API_BASE = "https://api.groq.com/openai/v1"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class _TransientGroqError(Exception):
    """Internal only — signals `call_with_retries` that this attempt is
    worth retrying. Never escapes `GroqProvider`."""


class GroqProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
    ):
        self.api_key = api_key or os.environ["GROQ_API_KEY"]
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.timeout_seconds = timeout_seconds or float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))
        retries = max_retries if max_retries is not None else int(os.getenv("GROQ_MAX_RETRIES", "2"))
        self._retry_config = RetryConfig(max_attempts=retries + 1)

    # ---- transport ----

    def _post(self, prompt: str) -> str:
        """One HTTP attempt. Raises `_TransientGroqError` for anything
        worth retrying, `LLMProviderError` for anything that isn't."""
        headers = {"Authorization": f"Bearer {self.api_key}", "content-type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{GROQ_API_BASE}/chat/completions", headers=headers, json=payload)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as exc:
            raise _TransientGroqError(f"network error calling Groq: {exc}") from exc

        if response.status_code in _RETRYABLE_STATUS_CODES:
            raise _TransientGroqError(
                f"Groq returned retryable status {response.status_code}: {response.text[:300]}"
            )
        if response.status_code >= 400:
            raise LLMProviderError(
                f"Groq returned non-retryable status {response.status_code}: {response.text[:300]}"
            )

        try:
            data = response.json()
            return strip_json_fences(data["choices"][0]["message"]["content"])
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise _TransientGroqError(f"unexpected Groq response shape: {exc}") from exc

    # ---- LLMProvider ----

    def extract_signal_vector(self, raw_input: RawInput) -> SignalVector:
        prompt = SIGNAL_VECTOR_PROMPT.format(
            text=raw_input.text,
            hints=raw_input.hints.model_dump_json(),
            known_tags=", ".join(raw_input.known_tags),
        )

        def attempt() -> SignalVector:
            raw = self._post(prompt)
            try:
                extracted = RawExtractedSignal.model_validate_json(raw)
            except (ValidationError, json.JSONDecodeError) as exc:
                raise _TransientGroqError(f"Groq returned an unparseable signal vector: {exc}") from exc
            return normalize_signal(extracted, hints=raw_input.hints, known_tags=raw_input.known_tags)

        try:
            return call_with_retries(
                attempt,
                retryable=(_TransientGroqError,),
                config=self._retry_config,
                op_name="groq.extract_signal_vector",
            )
        except _TransientGroqError as exc:
            raise LLMProviderError(f"Groq unavailable after retries (extract_signal_vector): {exc}") from exc

    def generate_executive_report(self, engine_output: EngineOutput) -> ExecutiveNarrative:
        prompt = NARRATIVE_PROMPT.format(
            business_context=_format_business_context(engine_output.business_understanding),
            engine_output=engine_output.model_dump_json(indent=2),
        )

        def attempt() -> ExecutiveNarrative:
            raw = self._post(prompt)
            try:
                return ExecutiveNarrative.model_validate_json(raw)
            except (ValidationError, json.JSONDecodeError) as exc:
                raise _TransientGroqError(f"Groq returned an invalid executive narrative: {exc}") from exc

        try:
            return call_with_retries(
                attempt,
                retryable=(_TransientGroqError,),
                config=self._retry_config,
                op_name="groq.generate_executive_report",
            )
        except _TransientGroqError as exc:
            raise LLMProviderError(f"Groq unavailable after retries (generate_executive_report): {exc}") from exc

    def optimize_prompt(self, raw_input: RawInput, prior_answers: list[QAExchange]) -> PromptOptimizationResult:
        prompt = PROMPT_OPTIMIZER_PROMPT.format(
            text=raw_input.text,
            hints=raw_input.hints.model_dump_json(),
            tracked_fields=format_tracked_fields(),
            prior_answers=_format_prior_answers(prior_answers),
        )

        def attempt() -> PromptOptimizationResult:
            raw = self._post(prompt)
            try:
                extracted = RawPromptOptimization.model_validate_json(raw)
            except (ValidationError, json.JSONDecodeError) as exc:
                raise _TransientGroqError(f"Groq returned an unparseable prompt optimization: {exc}") from exc
            return normalize_optimization(extracted, original_text=raw_input.text)

        try:
            return call_with_retries(
                attempt,
                retryable=(_TransientGroqError,),
                config=self._retry_config,
                op_name="groq.optimize_prompt",
            )
        except _TransientGroqError as exc:
            raise LLMProviderError(f"Groq unavailable after retries (optimize_prompt): {exc}") from exc


def _format_prior_answers(prior_answers: list[QAExchange]) -> str:
    if not prior_answers:
        return "(none)"
    return "\n".join(f"- Q: {qa.question}\n  A: {qa.answer}" for qa in prior_answers)


def _format_business_context(business_understanding: BusinessUnderstanding) -> str:
    signals = ", ".join(business_understanding.key_signals) or "(none)"
    return f"{business_understanding.problem_narrative}\nKey signals: {signals}"
