"""Builds the active LLMProvider for the running process.

Groq is the only production vendor provider in this POC; MockLLMProvider is
the fallback when it's unavailable. Two distinct "Groq isn't available"
cases are handled differently:

  * Not configured (no GROQ_API_KEY) — this is a boot-time condition, not a
    transient failure. We log a warning once and hand back MockLLMProvider
    directly; there's nothing to retry.
  * Configured but failing at request time (timeout, outage, bad output) —
    handled per-request by FallbackLLMProvider, via GroqProvider's own
    retry policy first.

Set LLM_PROVIDER=mock to force the deterministic mock (e.g. CI, or local
dev without a key). See `.env.example`.
"""

import logging
import os
from functools import lru_cache

from app.providers.llm.base import LLMProvider

logger = logging.getLogger("catalyst.llm.factory")

_ALL_PROVIDER_NAMES = ("mock", "groq")


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    from app.providers.llm.mock_provider import MockLLMProvider

    provider_name = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider_name == "mock":
        return MockLLMProvider()

    if provider_name != "groq":
        raise ValueError(f"Unknown LLM_PROVIDER '{provider_name}'. Expected one of {_ALL_PROVIDER_NAMES}.")

    if not os.getenv("GROQ_API_KEY"):
        logger.warning(
            "LLM_PROVIDER=groq but GROQ_API_KEY is not set — using MockLLMProvider for this process. "
            "Set GROQ_API_KEY (see .env.example) to activate Groq."
        )
        return MockLLMProvider()

    from app.providers.llm.groq_provider import GroqProvider

    primary = GroqProvider()

    fallback_enabled = os.getenv("LLM_FALLBACK_TO_MOCK", "true").lower() != "false"
    if not fallback_enabled:
        return primary

    from app.providers.llm.fallback_provider import FallbackLLMProvider

    return FallbackLLMProvider(primary=primary, fallback=MockLLMProvider())
