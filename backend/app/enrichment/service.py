"""Builds `RecommendationEnrichment` — the deterministic bridge between the
existing recommendation engine's output and every additive knowledge source:
the AI Catalog, the Solution Registry, the Enterprise Knowledge Platform,
and the engine's own config-driven rules (`decision_rules.json`).

No LLM call, no new scoring dimensions — every match here is a plain tag,
id, or config lookup, in keeping with `app/engine/`'s existing determinism.
This module also owns the report's "architect narrative" sections (business
understanding, security, governance, roadmap, evidence/confidence summary),
each built by its own single-purpose function in this package.
"""

from app.ai_catalog.factory import load_ai_catalog
from app.ai_catalog.models import CatalogAsset
from app.enrichment.business import build_business_understanding
from app.enrichment.evidence import build_evidence_confidence_summary
from app.enrichment.governance import build_governance_recommendations
from app.enrichment.roadmap import build_implementation_roadmap
from app.enrichment.security import build_security_summary
from app.enterprise_knowledge.factory import get_retrieval_service
from app.enterprise_knowledge.retrieval.base import RetrievalQuery
from app.models.schemas import (
    AIModel,
    ArchitecturePattern,
    BestPracticeReference,
    ConfidenceScores,
    RecommendationEnrichment,
    ReusableCatalogAsset,
    SignalVector,
    SimilarSolution,
    WorkbenchRecommendation,
)
from app.solution_registry.factory import load_solution_registry
from app.solution_registry.models import SolutionRecord

_MAX_REUSABLE_ASSETS = 5
_MAX_SIMILAR_SOLUTIONS = 3
_MAX_BEST_PRACTICES = 5


def _reusable_assets(signal_vector: SignalVector, pattern: ArchitecturePattern) -> list[ReusableCatalogAsset]:
    wanted = {t.lower() for t in [*signal_vector.tags, *pattern.suitable_for_tags]}
    scored: list[tuple[CatalogAsset, set[str]]] = []
    for asset in load_ai_catalog():
        overlap = wanted & {t.lower() for t in asset.tags}
        if overlap:
            scored.append((asset, overlap))
    scored.sort(key=lambda pair: (len(pair[1]), pair[0].reuse_count), reverse=True)
    return [
        ReusableCatalogAsset(
            id=asset.id,
            name=asset.name,
            asset_type=asset.asset_type,
            description=asset.description,
            rationale=f"Shares tags {sorted(overlap)} with this use case; reused in {asset.reuse_count} prior implementation(s).",
        )
        for asset, overlap in scored[:_MAX_REUSABLE_ASSETS]
    ]


def _similar_solutions(signal_vector: SignalVector, pattern: ArchitecturePattern) -> list[SimilarSolution]:
    same_pattern = [s for s in load_solution_registry() if s.architecture_pattern_id == pattern.id]

    def _sort_key(solution: SolutionRecord) -> tuple[int, int]:
        industry_match = int(solution.industry.lower() == signal_vector.industry.lower())
        tag_overlap = len({t.lower() for t in solution.tags} & {t.lower() for t in signal_vector.tags})
        return (industry_match, tag_overlap)

    same_pattern.sort(key=_sort_key, reverse=True)
    results = []
    for solution in same_pattern[:_MAX_SIMILAR_SOLUTIONS]:
        industry_note = (
            f"same industry ({solution.industry})"
            if solution.industry.lower() == signal_vector.industry.lower()
            else f"same architecture pattern, industry: {solution.industry}"
        )
        results.append(
            SimilarSolution(
                id=solution.id,
                title=solution.title,
                industry=solution.industry,
                architecture_pattern_name=solution.architecture_pattern_name,
                business_outcome=solution.business_outcome,
                lessons_learned=solution.lessons_learned,
                security_considerations=solution.security_considerations,
                rationale=f"Matched on {industry_note}.",
            )
        )
    return results


def _best_practices(signal_vector: SignalVector, pattern: ArchitecturePattern, primary_model: AIModel) -> list[BestPracticeReference]:
    query_tags = list({*signal_vector.tags, *pattern.suitable_for_tags})
    results = get_retrieval_service().search(RetrievalQuery(tags=query_tags, limit=_MAX_BEST_PRACTICES))
    return [
        BestPracticeReference(
            id=result.entry.id,
            title=result.entry.name,
            vendor=result.entry.source.vendor,
            category=result.entry.category,
            summary=result.entry.summary,
            reference=result.entry.source.reference,
        )
        for result in results
    ]


def build_enrichment(
    signal_vector: SignalVector,
    raw_text: str,
    pattern: ArchitecturePattern,
    primary_model: AIModel,
    workbench_recommendation: WorkbenchRecommendation,
    timeline_estimate: str,
    confidence_scores: ConfidenceScores,
    confidence_rationale: str,
    missing_information: list[str],
    validation_warnings: list[str],
    rules: dict,
) -> RecommendationEnrichment:
    reusable_assets = _reusable_assets(signal_vector, pattern)
    similar_solutions = _similar_solutions(signal_vector, pattern)
    best_practices = _best_practices(signal_vector, pattern, primary_model)

    return RecommendationEnrichment(
        business_understanding=build_business_understanding(signal_vector, raw_text),
        reusable_assets=reusable_assets,
        similar_solutions=similar_solutions,
        best_practices=best_practices,
        security_summary=build_security_summary(signal_vector, pattern, workbench_recommendation, similar_solutions),
        governance_recommendations=build_governance_recommendations(signal_vector, pattern, rules),
        implementation_roadmap=build_implementation_roadmap(pattern, timeline_estimate, rules),
        evidence_confidence_summary=build_evidence_confidence_summary(
            confidence_scores,
            confidence_rationale,
            missing_information,
            validation_warnings,
            best_practices,
            similar_solutions,
            reusable_assets,
        ),
    )
