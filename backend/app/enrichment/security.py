"""Deterministic security-considerations summary — combines the engine's
existing workbench/security-profile decision, matched Solution Registry
security considerations, and Enterprise Knowledge Platform security
controls retrieved by tag overlap. Pure aggregation; no new scoring.
"""

from app.enterprise_knowledge.factory import get_retrieval_service
from app.enterprise_knowledge.retrieval.base import RetrievalQuery
from app.models.schemas import (
    ArchitecturePattern,
    BestPracticeReference,
    SecuritySummary,
    SignalVector,
    SimilarSolution,
    WorkbenchRecommendation,
)

_MAX_RELEVANT_CONTROLS = 4
_MAX_CONSIDERATIONS = 6


def _security_query_tags(signal_vector: SignalVector, pattern: ArchitecturePattern) -> list[str]:
    """The Enterprise Knowledge Platform's security_control entries use their
    own tag vocabulary (identity, encryption, agentic-safety, ...), distinct
    from the engine's controlled tag set (agentic, realtime, batch, ...) — the
    two were never designed to overlap. This bridges SignalVector/pattern
    signals to that vocabulary directly, the same way `_known_tags()` bridges
    the engine's vocabulary to the LLM in `app/engine/recommend.py`.
    """
    tags = {"identity", "access-control", "data-protection", "encryption"}
    if signal_vector.data_sensitivity == "pii":
        tags.add("pii")
    if signal_vector.data_sensitivity in ("pii", "phi"):
        tags.add("regulated-industry")
    is_agentic_pattern = bool({"agentic", "autonomous"} & set(pattern.suitable_for_tags))
    if is_agentic_pattern or signal_vector.automation_level == "autonomous":
        tags.update({"agentic-safety", "prompt-injection", "human-in-the-loop"})
    if signal_vector.automation_level in ("copilot", "autonomous"):
        tags.add("human-in-the-loop")
    if signal_vector.data_modality in ("text", "mixed", "image"):
        tags.update({"guardrails", "content-safety"})
    return sorted(tags)


def build_security_summary(
    signal_vector: SignalVector,
    pattern: ArchitecturePattern,
    workbench_recommendation: WorkbenchRecommendation,
    similar_solutions: list[SimilarSolution],
) -> SecuritySummary:
    considerations: list[str] = []

    security_profile = workbench_recommendation.security_profile
    considerations.append(workbench_recommendation.reasons.get("security", security_profile.description))

    seen = {considerations[0]}
    for solution in similar_solutions:
        for item in solution.security_considerations:
            if item not in seen:
                considerations.append(item)
                seen.add(item)
            if len(considerations) >= _MAX_CONSIDERATIONS:
                break
        if len(considerations) >= _MAX_CONSIDERATIONS:
            break

    results = get_retrieval_service().search(
        RetrievalQuery(
            category="security_control", tags=_security_query_tags(signal_vector, pattern), limit=_MAX_RELEVANT_CONTROLS
        )
    )
    relevant_controls = [
        BestPracticeReference(
            id=r.entry.id,
            title=r.entry.name,
            vendor=r.entry.source.vendor,
            category=r.entry.category,
            summary=r.entry.summary,
            reference=r.entry.source.reference,
        )
        for r in results
    ]

    return SecuritySummary(
        security_profile_name=security_profile.name,
        restrictiveness_rank=security_profile.restrictiveness_rank,
        compliance_flags=security_profile.compliance_flags,
        considerations=considerations,
        relevant_controls=relevant_controls,
    )
