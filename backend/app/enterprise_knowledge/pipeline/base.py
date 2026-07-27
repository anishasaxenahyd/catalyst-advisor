"""The extension point for the next phase: an LLM-assisted, retrieval-
augmented recommendation pipeline over the Enterprise Knowledge Platform.

This module defines the *interface* and *output shape* only, per this
phase's brief — "do not implement full reasoning yet". Nothing here is
wired into `/api/recommendations`; the existing deterministic engine
(`app/engine/recommend.py`) is untouched and keeps serving that route.

Why a separate pipeline at all, rather than extending the existing one:
the existing engine reasons over the fictional Catalyst Catalog with
fixed, hand-tuned scoring rules. This pipeline is meant to reason over a
large, heterogeneous, real-vendor knowledge base where "the right answer"
isn't a deterministic formula — it's closer to a retrieval-augmented
judgment call, which is why it's LLM-assisted and reports evidence +
confidence rather than a fixed weighted score. The two are expected to
eventually inform each other (see `factory.py` and the README extension
notes), not merge into one engine.

Implementing this for real, in the next phase, looks like: retrieve
relevant entries via `RetrievalService`, hand them to an `LLMProvider`
(reusing `app.providers.llm` — same interface, same provider-swap
guarantees already established) as grounding context, and have the model
select from and cite the retrieved entries rather than free-associate.
"""

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from app.enterprise_knowledge.models import KnowledgeCategory, SourceVendor


class Evidence(BaseModel):
    """One piece of grounding for a recommendation — always traceable back
    to a specific `KnowledgeEntry` via `entry_id`, never a free-floating
    claim. Mirrors `RetrievalResult` closely on purpose: evidence is
    expected to be retrieval results the pipeline chose to cite."""

    entry_id: str
    category: KnowledgeCategory
    title: str
    vendor: SourceVendor
    excerpt: str
    relevance_score: float | None = None


class ConfidenceScore(BaseModel):
    """Placeholder shape for confidence reporting — deliberately not a
    single opaque number. `basis` records how the score was produced so a
    caller (and a reviewer) can tell a real judgment from a stub."""

    overall: float | None = Field(default=None, description="0-100 when a basis other than 'not_yet_implemented' is used.")
    rationale: str = ""
    basis: Literal["not_yet_implemented", "heuristic", "llm_judged"] = "not_yet_implemented"


class KnowledgeRecommendationRequest(BaseModel):
    """Intentionally loose compared to the deterministic engine's
    `RawInput`/`SignalVector` — the shape this should take (a signal
    vector? raw text? both?) is a next-phase design decision, not this
    phase's."""

    raw_text: str
    hints: dict = Field(default_factory=dict)


class KnowledgeRecommendationResult(BaseModel):
    summary: str
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    architecture_pattern_ids: list[str] = Field(default_factory=list)
    ai_model_ids: list[str] = Field(default_factory=list)
    security_control_ids: list[str] = Field(default_factory=list)


class RecommendationPipeline(ABC):
    @abstractmethod
    def recommend(self, request: KnowledgeRecommendationRequest) -> KnowledgeRecommendationResult: ...


class NotImplementedRecommendationPipeline(RecommendationPipeline):
    """The default (and only) pipeline in this phase. Returns a valid,
    clearly-labeled placeholder rather than raising, so the API route and
    any future frontend wiring can be built and tested against a real
    response shape before the reasoning itself exists."""

    def recommend(self, request: KnowledgeRecommendationRequest) -> KnowledgeRecommendationResult:
        return KnowledgeRecommendationResult(
            summary="LLM-assisted recommendation reasoning is not implemented yet. This response shows the intended output shape only.",
            confidence=ConfidenceScore(
                basis="not_yet_implemented",
                rationale="RecommendationPipeline foundation only — see app.enterprise_knowledge.pipeline for the extension point.",
            ),
        )
