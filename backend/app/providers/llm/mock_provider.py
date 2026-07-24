"""Deterministic stand-in for a real LLM, active by default in Phase 0 and
still the fallback target in every phase since.

`MockLLMProvider` implements the same `LLMProvider` interface a real vendor
provider fills in: keyword heuristics instead of a language model for
extraction, string templates instead of generated prose for narration. Its
extraction still routes through `app.validation.signal_normalizer`, same as
every real provider — so it's a faithful stand-in, not a special case, and
still exercises the same provenance/warning machinery.
"""

import re

from app.models.schemas import (
    EngineOutput,
    ExecutiveNarrative,
    RawExtractedSignal,
    RawInput,
    SignalVector,
)
from app.providers.llm.base import LLMProvider
from app.validation.signal_normalizer import normalize_signal

_KEYWORD_TAGS: dict[str, list[str]] = {
    "document": ["document-heavy"], "contract": ["document-heavy"], "invoice": ["document-heavy"],
    "pdf": ["document-heavy"], "scan": ["document-heavy"],
    "real-time": ["realtime", "low-latency"], "real time": ["realtime", "low-latency"],
    "realtime": ["realtime", "low-latency"], "live": ["realtime"], "instant": ["realtime", "low-latency"],
    "agent": ["agentic"], "autonomous": ["agentic", "autonomous"], "automatically": ["agentic"],
    "workflow": ["workflow"], "approval": ["workflow"], "process": ["workflow"],
    "salesforce": ["integration-heavy"], "sharepoint": ["integration-heavy"],
    "snowflake": ["integration-heavy"], "integrate": ["integration-heavy"], "integration": ["integration-heavy"],
    "copilot": ["copilot", "assist"], "assist": ["assist"], "suggest": ["copilot", "assist"],
    "draft": ["copilot", "assist"],
    "batch": ["batch"], "nightly": ["batch"], "overnight": ["batch"], "scheduled": ["batch"],
    "classify": ["classification"], "classification": ["classification"], "categorize": ["classification"],
    "route": ["classification"], "routing": ["classification"], "triage": ["classification"],
    "high volume": ["high-scale"], "millions": ["high-scale"], "thousands": ["high-scale"], "scale": ["high-scale"],
    "image": ["image", "multimodal"], "photo": ["image", "multimodal"], "diagram": ["image", "multimodal"],
    "screenshot": ["image", "multimodal"],
    "embedding": ["embeddings", "retrieval"], "semantic search": ["embeddings", "retrieval"],
    "retrieve": ["retrieval"], "retrieval": ["retrieval"], "search": ["retrieval"],
    "moderate": ["moderation", "safety"], "moderation": ["moderation", "safety"], "toxic": ["moderation", "safety"],
    "reason": ["reasoning"], "multi-step": ["reasoning", "multi-step"], "plan": ["reasoning", "multi-step"],
    "database": ["structured"], "sql": ["structured"], "records": ["structured"], "rows": ["structured"],
}

_SYSTEM_KEYWORDS = ["salesforce", "sharepoint", "snowflake", "workday", "sap", "servicenow"]


def _tags_from_text(text: str) -> list[str]:
    lowered = text.lower()
    tags: set[str] = set()
    for keyword, mapped in _KEYWORD_TAGS.items():
        if keyword in lowered:
            tags.update(mapped)
    return sorted(tags)


def _guess_data_modality(text: str, tags: list[str]) -> str:
    if "image" in tags:
        return "image"
    if "structured" in tags:
        return "structured"
    return "text"


def _guess_latency(text: str, tags: list[str]) -> str:
    if "realtime" in tags:
        return "realtime"
    if "batch" in tags:
        return "batch"
    return "near_realtime"


def _guess_automation_level(text: str) -> str:
    lowered = text.lower()
    if "autonomous" in lowered or "without human" in lowered or "no human" in lowered:
        return "autonomous"
    if "copilot" in lowered or "suggest" in lowered or "review before" in lowered:
        return "copilot"
    return "assist"


def _use_case_summary(text: str) -> str:
    first_sentence = re.split(r"(?<=[.!?])\s", text.strip())[0] if text.strip() else "Unspecified use case"
    return first_sentence[:120]


class MockLLMProvider(LLMProvider):
    def extract_signal_vector(self, raw_input: RawInput) -> SignalVector:
        tags = _tags_from_text(raw_input.text)
        integration_points = [s for s in _SYSTEM_KEYWORDS if s in raw_input.text.lower()]

        # Mock never guesses industry, data_sensitivity, or expected_scale
        # from text (left None) — those come from the user's hints or the
        # Validation layer's default, same as every other provider. Casing/
        # whitespace normalization, tag-vocabulary filtering, and dedup all
        # happen in normalize_signal() now too, not here.
        extracted = RawExtractedSignal(
            use_case_type=_use_case_summary(raw_input.text),
            industry=None,
            data_sensitivity=None,
            data_modality=_guess_data_modality(raw_input.text, tags),
            latency_requirement=_guess_latency(raw_input.text, tags),
            expected_scale=None,
            automation_level=_guess_automation_level(raw_input.text),
            integration_points=integration_points,
            tags=tags,
        )
        return normalize_signal(extracted, hints=raw_input.hints, known_tags=raw_input.known_tags)

    def generate_executive_report(self, engine_output: EngineOutput) -> ExecutiveNarrative:
        sv = engine_output.signal_vector
        pattern = engine_output.architecture_recommendation.pattern
        model = engine_output.model_recommendation.primary
        workbench = engine_output.workbench_recommendation
        confidence = engine_output.confidence_scores.overall

        summary = (
            f"For this {sv.use_case_type.lower()} use case, the deterministic engine recommends the "
            f"\"{pattern.name}\" architecture pattern paired with {model.name} as the primary model, "
            f"deployed on a {workbench.workspace_tier.name} workspace under the {workbench.security_profile.name} "
            f"security profile. Overall confidence in this recommendation is {confidence}%, based on "
            f"{'a fully' if confidence >= 75 else 'a partially'} specified signal vector."
        )

        risks = [
            f"Signal vector was inferred with default assumptions where the input did not specify "
            f"a value (see Decision Trace assumptions).",
            f"Enterprise reuse is estimated from Catalog metadata, not a live audit of build-vs-buy cost.",
        ]
        if sv.data_sensitivity != "none":
            risks.append(
                f"Data sensitivity was reported as '{sv.data_sensitivity}' — confirm the selected "
                f"security profile with governance before proceeding past a pilot."
            )

        assumptions = [
            f"Expected scale assumed: {sv.expected_scale}.",
            f"Automation level assumed: {sv.automation_level}.",
        ]

        next_best_actions = [
            "Validate the signal vector fields above with the requesting team.",
            f"Review the {pattern.name} pattern's Decision Trace for the specific alternatives it beat.",
            "Confirm data sensitivity classification with governance before selecting a Workbench security profile.",
        ]

        return ExecutiveNarrative(
            executive_summary=summary,
            risks=risks,
            assumptions=assumptions,
            next_best_actions=next_best_actions,
        )
