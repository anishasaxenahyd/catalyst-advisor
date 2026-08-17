"""Data shape for the Solution Registry.

A `SolutionRecord` is a fictional-but-realistic account of a past enterprise
AI implementation. `architecture_pattern_id` deliberately reuses the same
five pattern ids the deterministic engine already selects from
(`app/providers/knowledge`'s `architecture_templates.json`), so the
enrichment layer can match a recommendation to similar past solutions with
a plain id comparison instead of fuzzy text matching.
"""

from typing import Literal

from pydantic import BaseModel, Field

CloudProvider = Literal["Azure", "AWS", "GCP"]

EvidenceClass = Literal[
    "proven_in_production", "production_limited", "pilot", "prototype_poc", "abandoned", "superseded"
]


class SolutionRecord(BaseModel):
    id: str
    title: str
    industry: str
    business_problem: str
    architecture_pattern_id: str
    architecture_pattern_name: str
    ai_models: list[str] = Field(default_factory=list)
    cloud_provider: CloudProvider
    reused_catalog_assets: list[str] = Field(default_factory=list)
    security_considerations: list[str] = Field(default_factory=list)
    business_outcome: str
    lessons_learned: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # -- decision-situation fields (Knowledge Plane / precedent dossier) --
    obligation_profile: list[str] = Field(
        default_factory=list,
        description="Obligation IDs (data/policy/obligations.json) that governed this solution — the primary precedent-matching key.",
    )
    requirement_signatures: list[str] = Field(
        default_factory=list,
        description="Requirement signature IDs this solution satisfied, in the same closed vocabulary Stage 3 extracts into.",
    )
    evidence_class: EvidenceClass = Field(
        default="proven_in_production",
        description="Derived-from-signals evidence strength — only proven_in_production may support a transferable decision; "
        "abandoned/superseded are retained deliberately as hazard evidence.",
    )
    conditions: list[str] = Field(
        default_factory=list,
        description="What had to be true for this solution's decisions to be correct — the condition a precedent match must "
        "re-verify before transferring the decision to a new problem.",
    )
