"""Stage 10: Catalog Resolution — the Catalog Plane entry point.

The governing invariant lives here structurally, not by convention: this
function's only input is a `CapabilityRequirement` list that Stages 5-8
already derived without looking at the catalog. The catalog is asked
"what resolves CAP-X" — it is never asked "what have you got", and nothing
upstream of this stage has seen a catalog asset ID. That ordering is what
stops the Catalog from framing the problem (Part 1.3).

Six fit dimensions per the design doc; three are computed from real fields
in this prototype's catalog data (functional, compliance, lifecycle) and
three are placeholder-pass (integration, operational, access) until the
real AI Catalog MCP exposes capacity/SLA/consumer data — see
`docs/catalog-mcp-integration.md` for exactly what to wire up so those three
stop being placeholders without touching any other kernel stage.
"""

from app.engine.config_loader import get_decision_rules
from app.kernel.schemas import AssetFit, AssetResolution, CapabilityRequirement
from app.models.schemas import AIModel, EnterpriseAsset, SignalVector
from app.providers.knowledge.base import KnowledgeProvider


def _compliance_fit(signal: SignalVector, compliance: list[str]) -> AssetFit:
    required = get_decision_rules()["data_sensitivity_required_compliance"].get(signal.data_sensitivity, [])
    if not required:
        return AssetFit(dimension="compliance", status="pass", detail=f"No compliance flag required for data_sensitivity='{signal.data_sensitivity}'.")
    if any(flag in compliance for flag in required):
        return AssetFit(dimension="compliance", status="pass", detail=f"Carries required flag(s) {required} for '{signal.data_sensitivity}' data.")
    return AssetFit(dimension="compliance", status="fail", detail=f"Missing required flag(s) {required} for '{signal.data_sensitivity}' data — not a partial match, a non-match.")


def _lifecycle_fit(status: str) -> AssetFit:
    if status == "supported":
        return AssetFit(dimension="lifecycle", status="pass", detail="Actively supported.")
    if status == "deprecated":
        return AssetFit(dimension="lifecycle", status="partial", detail="Deprecated — usable but flagged for migration risk.")
    return AssetFit(dimension="lifecycle", status="fail", detail="Sunsetting — do not build a new dependency on this asset.")


_PLACEHOLDER_DIMENSIONS = (
    ("integration", "Assumed compatible pending real integration-surface data from the Catalog MCP."),
    ("operational", "Assumed sufficient capacity/SLA pending live capacity data from the Catalog MCP."),
    ("access", "Assumed consumable by the requesting team pending live ownership/access data from the Catalog MCP."),
)


def _overall_from_fit(fit: list[AssetFit]) -> str:
    by_dim = {f.dimension: f.status for f in fit}
    if by_dim["compliance"] == "fail" or by_dim["lifecycle"] == "fail":
        return "gap"
    if by_dim["lifecycle"] == "partial":
        return "extend"
    return "reuse"


def _candidate_assets(cap_id: str, assets: list[EnterpriseAsset], models: list[AIModel]) -> list[tuple[str, str, list[str], str, str]]:
    """Returns (id, name, compliance, lifecycle_status, reuse_score_sort_key) for every catalog item providing cap_id."""
    out = []
    for a in assets:
        if cap_id in a.capabilities:
            out.append((a.id, a.name, a.compliance, a.lifecycle_status, a.reuse_score))
    for m in models:
        if cap_id in m.capabilities:
            out.append((m.id, m.name, m.compliance, "supported", 50))
    return out


def resolve_capabilities(
    requirements: list[CapabilityRequirement], signal: SignalVector, kp: KnowledgeProvider
) -> list[AssetResolution]:
    assets = kp.list_enterprise_assets()
    models = kp.list_models()
    resolutions: list[AssetResolution] = []

    for req in requirements:
        if req.status == "deferred":
            continue
        candidates = _candidate_assets(req.id, assets, models)
        if not candidates:
            resolutions.append(AssetResolution(capability_id=req.id, overall="gap", fit=[AssetFit(dimension="functional", status="fail", detail="No catalog asset or model currently provides this capability.")]))
            continue

        best = None
        best_fit: list[AssetFit] = []
        best_rank = -1
        for asset_id, name, compliance, lifecycle_status, sort_key in candidates:
            fit = [
                AssetFit(dimension="functional", status="pass", detail=f"Provides capability {req.id} directly."),
                _compliance_fit(signal, compliance),
                _lifecycle_fit(lifecycle_status),
                *[AssetFit(dimension=d, status="pass", detail=note) for d, note in _PLACEHOLDER_DIMENSIONS],
            ]
            rank = sum(1 for f in fit if f.status == "pass") * 100 + sort_key
            if rank > best_rank:
                best, best_fit, best_rank = (asset_id, name), fit, rank

        resolutions.append(
            AssetResolution(
                capability_id=req.id,
                asset_id=best[0],
                asset_name=best[1],
                fit=best_fit,
                overall=_overall_from_fit(best_fit),
            )
        )
    return resolutions
