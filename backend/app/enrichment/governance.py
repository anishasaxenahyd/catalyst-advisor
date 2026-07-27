"""Deterministic governance recommendations — combine the engine's existing
config-driven compliance rules (`decision_rules.json`) with Enterprise
Knowledge Platform governance-rule entries matched by tag overlap. No new
scoring dimension: this reuses the same `data_sensitivity_required_compliance`
mapping the workbench selector already applies, plus two new config-driven
policy tables (`governance_policies_by_automation_level`,
`governance_policies_by_expected_scale`) added alongside it.
"""

from app.enterprise_knowledge.factory import get_retrieval_service
from app.enterprise_knowledge.retrieval.base import RetrievalQuery
from app.models.schemas import ArchitecturePattern, GovernanceRecommendation, SignalVector

_MAX_KNOWLEDGE_MATCHES = 3

_HEALTHCARE_INDUSTRY_KEYWORDS = ("health", "hospital", "clinical", "pharma", "life sciences")
_FINANCIAL_INDUSTRY_KEYWORDS = ("financ", "bank", "insur")


def _governance_query_tags(signal_vector: SignalVector, is_autonomous_pattern: bool) -> list[str]:
    """Bridges SignalVector signals to the Enterprise Knowledge Platform's
    governance_rule tag vocabulary (responsible-ai, risk-tiering, ...), which
    is disjoint from the engine's own controlled tag set — see the matching
    note in `app.enrichment.security`.
    """
    tags = {"responsible-ai", "risk-management"}
    if signal_vector.data_sensitivity in ("pii", "phi"):
        tags.update({"regulated-industry", "compliance", "regulation"})
    if signal_vector.automation_level == "autonomous" or is_autonomous_pattern:
        tags.update({"risk-tiering", "safety-levels"})
    industry = signal_vector.industry.lower()
    if any(keyword in industry for keyword in _HEALTHCARE_INDUSTRY_KEYWORDS):
        tags.add("healthcare")
    if any(keyword in industry for keyword in _FINANCIAL_INDUSTRY_KEYWORDS):
        tags.add("financial-services")
    return sorted(tags)


def build_governance_recommendations(
    signal_vector: SignalVector, pattern: ArchitecturePattern, rules: dict
) -> list[GovernanceRecommendation]:
    recommendations: list[GovernanceRecommendation] = []
    is_autonomous_pattern = "autonomous" in pattern.suitable_for_tags

    for flag in rules["data_sensitivity_required_compliance"].get(signal_vector.data_sensitivity, []):
        recommendations.append(
            GovernanceRecommendation(
                title=f"Maintain {flag} compliance posture",
                rationale=f"Data classified as '{signal_vector.data_sensitivity}' sensitivity requires {flag} controls.",
                framework=flag,
                source="policy_rule",
            )
        )

    # The selected architecture pattern is the ground truth for autonomy —
    # apply the autonomous-automation governance policies whenever the
    # pattern itself is autonomous, even if the automation_level hint (a
    # user/LLM signal, not the final decision) said something narrower.
    automation_levels = {signal_vector.automation_level}
    if is_autonomous_pattern:
        automation_levels.add("autonomous")
    for level in sorted(automation_levels):
        for item in rules["governance_policies_by_automation_level"].get(level, []):
            recommendations.append(
                GovernanceRecommendation(title=item["title"], rationale=item["rationale"], source="policy_rule")
            )

    for item in rules["governance_policies_by_expected_scale"].get(signal_vector.expected_scale, []):
        recommendations.append(
            GovernanceRecommendation(title=item["title"], rationale=item["rationale"], source="policy_rule")
        )

    results = get_retrieval_service().search(
        RetrievalQuery(
            category="governance_rule",
            tags=_governance_query_tags(signal_vector, is_autonomous_pattern),
            limit=_MAX_KNOWLEDGE_MATCHES,
        )
    )
    for result in results:
        entry = result.entry
        recommendations.append(
            GovernanceRecommendation(
                title=entry.name,
                rationale=entry.summary,
                framework=getattr(entry, "framework", None),
                source="enterprise_knowledge",
            )
        )

    return recommendations
