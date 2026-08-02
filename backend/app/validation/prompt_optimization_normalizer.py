"""Validation layer for the prompt optimizer — sits between an LLMProvider's
raw `optimize_prompt` output and the `PromptOptimizationResult` the API
returns. Same philosophy as `signal_normalizer.py`: never trust an LLM's
output directly, reject-don't-guess on anything outside a known vocabulary,
and keep this module pure (no I/O, no vendor knowledge).

Token counts in particular are never taken from the LLM's own claims —
`token_utils.estimate_tokens` is the only source of truth for those, computed
locally on both the original and optimized text.
"""

from app.models.schemas import ClarifyingQuestion, PromptOptimizationResult, RawPromptOptimization
from app.providers.llm.token_utils import estimate_tokens
from app.validation.signal_normalizer import TRACKED_FIELDS

MAX_CLARIFYING_QUESTIONS = 3

# Short, human-readable descriptions of each tracked field, shared between
# the optimizer prompt (so the model knows what each field means) and the
# mock provider's canned questions.
TRACKED_FIELD_DESCRIPTIONS: dict[str, str] = {
    "data_sensitivity": "whether the data involved is none/PII/PHI",
    "data_modality": "the primary data type (text, image, structured, or mixed)",
    "latency_requirement": "how fast responses must be (batch, near-realtime, or realtime)",
    "expected_scale": "expected rollout scale (pilot, department, or enterprise)",
    "automation_level": "how autonomous the system should be (assist, copilot, or autonomous)",
    "industry": "the industry or business domain",
}


def format_tracked_fields() -> str:
    return "\n".join(f"- {field}: {desc}" for field, desc in TRACKED_FIELD_DESCRIPTIONS.items())


def normalize_optimization(raw: RawPromptOptimization, *, original_text: str) -> PromptOptimizationResult:
    optimized_text = (raw.optimized_text or "").strip() or original_text.strip()

    gaps = [field for field in dict.fromkeys(raw.gaps) if field in TRACKED_FIELD_DESCRIPTIONS]

    questions: list[ClarifyingQuestion] = []
    seen_fields: set[str] = set()
    for entry in raw.questions:
        field = str(entry.get("field", "")).strip()
        question = str(entry.get("question", "")).strip()
        if not field or not question or field not in TRACKED_FIELD_DESCRIPTIONS:
            continue
        if field in seen_fields:
            continue
        seen_fields.add(field)
        questions.append(ClarifyingQuestion(field=field, question=question))
        if len(questions) >= MAX_CLARIFYING_QUESTIONS:
            break

    return PromptOptimizationResult(
        optimized_text=optimized_text,
        original_token_estimate=estimate_tokens(original_text),
        optimized_token_estimate=estimate_tokens(optimized_text),
        gaps=gaps,
        clarifying_questions=questions,
        notes=(raw.notes or "").strip(),
    )
