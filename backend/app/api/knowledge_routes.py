"""Additive API surface for the Enterprise Knowledge Platform foundation.

Entirely new routes under `/api/knowledge`. Does not modify `routes.py`,
which still serves the deterministic `/api/recommendations` flow exactly
as before — this file exists so the new ingestion/retrieval/pipeline
layers are actually reachable and testable, not just importable.
"""

from fastapi import APIRouter, Query

from app.enterprise_knowledge.factory import (
    get_recommendation_pipeline,
    get_retrieval_service,
    load_knowledge_base,
)
from app.enterprise_knowledge.models import KnowledgeCategory, SourceVendor
from app.enterprise_knowledge.pipeline.base import (
    KnowledgeRecommendationRequest,
    KnowledgeRecommendationResult,
)
from app.enterprise_knowledge.retrieval.base import RetrievalQuery, RetrievalResult

router = APIRouter()


@router.get("/categories")
def list_categories() -> dict[str, int]:
    """Entry counts per category — a quick way to confirm the knowledge
    base loaded, and the shape a future admin/ingestion UI would read."""
    return load_knowledge_base().counts()


@router.get("/search", response_model=list[RetrievalResult])
def search_knowledge(
    text: str | None = Query(default=None),
    category: KnowledgeCategory | None = Query(default=None),
    vendor: SourceVendor | None = Query(default=None),
    tags: list[str] = Query(default=[]),
    limit: int = Query(default=20, le=100),
) -> list[RetrievalResult]:
    query = RetrievalQuery(text=text, category=category, vendor=vendor, tags=tags, limit=limit)
    return get_retrieval_service().search(query)


@router.post("/recommend", response_model=KnowledgeRecommendationResult)
def recommend(request: KnowledgeRecommendationRequest) -> KnowledgeRecommendationResult:
    """Placeholder — returns a clearly-labeled not-yet-implemented result.
    See `app.enterprise_knowledge.pipeline` for the real extension point.
    Does not touch, and is not touched by, `/api/recommendations`."""
    return get_recommendation_pipeline().recommend(request)
