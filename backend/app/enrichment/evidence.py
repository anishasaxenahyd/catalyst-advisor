"""Deterministic evidence & confidence summary — a single consolidated view
over data the engine and enrichment layer already computed: per-dimension
confidence, validation warnings, missing information, and how much
supporting evidence (best practices, comparable implementations, reusable
assets) backs the recommendation. Pure aggregation, no new computation.
"""

from app.models.schemas import (
    BestPracticeReference,
    ConfidenceScores,
    EvidenceConfidenceSummary,
    ReusableCatalogAsset,
    SimilarSolution,
)


def build_evidence_confidence_summary(
    confidence_scores: ConfidenceScores,
    confidence_rationale: str,
    missing_information: list[str],
    validation_warnings: list[str],
    best_practices: list[BestPracticeReference],
    similar_solutions: list[SimilarSolution],
    reusable_assets: list[ReusableCatalogAsset],
) -> EvidenceConfidenceSummary:
    evidence_strength_summary = (
        f"This recommendation draws on {len(best_practices)} industry best-practice reference(s), "
        f"{len(similar_solutions)} comparable enterprise implementation(s), and "
        f"{len(reusable_assets)} reusable AI Catalog asset(s)."
    )

    return EvidenceConfidenceSummary(
        overall_confidence=confidence_scores.overall,
        confidence_rationale=confidence_rationale,
        dimension_confidence={
            "architecture": confidence_scores.architecture,
            "model": confidence_scores.model,
            "workbench": confidence_scores.workbench,
        },
        missing_information=missing_information,
        validation_warnings=validation_warnings,
        evidence_strength_summary=evidence_strength_summary,
        best_practice_count=len(best_practices),
        similar_solution_count=len(similar_solutions),
        reusable_asset_count=len(reusable_assets),
    )
