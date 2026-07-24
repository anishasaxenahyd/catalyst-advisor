"""Rule-based Workbench axis selection.

Workbench axes aren't scored on the same six dimensions as a pattern, model,
or asset — a security profile is an eligibility question ("does it permit
this data sensitivity"), not a preference ranking. So this module has its
own lighter selection rules, still entirely config-driven via
`decision_rules.json`, but it produces the same `DecisionTrace` shape as
`engine/trace.py` so the frontend renders every recommendation — pattern,
model, or workbench — with one component.
"""

from app.models.schemas import (
    AIModel,
    AlternativeConsidered,
    ComputeProfile,
    DecisionTrace,
    DeploymentTarget,
    SecurityProfile,
    SignalVector,
    WorkbenchRecommendation,
    WorkspaceTier,
)


def _select_security_profile(
    signal: SignalVector, security_profiles: list[SecurityProfile]
) -> tuple[SecurityProfile, str, list[AlternativeConsidered]]:
    eligible = [p for p in security_profiles if signal.data_sensitivity in p.allowed_data_sensitivity]
    ineligible = [p for p in security_profiles if p not in eligible]
    chosen = min(eligible, key=lambda p: p.restrictiveness_rank) if eligible else min(
        security_profiles, key=lambda p: -p.restrictiveness_rank
    )

    alternatives = [
        AlternativeConsidered(
            id=p.id,
            name=p.name,
            score=70.0,
            why_lower=f"Eligible but more restrictive (rank {p.restrictiveness_rank} vs {chosen.restrictiveness_rank}) — unnecessary overhead for this sensitivity level.",
        )
        for p in eligible
        if p.id != chosen.id
    ] + [
        AlternativeConsidered(
            id=p.id,
            name=p.name,
            score=10.0,
            why_lower=f"Does not permit data_sensitivity='{signal.data_sensitivity}' (allows {p.allowed_data_sensitivity}).",
        )
        for p in ineligible
    ]

    reason = f"Least restrictive Workbench security profile that still permits data_sensitivity='{signal.data_sensitivity}'."
    return chosen, reason, alternatives


def _select_workspace_tier(
    security_profile: SecurityProfile, workspace_tiers: list[WorkspaceTier]
) -> tuple[WorkspaceTier, str, list[AlternativeConsidered]]:
    matching = [t for t in workspace_tiers if security_profile.id in t.compatible_security_profiles]
    chosen = matching[0] if matching else workspace_tiers[0]
    others = [t for t in workspace_tiers if t.id != chosen.id]
    alternatives = [
        AlternativeConsidered(
            id=t.id, name=t.name, score=20.0,
            why_lower=f"Not provisioned for the {security_profile.name} security profile.",
        )
        for t in others
    ]
    reason = f"Only workspace tier provisioned for the {security_profile.name} security profile."
    return chosen, reason, alternatives


def _select_compute_profile(
    signal: SignalVector, model: AIModel, compute_profiles: list[ComputeProfile]
) -> tuple[ComputeProfile, str, list[AlternativeConsidered]]:
    scale_matched = [c for c in compute_profiles if signal.expected_scale in c.suitable_scale]
    pool = scale_matched or compute_profiles
    cost_matched = [c for c in pool if model.cost_tier in c.suitable_cost_tiers]
    candidates = cost_matched or pool
    chosen = min(candidates, key=lambda c: c.cost_tier)

    others = [c for c in compute_profiles if c.id != chosen.id]
    alternatives = [
        AlternativeConsidered(
            id=c.id, name=c.name, score=max(10.0, 100 - abs(c.cost_tier - chosen.cost_tier) * 20),
            why_lower=(
                f"Not sized for {signal.expected_scale} scale."
                if signal.expected_scale not in c.suitable_scale
                else f"Higher cost tier than needed for {model.name} (cost_tier {model.cost_tier})."
            ),
        )
        for c in others
    ]
    reason = f"Cheapest compute pool that fits {signal.expected_scale} scale and {model.name}'s cost tier ({model.cost_tier})."
    return chosen, reason, alternatives


def _select_deployment_targets(
    security_profile: SecurityProfile, deployment_targets: list[DeploymentTarget]
) -> tuple[list[DeploymentTarget], str, list[AlternativeConsidered]]:
    required = set(security_profile.compliance_flags)
    qualifying = [t for t in deployment_targets if required.issubset(set(t.supports_compliance_flags))]
    chosen = qualifying or deployment_targets
    excluded = [t for t in deployment_targets if t not in chosen]
    alternatives = [
        AlternativeConsidered(
            id=t.id, name=t.name, score=15.0,
            why_lower=f"Missing required compliance flag(s) for {security_profile.name}: {sorted(required - set(t.supports_compliance_flags))}.",
        )
        for t in excluded
    ]
    reason = (
        f"All targets supporting every compliance flag required by {security_profile.name}."
        if qualifying
        else "No target fully covers the required compliance flags — all three listed for governance review."
    )
    return chosen, reason, alternatives


def select_workbench(
    signal: SignalVector,
    primary_model: AIModel,
    security_profiles: list[SecurityProfile],
    workspace_tiers: list[WorkspaceTier],
    compute_profiles: list[ComputeProfile],
    deployment_targets: list[DeploymentTarget],
) -> WorkbenchRecommendation:
    security_profile, security_reason, security_alts = _select_security_profile(signal, security_profiles)
    workspace_tier, workspace_reason, workspace_alts = _select_workspace_tier(security_profile, workspace_tiers)
    compute_profile, compute_reason, compute_alts = _select_compute_profile(signal, primary_model, compute_profiles)
    chosen_targets, deployment_reason, deployment_alts = _select_deployment_targets(
        security_profile, deployment_targets
    )

    merged_trace = DecisionTrace(
        selected=f"{workspace_tier.id}+{compute_profile.id}+{security_profile.id}",
        why_selected=(
            f"Security: {security_reason} Workspace: {workspace_reason} "
            f"Compute: {compute_reason} Deployment: {deployment_reason}"
        ),
        alternatives_considered=security_alts + workspace_alts + compute_alts + deployment_alts,
        assumptions=[
            f"Compute sizing assumes {primary_model.name} as the primary model; a different model choice would re-run this selection."
        ],
        confidence=90.0 if signal.data_sensitivity == "none" or security_profile.id != "security-standard" else 75.0,
        evidence=[
            f"signal.data_sensitivity={signal.data_sensitivity}",
            f"signal.expected_scale={signal.expected_scale}",
            f"primary_model.cost_tier={primary_model.cost_tier}",
        ],
    )

    return WorkbenchRecommendation(
        workspace_tier=workspace_tier,
        compute_profile=compute_profile,
        security_profile=security_profile,
        deployment_targets=chosen_targets,
        reasons={
            "workspace": workspace_reason,
            "compute": compute_reason,
            "security": security_reason,
            "deployment": deployment_reason,
        },
        decision_trace=merged_trace,
    )
