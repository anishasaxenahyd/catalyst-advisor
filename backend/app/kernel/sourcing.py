"""Stage 11: Sourcing Decisions — the Reuse -> Compose -> Extend -> Buy ->
Build -> Defer precedence ladder (Part 8). Burden of proof rises as you
descend; every non-Reuse decision names the higher option it rejected.

This prototype's catalog has no data on which assets could be composed
together (that needs the real Catalog MCP's dependency-graph/integration-
surface data — see the Catalog Resolution module docstring), so `Compose`
is never emitted here yet; every gap falls through to Buy or Build via the
commodity/differentiating split from Part 8.1's note that guardrails, eval,
and observability are the assurance layer and are usually a Buy.
"""

from app.kernel.schemas import AssetResolution, CapabilityRequirement, SourcingDecision

_COMMODITY_CAPABILITIES = {
    "CAP-INPUT-OUTPUT-GUARDRAILS",
    "CAP-EVAL-HARNESS",
    "CAP-OBSERVABILITY-TRACE",
    "CAP-PHI-SAFE-LOGGING",
    "CAP-AUDIT-SUBJECT-TRACE",
    "CAP-MODEL-SERVING-APPROVED",
}


def decide_sourcing(
    requirements: list[CapabilityRequirement], resolutions: dict[str, AssetResolution]
) -> list[SourcingDecision]:
    decisions: list[SourcingDecision] = []

    for req in requirements:
        if req.status == "deferred":
            decisions.append(
                SourcingDecision(
                    capability_id=req.id,
                    capability_name=req.name,
                    decision="defer",
                    justification="Not required in the current increment; a seam is recorded so it can be added without a breaking change later.",
                )
            )
            continue

        resolution = resolutions.get(req.id)
        if resolution is None or resolution.overall == "gap":
            if req.id in _COMMODITY_CAPABILITIES:
                decisions.append(
                    SourcingDecision(
                        capability_id=req.id,
                        capability_name=req.name,
                        decision="buy",
                        justification="No internal asset provides this capability; it is commodity, non-differentiating assurance-layer capability with a mature market — buying is the standard recommendation here rather than building it from scratch.",
                        rejected_alternatives=["Reuse — no catalog asset found", "Extend — no partial-fit asset exists", "Build — non-differentiating, would duplicate a commodity market"],
                    )
                )
            else:
                decisions.append(
                    SourcingDecision(
                        capability_id=req.id,
                        capability_name=req.name,
                        decision="build",
                        justification="No internal asset provides this capability and it is not commodity assurance-layer functionality — flagged as a genuine capability gap for the platform roadmap.",
                        rejected_alternatives=["Reuse — no catalog asset found", "Extend — no partial-fit asset exists", "Buy — not a commodity capability with a clear market fit"],
                    )
                )
            continue

        if resolution.overall == "reuse":
            decisions.append(
                SourcingDecision(
                    capability_id=req.id,
                    capability_name=req.name,
                    decision="reuse",
                    justification=f"{resolution.asset_name} ({resolution.asset_id}) satisfies functional, compliance, and lifecycle fit for this capability.",
                    asset_ref=resolution.asset_id,
                )
            )
        else:  # extend
            gap_detail = next((f.detail for f in resolution.fit if f.status != "pass"), "a partial fit gap")
            decisions.append(
                SourcingDecision(
                    capability_id=req.id,
                    capability_name=req.name,
                    decision="extend",
                    justification=f"{resolution.asset_name} ({resolution.asset_id}) covers this capability but has a fit gap: {gap_detail} Extending is additive rather than forking.",
                    rejected_alternatives=["Reuse as-is — fit gap noted above", "Build new — would duplicate an existing, mostly-fitting asset"],
                    asset_ref=resolution.asset_id,
                )
            )

    return decisions
