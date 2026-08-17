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

from app.kernel.schemas import AlternativeNarrative, KernelNarrationInput, KernelNarrativeExtras
from app.models.schemas import (
    ClarifyingQuestion,
    EngineOutput,
    ExecutiveCards,
    ExecutiveNarrative,
    PromptOptimizationResult,
    QAExchange,
    RawExtractedSignal,
    RawInput,
    RiskItem,
    SignalVector,
)
from app.providers.llm.base import LLMProvider
from app.providers.llm.token_utils import estimate_tokens
from app.validation.prompt_optimization_normalizer import MAX_CLARIFYING_QUESTIONS
from app.validation.signal_normalizer import normalize_signal

_KEYWORD_TAGS: dict[str, list[str]] = {
    "document": ["document-heavy"], "contract": ["document-heavy"], "invoice": ["document-heavy"],
    "pdf": ["document-heavy"], "scan": ["document-heavy"],
    "enterprise data": ["document-heavy"], "private data": ["document-heavy"], "internal data": ["document-heavy"],
    "company data": ["document-heavy"], "knowledge base": ["document-heavy", "retrieval"],
    "citation": ["retrieval"], "citations": ["retrieval"], "cite": ["retrieval"], "cited": ["retrieval"],
    "grounded": ["retrieval"], "source document": ["retrieval"],
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

_SENSITIVITY_KEYWORDS = [
    "pii", "phi", "personal data", "personally identifiable", "patient", "medical", "health record",
    "ssn", "social security", "financial record", "credit card", "hipaa", "gdpr",
]

_CANNED_QUESTIONS: dict[str, str] = {
    "data_sensitivity": "Does this involve PII or PHI data (e.g. customer, patient, or financial records)?",
    "industry": "What industry or business domain is this for?",
    "expected_scale": "Is this a pilot, a department-wide rollout, or an enterprise-wide rollout?",
    "automation_level": "Should it just assist a human, draft for review (copilot), or act on its own (autonomous)?",
    "data_modality": "What's the primary data type involved — text, images, or structured/tabular data?",
    "latency_requirement": "Does this need to respond in real time, or can it run in scheduled batches?",
}


def _has_sensitivity_signal(lowered: str) -> bool:
    return any(keyword in lowered for keyword in _SENSITIVITY_KEYWORDS)


def _has_explicit_automation_signal(lowered: str) -> bool:
    explicit_keywords = ("autonomous", "without human", "no human", "copilot", "suggest", "review before")
    return any(keyword in lowered for keyword in explicit_keywords)


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


_DOMAIN_PHRASE_PATTERNS = [
    re.compile(r"\banswers?\s+(.+?)\s+questions?\b", re.IGNORECASE),
    re.compile(r"\bquestions?\s+about\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\bhelps?\s+(?:with\s+)?(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\bautomat(?:es?|ing)\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\bmanages?\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\breviews?\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\bprocess(?:es|ing)?\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\btriag(?:e|es|ing)\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
    re.compile(r"\bclassif(?:y|ies|ying)\s+(.+?)(?:[,.;]|$)", re.IGNORECASE),
]
_LEADING_BOILERPLATE = re.compile(
    r"^(?:build|create|develop|design|make|i want to build|we need|we want)\s+"
    r"(?:an?\s+)?(?:ai\s+)?(?:assistant|agent|tool|system|solution|pipeline|bot|copilot)?\s*"
    r"(?:that|to|which)?\s*",
    re.IGNORECASE,
)
_STOPWORDS = {"a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "with", "using"}


def _smart_title_case(phrase: str) -> str:
    words = phrase.split()
    out = []
    for i, w in enumerate(words):
        if w.isupper() and len(w) <= 5:  # preserve acronyms: PHI, PII, CRM, KYC
            out.append(w)
        elif i > 0 and w.lower() in _STOPWORDS:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def _domain_phrase(text: str, *, max_words: int = 6) -> str:
    """A short, non-restated noun phrase naming what the request is about —
    used for the report title and summary instead of echoing the raw input
    sentence back at the reader."""
    stripped = text.strip()
    for pattern in _DOMAIN_PHRASE_PATTERNS:
        match = pattern.search(stripped)
        if match:
            candidate = match.group(1).strip()
            words = candidate.split()[:max_words]
            if words:
                return _smart_title_case(" ".join(words))

    first_clause = re.split(r"[,.;]", stripped)[0] if stripped else "This use case"
    without_boilerplate = _LEADING_BOILERPLATE.sub("", first_clause).strip()
    words = (without_boilerplate or first_clause).split()[:max_words]
    return _smart_title_case(" ".join(words)) if words else "This use case"


_SHAPE_NOUN_BY_PATTERN_ID = {
    "pattern-batch-classification": "Pipeline",
    "pattern-agentic-hitl": "Workflow Assistant",
    "pattern-autonomous-multi-agent": "Automation",
    "pattern-realtime-copilot": "Copilot",
    "pattern-fine-tuning-knowledge-injection": "Assistant",
}


def _solution_shape_noun(pattern_id: str) -> str:
    return _SHAPE_NOUN_BY_PATTERN_ID.get(pattern_id, "Assistant")


def _use_case_summary(text: str) -> str:
    """Kept short and generic — feeds SignalVector.use_case_type, which
    reads into several downstream sentences ("The stated need is a {this}
    capability..."), so it stays a plain phrase rather than a full title."""
    return _domain_phrase(text)


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
        confidence = engine_output.confidence_scores.overall
        domain_phrase = sv.use_case_type or "This Use Case"

        report_title = f"{domain_phrase} {_solution_shape_noun(pattern.id)}"
        one_line_summary = (
            f"Recommended approach: {pattern.name}, powered by {model.name}, built to support {domain_phrase.lower()}."
        )

        executive_cards = ExecutiveCards(
            problem=engine_output.business_understanding.problem_narrative,
            opportunity=(
                f"An AI {sv.automation_level} solution fits well here — the request was "
                f"{'fully' if confidence >= 75 else 'partially'} specified, giving {confidence}% overall confidence."
            ),
            recommended_pattern=(
                f'The "{pattern.name}" pattern is recommended. {engine_output.architecture_recommendation.rationale}'
            ),
            expected_outcome=(
                f"Deploying {model.name} under this pattern is expected to deliver "
                f"{engine_output.feasibility.business}% business feasibility with "
                f"{engine_output.feasibility.technical}% technical feasibility."
            ),
        )

        risks = [
            RiskItem(
                risk="Some requirements weren't stated explicitly and were filled in with reasonable defaults.",
                impact="medium",
                likelihood="medium",
                mitigation="Confirm the assumed details with the requesting team before finalizing scope.",
            ),
            RiskItem(
                risk="Reuse recommendations are based on catalog metadata, not a live audit of build-vs-buy cost.",
                impact="low",
                likelihood="medium",
                mitigation="Confirm actual reuse feasibility with the owning team before committing effort estimates.",
            ),
        ]
        if sv.data_sensitivity != "none":
            risks.append(
                RiskItem(
                    risk=f"Data sensitivity was reported as '{sv.data_sensitivity}'.",
                    impact="high" if sv.data_sensitivity == "phi" else "medium",
                    likelihood="medium",
                    mitigation="Confirm the selected security profile with governance before proceeding past a pilot.",
                )
            )

        assumptions = [
            f"Expected scale assumed: {sv.expected_scale}.",
            f"Automation level assumed: {sv.automation_level}.",
        ]

        next_best_actions = [
            "Validate the assumed details above with the requesting team.",
            f"Review 'How this was decided' for why {pattern.name} was chosen over the alternatives.",
            "Confirm data sensitivity classification with governance before selecting a security profile.",
        ]

        return ExecutiveNarrative(
            report_title=report_title,
            one_line_summary=one_line_summary,
            executive_cards=executive_cards,
            risks=risks,
            assumptions=assumptions,
            next_best_actions=next_best_actions,
        )

    def optimize_prompt(self, raw_input: RawInput, prior_answers: list[QAExchange]) -> PromptOptimizationResult:
        original_text = raw_input.text
        hints = raw_input.hints
        lowered = original_text.lower()
        tags = _tags_from_text(original_text)
        answered_fields = {qa.field for qa in prior_answers if qa.answer.strip()}

        gaps: list[str] = []
        if (
            hints.data_sensitivity is None
            and "data_sensitivity" not in answered_fields
            and not _has_sensitivity_signal(lowered)
        ):
            gaps.append("data_sensitivity")
        if hints.industry is None and "industry" not in answered_fields:
            gaps.append("industry")
        if hints.expected_scale is None and "expected_scale" not in answered_fields:
            gaps.append("expected_scale")
        if (
            hints.automation_level is None
            and "automation_level" not in answered_fields
            and not _has_explicit_automation_signal(lowered)
        ):
            gaps.append("automation_level")
        if "data_modality" not in answered_fields and "image" not in tags and "structured" not in tags:
            gaps.append("data_modality")
        if "latency_requirement" not in answered_fields and "realtime" not in tags and "batch" not in tags:
            gaps.append("latency_requirement")

        questions = [
            ClarifyingQuestion(field=field, question=_CANNED_QUESTIONS[field])
            for field in gaps[:MAX_CLARIFYING_QUESTIONS]
        ]

        optimized_text = " ".join(original_text.split())
        answer_clauses = "; ".join(
            f"{qa.field.replace('_', ' ')}: {qa.answer.strip()}" for qa in prior_answers if qa.answer.strip()
        )
        if answer_clauses:
            optimized_text = f"{optimized_text} Additional context — {answer_clauses}."

        return PromptOptimizationResult(
            optimized_text=optimized_text,
            original_token_estimate=estimate_tokens(original_text),
            optimized_token_estimate=estimate_tokens(optimized_text),
            gaps=gaps,
            clarifying_questions=questions,
            notes="Whitespace collapsed" + (" and prior answers folded in." if answer_clauses else "."),
        )

    def narrate_kernel_findings(self, narration_input: KernelNarrationInput) -> KernelNarrativeExtras:
        rejected = [v for v in narration_input.pattern_verdicts if v.verdict in ("UNNECESSARY", "CONTRA_INDICATED")]
        rejected_narrative = (
            "; ".join(f"{v.pattern_name} ({v.verdict.replace('_', ' ').lower()}) — {v.reason}" for v in rejected)
            or "No patterns in the library were ruled out for this problem."
        )

        sourcing_narrative = "; ".join(
            f"{sd.capability_name}: {sd.decision}" + (f" via {sd.asset_ref}" if sd.asset_ref else "")
            for sd in narration_input.sourcing_decisions
        ) or "No capability requirements to source."

        alternatives_narrative = [
            AlternativeNarrative(
                candidate_id=alt.candidate_id,
                narrative=f"{alt.label}: {alt.governing_priority} You give up: {alt.what_is_given_up} Revisit if: {alt.revisit_trigger}",
            )
            for alt in narration_input.alternatives
        ]

        eliminated = [f"{e.candidate_label} — eliminated ({e.rule_id}): {e.evidence}" for e in narration_input.elimination_record]

        return KernelNarrativeExtras(
            rejected_options_narrative=rejected_narrative,
            sourcing_narrative=sourcing_narrative,
            alternatives_narrative=alternatives_narrative,
            counterfactuals=eliminated[:2],
        )
