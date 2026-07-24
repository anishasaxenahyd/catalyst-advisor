"""The entire Phase 0 API surface: one stateless recommendation route.

No persistence — each request is parsed, scored, and returned. No GET by
id, because there's nothing to fetch after the response is sent.
"""

from fastapi import APIRouter, HTTPException

from app.engine.recommend import build_report
from app.intake.diagram_text_parser import diagram_text_to_description
from app.models.schemas import RecommendationRequest, Report
from app.providers.knowledge.factory import get_knowledge_provider
from app.providers.llm.factory import get_llm_provider

router = APIRouter()


@router.post("/recommendations", response_model=Report)
def create_recommendation(request: RecommendationRequest) -> Report:
    raw_text = request.description.strip()

    if request.mode == "design_review" and request.diagram_text:
        diagram_summary = diagram_text_to_description(request.diagram_text)
        raw_text = f"{diagram_summary}\n\n{raw_text}".strip()

    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail="Describe the idea, or upload/paste a diagram, before requesting a recommendation.",
        )

    return build_report(
        mode=request.mode,
        raw_text=raw_text,
        hints=request.hints,
        llm=get_llm_provider(),
        kp=get_knowledge_provider(),
    )
