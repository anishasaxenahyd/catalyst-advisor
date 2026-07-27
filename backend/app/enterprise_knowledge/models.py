"""Vendor-neutral knowledge model for the Enterprise Knowledge Platform.

Deliberately separate from `app.models.schemas` — that module is the
Catalyst-specific (fictional) catalog shape consumed by the deterministic
engine, and this phase's brief is explicit: don't touch it. This module is
the foundation for a broader, real-vendor knowledge base (Microsoft, AWS,
Google Cloud, Anthropic, OpenAI, and vendor-neutral frameworks) that a
future LLM-assisted pipeline will reason over. Nothing here is wired into
the live recommendation flow yet.

Every entry traces back to a `KnowledgeSourceRef` — no entry exists without
attribution to where the knowledge came from, since "evidence" is the
whole point of the platform this is a foundation for.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

SourceVendor = Literal["microsoft", "aws", "google_cloud", "anthropic", "openai", "vendor_neutral"]

KnowledgeCategory = Literal[
    "architecture_pattern",
    "ai_model",
    "security_control",
    "governance_rule",
    "cloud_service",
    "ai_catalog_component",
    "reference_architecture",
]


EvidenceType = Literal[
    "official_documentation",
    "reference_architecture",
    "whitepaper",
    "best_practice_guide",
    "framework_publication",
    "engineering_blog",
]

EvidenceConfidence = Literal["high", "medium", "low"]


class KnowledgeSourceRef(BaseModel):
    """Attribution for one knowledge entry or relationship — the platform's
    structured evidence metadata. `reference` is a descriptive citation
    (e.g. "Microsoft Learn — Azure Well-Architected Framework"),
    deliberately not a deep-linked URL — vendor doc URLs change and
    shouldn't be guessed at or hardcoded as if verified.

    `evidence_type`/`confidence`/`excerpt` are additive fields with
    defaults, so every entry seeded before they existed still validates
    unchanged — existing data and tests are unaffected by this extension.
    """

    vendor: SourceVendor
    title: str
    reference: str
    published: str | None = Field(
        default=None, description="Rough recency marker (e.g. a year), not a precise date."
    )
    evidence_type: EvidenceType = Field(
        default="official_documentation", description="What kind of public source this attribution points to."
    )
    confidence: EvidenceConfidence = Field(
        default="medium", description="How strongly this evidence supports the claim it's attached to."
    )
    excerpt: str | None = Field(
        default=None, description="An optional short paraphrase/quote grounding the claim, not a verbatim reproduction."
    )


class KnowledgeEntryBase(BaseModel):
    id: str
    name: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    source: KnowledgeSourceRef


class ArchitecturePatternEntry(KnowledgeEntryBase):
    category: Literal["architecture_pattern"] = "architecture_pattern"
    use_cases: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    trade_offs: list[str] = Field(default_factory=list)


class AIModelEntry(KnowledgeEntryBase):
    category: Literal["ai_model"] = "ai_model"
    modality: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    considerations: list[str] = Field(default_factory=list)


class SecurityControlEntry(KnowledgeEntryBase):
    category: Literal["security_control"] = "security_control"
    control_family: str
    frameworks: list[str] = Field(default_factory=list)


class GovernanceRuleEntry(KnowledgeEntryBase):
    category: Literal["governance_rule"] = "governance_rule"
    framework: str
    applies_to: list[str] = Field(default_factory=list)


class CloudServiceEntry(KnowledgeEntryBase):
    category: Literal["cloud_service"] = "cloud_service"
    service_type: str
    deployment_models: list[str] = Field(default_factory=list)


class AICatalogComponentEntry(KnowledgeEntryBase):
    category: Literal["ai_catalog_component"] = "ai_catalog_component"
    component_type: str


class ReferenceArchitectureEntry(KnowledgeEntryBase):
    category: Literal["reference_architecture"] = "reference_architecture"
    industries: list[str] = Field(default_factory=list)
    related_pattern_ids: list[str] = Field(default_factory=list)


KnowledgeEntry = Annotated[
    Union[
        ArchitecturePatternEntry,
        AIModelEntry,
        SecurityControlEntry,
        GovernanceRuleEntry,
        CloudServiceEntry,
        AICatalogComponentEntry,
        ReferenceArchitectureEntry,
    ],
    Field(discriminator="category"),
]

_CATEGORY_MODEL: dict[KnowledgeCategory, type[KnowledgeEntryBase]] = {
    "architecture_pattern": ArchitecturePatternEntry,
    "ai_model": AIModelEntry,
    "security_control": SecurityControlEntry,
    "governance_rule": GovernanceRuleEntry,
    "cloud_service": CloudServiceEntry,
    "ai_catalog_component": AICatalogComponentEntry,
    "reference_architecture": ReferenceArchitectureEntry,
}


def model_for_category(category: KnowledgeCategory) -> type[KnowledgeEntryBase]:
    return _CATEGORY_MODEL[category]


RelationType = Literal[
    "requires",
    "recommends",
    "alternative_to",
    "implements",
    "composed_of",
    "governed_by",
    "hosted_on",
    "mitigates",
    "compatible_with",
]


class KnowledgeRelationship(BaseModel):
    """A directed, typed edge between two knowledge entries — e.g. the RAG
    pattern *requires* prompt-injection mitigation, or Azure OpenAI is
    *hosted_on* Azure AI Foundry. Not a graph database: this is a flat,
    seeded edge list today, deliberately simple (see `RelationshipIndex`
    in `retrieval/`), with the same evidence-attribution discipline as
    every entry — a relationship is a claim too, and claims need sources.
    """

    id: str
    from_id: str
    from_category: KnowledgeCategory
    to_id: str
    to_category: KnowledgeCategory
    relation_type: RelationType
    description: str
    source: KnowledgeSourceRef


class KnowledgeBase(BaseModel):
    """The full, in-memory knowledge base — one list per category. A thin
    container today; `factory.py` is the only place that constructs one,
    from the seed data. A future ingestion source (a live vendor feed, a
    vector index, a knowledge graph) fills the same container shape."""

    architecture_patterns: list[ArchitecturePatternEntry] = Field(default_factory=list)
    ai_models: list[AIModelEntry] = Field(default_factory=list)
    security_controls: list[SecurityControlEntry] = Field(default_factory=list)
    governance_rules: list[GovernanceRuleEntry] = Field(default_factory=list)
    cloud_services: list[CloudServiceEntry] = Field(default_factory=list)
    ai_catalog_components: list[AICatalogComponentEntry] = Field(default_factory=list)
    reference_architectures: list[ReferenceArchitectureEntry] = Field(default_factory=list)
    # Added alongside the existing seven category lists. `counts()` below
    # is intentionally left untouched (still entry-category counts only)
    # so existing callers/tests keep working unchanged — relationship
    # totals are available via `len(kb.relationships)` or the new
    # `/api/knowledge/relationships` route.
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)

    def all_entries(self) -> list[KnowledgeEntry]:
        return [
            *self.architecture_patterns,
            *self.ai_models,
            *self.security_controls,
            *self.governance_rules,
            *self.cloud_services,
            *self.ai_catalog_components,
            *self.reference_architectures,
        ]

    def counts(self) -> dict[str, int]:
        return {
            "architecture_pattern": len(self.architecture_patterns),
            "ai_model": len(self.ai_models),
            "security_control": len(self.security_controls),
            "governance_rule": len(self.governance_rules),
            "cloud_service": len(self.cloud_services),
            "ai_catalog_component": len(self.ai_catalog_components),
            "reference_architecture": len(self.reference_architectures),
        }
