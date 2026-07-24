"""Vendor-agnostic LLM interface.

`LLMProvider` exposes exactly two operations. Neither is allowed to decide a
recommendation — that stays in `engine/`, which never imports this package.

  * extract_signal_vector  — turn free text (+ any structured hints already
    picked by the user) into a SignalVector the engine can score against.
  * generate_executive_report — turn a completed EngineOutput (the engine's
    already-decided scores, patterns, models, and decision traces) into
    prose. It reads facts, it does not choose them.

Business logic (`app/engine/**`) must never import a concrete provider
class from this package — only `LLMProvider` and the factory.
"""

from abc import ABC, abstractmethod

from app.models.schemas import EngineOutput, ExecutiveNarrative, RawInput, SignalVector


class LLMProvider(ABC):
    @abstractmethod
    def extract_signal_vector(self, raw_input: RawInput) -> SignalVector: ...

    @abstractmethod
    def generate_executive_report(self, engine_output: EngineOutput) -> ExecutiveNarrative: ...
