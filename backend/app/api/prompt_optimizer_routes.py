"""Prompt optimizer route — pre-submission, advisory only.

Stateless like the rest of the Phase 0 API surface: the frontend carries
`prior_answers` itself across calls, nothing is persisted server-side. This
never touches the deterministic engine or scoring — it only helps the user
supply a better `description` before they hit `/api/recommendations`.
"""

from fastapi import APIRouter, HTTPException

from app.intake.diagram_text_parser import diagram_text_to_description
from app.models.schemas import PromptOptimizationRequest, PromptOptimizationResult, RawInput
from app.providers.llm.factory import get_llm_provider

router = APIRouter()


@router.post("/prompt-optimizer", response_model=PromptOptimizationResult)
def optimize_prompt(request: PromptOptimizationRequest) -> PromptOptimizationResult:
    raw_text = request.description.strip()

    if request.mode == "design_review" and request.diagram_text:
        diagram_summary = diagram_text_to_description(request.diagram_text)
        raw_text = f"{diagram_summary}\n\n{raw_text}".strip()

    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail="Describe the idea, or upload/paste a diagram, before requesting a prompt optimization.",
        )

    raw_input = RawInput(mode=request.mode, text=raw_text, hints=request.hints)
    return get_llm_provider().optimize_prompt(raw_input, request.prior_answers)
