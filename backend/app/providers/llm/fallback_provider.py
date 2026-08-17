"""Wraps any two LLMProvider implementations so a failure of the first
degrades to the second, per call, rather than failing the request.

Generic on purpose. `factory.py` uses it as
`FallbackLLMProvider(primary=GroqProvider(), fallback=MockLLMProvider())`,
but it would work identically pairing any two LLMProvider implementations.
"""

import logging

from app.kernel.schemas import KernelNarrationInput, KernelNarrativeExtras
from app.models.schemas import (
    EngineOutput,
    ExecutiveNarrative,
    PromptOptimizationResult,
    QAExchange,
    RawInput,
    SignalVector,
)
from app.providers.llm.base import LLMProvider

logger = logging.getLogger("catalyst.llm.fallback")


class FallbackLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    def extract_signal_vector(self, raw_input: RawInput) -> SignalVector:
        try:
            return self.primary.extract_signal_vector(raw_input)
        except Exception as exc:
            logger.warning(
                "%s.extract_signal_vector failed (%s: %s) — falling back to %s.",
                type(self.primary).__name__, type(exc).__name__, exc, type(self.fallback).__name__,
            )
            return self.fallback.extract_signal_vector(raw_input)

    def generate_executive_report(self, engine_output: EngineOutput) -> ExecutiveNarrative:
        try:
            return self.primary.generate_executive_report(engine_output)
        except Exception as exc:
            logger.warning(
                "%s.generate_executive_report failed (%s: %s) — falling back to %s.",
                type(self.primary).__name__, type(exc).__name__, exc, type(self.fallback).__name__,
            )
            return self.fallback.generate_executive_report(engine_output)

    def optimize_prompt(self, raw_input: RawInput, prior_answers: list[QAExchange]) -> PromptOptimizationResult:
        try:
            return self.primary.optimize_prompt(raw_input, prior_answers)
        except Exception as exc:
            logger.warning(
                "%s.optimize_prompt failed (%s: %s) — falling back to %s.",
                type(self.primary).__name__, type(exc).__name__, exc, type(self.fallback).__name__,
            )
            return self.fallback.optimize_prompt(raw_input, prior_answers)

    def narrate_kernel_findings(self, narration_input: KernelNarrationInput) -> KernelNarrativeExtras:
        try:
            return self.primary.narrate_kernel_findings(narration_input)
        except Exception as exc:
            logger.warning(
                "%s.narrate_kernel_findings failed (%s: %s) — falling back to %s.",
                type(self.primary).__name__, type(exc).__name__, exc, type(self.fallback).__name__,
            )
            return self.fallback.narrate_kernel_findings(narration_input)
