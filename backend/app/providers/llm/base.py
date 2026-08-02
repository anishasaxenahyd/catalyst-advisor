"""Vendor-agnostic LLM interface.

`LLMProvider` exposes exactly three operations. None is allowed to decide a
recommendation — that stays in `engine/`, which never imports this package.

  * extract_signal_vector  — turn free text (+ any structured hints already
    picked by the user) into a SignalVector the engine can score against.
  * generate_executive_report — turn a completed EngineOutput (the engine's
    already-decided scores, patterns, models, and decision traces) into
    prose. It reads facts, it does not choose them.
  * optimize_prompt — a pre-submission, advisory-only step: rewrite the
    user's raw input into a denser prompt and flag which signal-relevant
    facts are still missing. Runs before extract_signal_vector and never
    influences scoring; it only helps the user supply better input to it.

Business logic (`app/engine/**`) must never import a concrete provider
class from this package — only `LLMProvider` and the factory.
"""

from abc import ABC, abstractmethod

from app.models.schemas import (
    EngineOutput,
    ExecutiveNarrative,
    PromptOptimizationResult,
    QAExchange,
    RawInput,
    SignalVector,
)


class LLMProvider(ABC):
    @abstractmethod
    def extract_signal_vector(self, raw_input: RawInput) -> SignalVector: ...

    @abstractmethod
    def generate_executive_report(self, engine_output: EngineOutput) -> ExecutiveNarrative: ...

    @abstractmethod
    def optimize_prompt(
        self, raw_input: RawInput, prior_answers: list[QAExchange]
    ) -> PromptOptimizationResult: ...
