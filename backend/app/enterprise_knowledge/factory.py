"""Wires the ingestion layer to the retrieval service and pipeline for the
running process — the only place that knows the seed data is JSON files
on disk. Everything downstream (routes, a future pipeline implementation)
depends on `RetrievalService`/`RecommendationPipeline` interfaces, not on
`data/enterprise_knowledge/*.json` directly. Mirrors the existing
`app.providers.knowledge.factory` / `app.providers.llm.factory` pattern.
"""

from functools import lru_cache
from pathlib import Path

from app.enterprise_knowledge.ingestion.file_loaders import JsonKnowledgeLoader
from app.enterprise_knowledge.models import (
    AICatalogComponentEntry,
    AIModelEntry,
    ArchitecturePatternEntry,
    CloudServiceEntry,
    GovernanceRuleEntry,
    KnowledgeBase,
    ReferenceArchitectureEntry,
    SecurityControlEntry,
)
from app.enterprise_knowledge.pipeline.base import NotImplementedRecommendationPipeline, RecommendationPipeline
from app.enterprise_knowledge.retrieval.base import RetrievalService
from app.enterprise_knowledge.retrieval.in_memory import InMemoryKeywordRetrievalService

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "enterprise_knowledge"


@lru_cache(maxsize=1)
def load_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(
        architecture_patterns=JsonKnowledgeLoader(
            DATA_DIR / "architecture_patterns.json", ArchitecturePatternEntry
        ).load(),
        ai_models=JsonKnowledgeLoader(DATA_DIR / "ai_models.json", AIModelEntry).load(),
        security_controls=JsonKnowledgeLoader(DATA_DIR / "security_controls.json", SecurityControlEntry).load(),
        governance_rules=JsonKnowledgeLoader(DATA_DIR / "governance_rules.json", GovernanceRuleEntry).load(),
        cloud_services=JsonKnowledgeLoader(DATA_DIR / "cloud_services.json", CloudServiceEntry).load(),
        ai_catalog_components=JsonKnowledgeLoader(
            DATA_DIR / "ai_catalog_components.json", AICatalogComponentEntry
        ).load(),
        reference_architectures=JsonKnowledgeLoader(
            DATA_DIR / "reference_architectures.json", ReferenceArchitectureEntry
        ).load(),
    )


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    return InMemoryKeywordRetrievalService(load_knowledge_base().all_entries())


@lru_cache(maxsize=1)
def get_recommendation_pipeline() -> RecommendationPipeline:
    return NotImplementedRecommendationPipeline()
