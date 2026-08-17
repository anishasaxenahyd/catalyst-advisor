"""Data shapes for the Decision Kernel.

Kept separate from `app.models.schemas` (the Catalyst catalog/report shapes
consumed by the UI) because these types are internal to the reasoning
pipeline — most never reach the API response directly; `Report` in
`app.models.schemas` embeds only the projections a client needs.

Two families of type live here:
  * Taxonomy/knowledge definitions (`CapabilityDef`, `RequirementSignatureDef`,
    `SolutionClassDef`, `PatternRecord`, `ObligationRule`) — loaded once from
    `data/taxonomy/`, `data/knowledge/`, `data/policy/` and cached.
  * Working types the kernel stages produce and thread through the pipeline,
    culminating in the `DecisionRecord` — the typed graph every rendered
    recommendation is a projection of, never an independent regeneration.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Taxonomy / knowledge definitions (loaded, not computed)
# --------------------------------------------------------------------------


class CapabilityDef(BaseModel):
    id: str
    name: str
    description: str
    category: str


class RequirementSignatureDef(BaseModel):
    id: str
    category: str
    description: str
    legacy_tags: list[str] = Field(default_factory=list)


class SolutionClassDef(BaseModel):
    id: str
    name: str
    description: str
    indicative_signatures: list[str] = Field(default_factory=list)
    required_signature_categories: list[str] = Field(default_factory=list)


PatternType = Literal["solution", "assurance"]
Maturity = Literal["proven", "emerging", "experimental"]


class PatternRecord(BaseModel):
    id: str
    name: str
    pattern_type: PatternType
    intent: str
    description: str
    preconditions: list[str] = Field(default_factory=list)
    indications: list[str] = Field(default_factory=list)
    contra_indications: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    fulfills_capabilities: list[str] = Field(
        default_factory=list, description="Assurance patterns only: the capability requirement that makes this REQUIRED."
    )
    complexity_tier: int = Field(ge=1, le=5)
    escalation_trigger: Optional[str] = None
    composition: dict[str, list[str]] = Field(default_factory=dict)
    maturity: Maturity = "proven"
    internal_precedent_count: int = 0
    scale_ceiling: str = "enterprise"
    mermaid_template: str = ""


class ObligationCondition(BaseModel):
    field: str
    op: Literal["equals", "in", "contains"]
    value: object


class ObligationRule(BaseModel):
    id: str
    title: str
    source: str
    match: Literal["any", "all"] = "any"
    conditions: list[ObligationCondition] = Field(default_factory=list)
    mandates_capabilities: list[str] = Field(default_factory=list)
    description: str = ""


# --------------------------------------------------------------------------
# Working types — produced stage by stage
# --------------------------------------------------------------------------

ProvenanceType = Literal[
    "user_stated", "policy_rule", "catalog_fact", "precedent", "pattern_contract",
    "external_reference", "service_derived", "model_inference",
]

ConfidenceClass = Literal["established", "reasoned", "provisional", "uncertain"]


class RequirementSignatureInstance(BaseModel):
    id: str
    category: str
    source_span: str
    provenance: ProvenanceType


class Assumption(BaseModel):
    id: str
    statement: str
    field: str = ""


class Clarification(BaseModel):
    field_or_signature: str
    question: str
    decision_critical: bool = False


SufficiencyStatus = Literal["PROCEED", "PROCEED_WITH_QUESTIONS", "HALT_CLARIFY"]


class SufficiencyOutcome(BaseModel):
    status: SufficiencyStatus
    blocking_questions: list[Clarification] = Field(default_factory=list)
    advisory_questions: list[Clarification] = Field(default_factory=list)
    rationale: str = ""


class ObligationInstance(BaseModel):
    id: str
    title: str
    source: str
    mandates_capabilities: list[str] = Field(default_factory=list)
    rationale: str


CapabilityStatus = Literal["mandatory", "conditional", "deferred"]


class CapabilityRequirement(BaseModel):
    id: str
    name: str
    status: CapabilityStatus
    derived_from: list[str] = Field(default_factory=list, description="Obligation/pattern/signature IDs this was derived from.")


PatternVerdict = Literal["REQUIRED", "APPLICABLE", "CONDITIONAL", "UNNECESSARY", "CONTRA_INDICATED"]


class PatternVerdictEntry(BaseModel):
    pattern_id: str
    pattern_name: str
    pattern_type: PatternType
    verdict: PatternVerdict
    reason: str
    matched_indications: list[str] = Field(default_factory=list)
    matched_contra_indications: list[str] = Field(default_factory=list)


class PrecedentFinding(BaseModel):
    solution_id: str
    title: str
    evidence_class: str
    similarity_basis: list[str] = Field(default_factory=list)
    transferable: bool
    conditions: list[str] = Field(default_factory=list)
    divergences: list[str] = Field(default_factory=list)
    lesson_summary: str = ""
    usage: Literal["transferable_decision_evidence", "feasibility_evidence", "hazard_evidence"] = "feasibility_evidence"


FitStatus = Literal["pass", "partial", "fail"]


class AssetFit(BaseModel):
    dimension: str
    status: FitStatus
    detail: str


class AssetResolution(BaseModel):
    capability_id: str
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    fit: list[AssetFit] = Field(default_factory=list)
    overall: Literal["reuse", "extend", "gap"]


SourcingOutcome = Literal["reuse", "compose", "extend", "buy", "build", "defer"]


class SourcingDecision(BaseModel):
    capability_id: str
    capability_name: str
    decision: SourcingOutcome
    justification: str
    rejected_alternatives: list[str] = Field(default_factory=list)
    asset_ref: Optional[str] = None


class Candidate(BaseModel):
    id: str
    label: str
    description: str
    pattern_ids: list[str] = Field(default_factory=list)
    complexity_score: int = 0
    covers_all_mandatory_capabilities: bool = True
    uncovered_capabilities: list[str] = Field(default_factory=list)


class EliminationEntry(BaseModel):
    candidate_id: str
    candidate_label: str
    gate: str
    rule_id: str
    evidence: str


class Alternative(BaseModel):
    candidate_id: str
    label: str
    governing_priority: str
    what_is_given_up: str
    switching_cost: str
    revisit_trigger: str


class DecisionNode(BaseModel):
    id: str
    type: str
    statement: str
    provenance: ProvenanceType
    stage: str
    confidence: ConfidenceClass = "reasoned"


class DecisionEdge(BaseModel):
    from_id: str
    to_id: str
    relation: str


class DecisionRecord(BaseModel):
    nodes: list[DecisionNode] = Field(default_factory=list)
    edges: list[DecisionEdge] = Field(default_factory=list)

    def add_node(self, node: DecisionNode) -> DecisionNode:
        self.nodes.append(node)
        return node

    def add_edge(self, from_id: str, to_id: str, relation: str) -> None:
        self.edges.append(DecisionEdge(from_id=from_id, to_id=to_id, relation=relation))


class KernelNarrationInput(BaseModel):
    """What reaches the LLM's narration-extras call — already-decided facts
    only, per the same 'render, don't decide' contract as ExecutiveNarrative."""

    solution_class_name: str
    pattern_verdicts: list[PatternVerdictEntry]
    sourcing_decisions: list[SourcingDecision]
    candidates: list[Candidate]
    elimination_record: list[EliminationEntry]
    recommended_candidate_label: str
    alternatives: list[Alternative]
    precedent_findings: list[PrecedentFinding]


class AlternativeNarrative(BaseModel):
    candidate_id: str
    narrative: str


class KernelNarrativeExtras(BaseModel):
    """LLM-authored prose over the kernel's already-decided findings — never
    permitted to introduce a pattern, asset, or decision not already present
    in `KernelNarrationInput`."""

    rejected_options_narrative: str
    sourcing_narrative: str
    alternatives_narrative: list[AlternativeNarrative] = Field(default_factory=list)
    counterfactuals: list[str] = Field(default_factory=list)


class KernelResult(BaseModel):
    """Everything the kernel decided, before the LLM renders it into prose.
    Analogous to `EngineOutput` in the old pipeline, but carrying the full
    staged trail instead of just final scores."""

    sufficiency: SufficiencyOutcome
    obligations: list[ObligationInstance]
    solution_class_id: str
    solution_class_name: str
    capability_requirements: list[CapabilityRequirement]
    pattern_verdicts: list[PatternVerdictEntry]
    precedent_findings: list[PrecedentFinding]
    asset_resolutions: list[AssetResolution]
    sourcing_decisions: list[SourcingDecision]
    candidates: list[Candidate]
    surviving_candidate_ids: list[str]
    elimination_record: list[EliminationEntry]
    recommended_candidate_id: Optional[str]
    alternatives: list[Alternative]
    rejected_patterns: list[PatternVerdictEntry]
    assumptions: list[Assumption]
    counterfactuals: list[str]
    decision_record: DecisionRecord
