"""Uniform failure signal for the LLM provider layer.

Every vendor implementation normalizes its own failure modes — httpx
errors, non-2xx responses, malformed JSON, schema validation failures —
into `LLMProviderError` before letting them escape. Callers one layer up
(`FallbackLLMProvider`, `factory.py`) only ever need to handle one
exception type regardless of which vendor is active.
"""


class LLMProviderError(Exception):
    """Raised by an LLMProvider implementation when it could not fulfill a
    request, after exhausting its own retry policy (if any)."""
