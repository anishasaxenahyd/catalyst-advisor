"""Pydantic schemas shared across providers, engine, and API.

Nothing in this module talks to a vendor, a file, or the network — it is pure
data shape. Providers (knowledge/, llm/) produce and consume these types;
engine/ never sees anything else.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.kernel.schemas import (
    Alternative,
    Assumption,
    Candidate,
    DecisionRecord,
    EliminationEntry,
    KernelNarrativeExtras,
    ObligationInstance,
    PatternVerdictEntry,
    PrecedentFinding,
    SourcingDecision,
    SufficiencyOutcome,
)

DataSensitivity = Literal["none", "pii", "phi"]
DataModality = Literal["text", "image", "structured", "mixed"]
LatencyRequirement = Literal["batch", "near_realtime", "realtime"]
ExpectedScale = Literal["pilot", "department", "enterprise"]
AutomationLevel = Literal["assist", "copilot", "autonomous"]
SubmissionMode = Literal["idea", "design_review"]
RelativeLevel = Literal["low", "medium", "high"]


# --------------------------------------------------------------------------
# Catalog / Workbench entities (as loaded from JSON, unmodified by the engine)
# --------------------------------------------------------------------------


class AIModel(BaseModel):
    id: str
    name: str
    family: str
    modality: list[str]
    context_window: int
    cost_tier: int = Field(ge=1, le=5)
    latency_tier: int = Field(ge=1, le=5)
    compliance: list[str] = Field(default_factory=list)
    suitable_for_tags: list[str] = Field(default_factory=list)
    scale_ceiling: ExpectedScale
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    description: str
    is_primary_candidate: bool = Field(
        default=True,
        description="False for support-only models (embeddings, moderation) that should never be picked as the primary recommendation.",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Capability taxonomy IDs this model provides (see data/taxonomy/capabilities.json).",
    )


class ArchitecturePattern(BaseModel):
    id: str
    name: str
    description: str
    complexity_tier: int = Field(ge=1, le=5)
    suitable_for_tags: list[str] = Field(default_factory=list)
    scale_ceiling: ExpectedScale
    mermaid_template: str


class EnterpriseAsset(BaseModel):
    id: str
    category: Literal["skill", "mcp_server", "agent", "api"]
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    reuse_score: int = Field(ge=0, le=100)
    compliance: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(
        default_factory=list,
        description="Capability taxonomy IDs this asset provides (see data/taxonomy/capabilities.json). "
        "The Catalog Resolution stage matches on this, never on tags.",
    )
    lifecycle_status: Literal["supported", "deprecated", "sunsetting"] = "supported"
    owning_team: str = "Unassigned"


class SecurityProfile(BaseModel):
    id: str
    name: str
    description: str
    allowed_data_sensitivity: list[DataSensitivity]
    compliance_flags: list[str] = Field(default_factory=list)
    restrictiveness_rank: int


class WorkspaceTier(BaseModel):
    id: str
    name: str
    description: str
    compatible_security_profiles: list[str]


class ComputeProfile(BaseModel):
    id: str
    name: str
    description: str
    suitable_scale: list[ExpectedScale]
    suitable_cost_tiers: list[int]
    cost_tier: int = Field(ge=1, le=5)


class DeploymentTarget(BaseModel):
    id: str
    name: str
    description: str
    supports_compliance_flags: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Request / intake
# --------------------------------------------------------------------------


class StructuredHints(BaseModel):
    """Fields the Phase 0 UI collects directly via dropdowns, rather than
    inferring from free text — kept deterministic until an LLMProvider is
    activated to do real inference."""

    industry: Optional[str] = None
    data_sensitivity: Optional[DataSensitivity] = None
    expected_scale: Optional[ExpectedScale] = None
    automation_level: Optional[AutomationLevel] = None


class RecommendationRequest(BaseModel):
    mode: SubmissionMode
    description: str = ""
    diagram_text: Optional[str] = None
    diagram_filename: Optional[str] = None
    hints: StructuredHints = Field(default_factory=StructuredHints)


class RawInput(BaseModel):
    """What reaches the LLMProvider — already normalized, never a raw upload."""

    mode: SubmissionMode
    text: str
    hints: StructuredHints
    known_tags: list[str] = Field(
        default_factory=list,
        description=(
            "The Catalog's controlled tag vocabulary, supplied by the engine "
            "orchestrator so extraction constrains SignalVector.tags to values "
            "the scoring engine can actually match against."
        ),
    )


class RawExtractedSignal(BaseModel):
    """What an LLMProvider hands back before validation — every field
    optional and untyped-beyond-string, because untrusted model output
    should never be allowed to fail Pydantic's strict Literal validation
    for something fixable (wrong casing, a synonym, a value the user
    already supplied via hints). `app.validation.signal_normalizer` turns
    this into a proper `SignalVector`; nothing else consumes it.
    """

    use_case_type: Optional[str] = None
    industry: Optional[str] = None
    data_sensitivity: Optional[str] = None
    data_modality: Optional[str] = None
    latency_requirement: Optional[str] = None
    expected_scale: Optional[str] = None
    automation_level: Optional[str] = None
    integration_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Prompt optimizer (pre-submission, advisory only — never touches scoring)
# --------------------------------------------------------------------------


class QAExchange(BaseModel):
    """One clarifying question the optimizer asked and how the user
    answered it (or skipped it), carried by the stateless frontend across
    optimize_prompt() calls rather than persisted server-side."""

    field: str
    question: str
    answer: str = ""


class PromptOptimizationRequest(BaseModel):
    mode: SubmissionMode
    description: str = ""
    diagram_text: Optional[str] = None
    hints: StructuredHints = Field(default_factory=StructuredHints)
    prior_answers: list[QAExchange] = Field(default_factory=list)


class RawPromptOptimization(BaseModel):
    """What an LLMProvider hands back before validation — untrusted, like
    `RawExtractedSignal`. `app.validation.prompt_optimization_normalizer`
    turns this into a `PromptOptimizationResult`; nothing else consumes it.
    """

    optimized_text: Optional[str] = None
    gaps: list[str] = Field(default_factory=list)
    questions: list[dict] = Field(default_factory=list)
    notes: Optional[str] = None


class ClarifyingQuestion(BaseModel):
    field: str
    question: str


class PromptOptimizationResult(BaseModel):
    optimized_text: str
    original_token_estimate: int
    optimized_token_estimate: int
    gaps: list[str] = Field(default_factory=list)
    clarifying_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    notes: str = ""


FieldProvenance = Literal["user", "llm", "default"]


class ValidationWarning(BaseModel):
    field: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    reason: str


class SignalVector(BaseModel):
    use_case_type: str
    industry: str
    data_sensitivity: DataSensitivity
    data_modality: DataModality
    latency_requirement: LatencyRequirement
    expected_scale: ExpectedScale
    automation_level: AutomationLevel
    integration_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    field_provenance: dict[str, FieldProvenance] = Field(
        default_factory=dict,
        description="Per-field origin (user hint / LLM inference / default fallback) recorded by the validation layer.",
    )
    validation_warnings: list[ValidationWarning] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Scoring / explanation
# --------------------------------------------------------------------------


class ScoringResult(BaseModel):
    dimension_scores: dict[str, float]
    weighted_total: float
    confidence: float


class ScoredCandidate(BaseModel):
    id: str
    name: str
    scoring: ScoringResult


class AlternativeConsidered(BaseModel):
    id: str
    name: str
    score: float
    why_lower: str


class DecisionTrace(BaseModel):
    selected: str
    why_selected: str
    alternatives_considered: list[AlternativeConsidered] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(
        default_factory=list,
        description="Signal fields that neither the user nor the LLM provided, and were filled with a default.",
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable record of every value the validation layer corrected or discarded.",
    )
    confidence_rationale: str = Field(
        default="",
        description="Why overall confidence is what it is, in terms of user-provided vs. LLM-inferred vs. defaulted signal fields.",
    )


# --------------------------------------------------------------------------
# Recommendation presentation
# --------------------------------------------------------------------------


class ArchitectureRecommendation(BaseModel):
    pattern: ArchitecturePattern
    rationale: str
    decision_trace: DecisionTrace


class ModelAlternative(BaseModel):
    model: AIModel
    rationale: str
    trade_off: str
    relative_cost: RelativeLevel


class ModelRecommendation(BaseModel):
    primary: AIModel
    primary_rationale: str
    alternatives: list[ModelAlternative] = Field(default_factory=list)
    relative_cost: RelativeLevel
    relative_latency: RelativeLevel
    suitability_rationale: str
    decision_trace: DecisionTrace


class EnterpriseReuseItem(BaseModel):
    asset: EnterpriseAsset
    rationale: str


class WorkbenchRecommendation(BaseModel):
    workspace_tier: WorkspaceTier
    compute_profile: ComputeProfile
    security_profile: SecurityProfile
    deployment_targets: list[DeploymentTarget]
    reasons: dict[str, str]
    decision_trace: DecisionTrace


class FeasibilityScore(BaseModel):
    technical: int
    business: int


class ConfidenceScores(BaseModel):
    overall: int
    architecture: int
    model: int
    workbench: int


class RiskItem(BaseModel):
    """LLM-authored risk assessment. `status` is deliberately absent here —
    it is stamped on deterministically (always "Open") when assembling the
    final `Report`, never invented by the model."""

    risk: str
    impact: RelativeLevel
    likelihood: RelativeLevel
    mitigation: str


class Risk(RiskItem):
    status: str = "Open"


class ExecutiveCards(BaseModel):
    """Four short LLM-authored cards replacing the old prose executive
    summary — same 'narrate, don't decide' contract as the rest of
    ExecutiveNarrative. `recommended_pattern` is cross-checked by the UI
    against the deterministic pattern name so it can't silently drift."""

    problem: str
    opportunity: str
    recommended_pattern: str
    expected_outcome: str


class ExecutiveNarrative(BaseModel):
    """The only part of a Report an LLMProvider is allowed to author."""

    report_title: str
    one_line_summary: str
    executive_cards: ExecutiveCards
    risks: list[RiskItem]
    assumptions: list[str]
    next_best_actions: list[str]


class EngineOutput(BaseModel):
    """Everything the deterministic engine decided, before narration.

    Passed whole into LLMProvider.generate_executive_report() so the prose
    can reference specifics without being able to change any of them.
    """

    signal_vector: SignalVector
    business_understanding: "BusinessUnderstanding"
    architecture_recommendation: ArchitectureRecommendation
    enterprise_reuse: list[EnterpriseReuseItem]
    model_recommendation: ModelRecommendation
    workbench_recommendation: WorkbenchRecommendation
    feasibility: FeasibilityScore
    effort_estimate: str
    timeline_estimate: str
    confidence_scores: ConfidenceScores


# --------------------------------------------------------------------------
# Enterprise context enrichment (AI Catalog, Solution Registry, Enterprise
# Knowledge Platform) — additive, populated by app.enrichment.service and
# attached to Report.enrichment. Optional so nothing that already builds a
# Report without it (existing tests, the mock provider path) breaks.
# --------------------------------------------------------------------------


class ReusableCatalogAsset(BaseModel):
    id: str
    name: str
    asset_type: str
    description: str
    rationale: str


class SimilarSolution(BaseModel):
    id: str
    title: str
    industry: str
    architecture_pattern_name: str
    business_outcome: str
    lessons_learned: list[str] = Field(default_factory=list)
    security_considerations: list[str] = Field(default_factory=list)
    rationale: str


class BestPracticeReference(BaseModel):
    id: str
    title: str
    vendor: str
    category: str
    summary: str
    reference: str


class BusinessUnderstanding(BaseModel):
    """A deterministic, architect-style restatement of what was asked for —
    built entirely from the already-validated SignalVector, never from a
    new LLM call."""

    stated_need: str
    problem_narrative: str
    industry: str
    use_case_type: str
    data_sensitivity: DataSensitivity
    data_modality: DataModality
    latency_requirement: LatencyRequirement
    expected_scale: ExpectedScale
    automation_level: AutomationLevel
    integration_points: list[str] = Field(default_factory=list)
    key_signals: list[str] = Field(default_factory=list)


class SecuritySummary(BaseModel):
    security_profile_name: str
    restrictiveness_rank: int
    compliance_flags: list[str] = Field(default_factory=list)
    considerations: list[str] = Field(default_factory=list)
    relevant_controls: list[BestPracticeReference] = Field(default_factory=list)


class GovernanceRecommendation(BaseModel):
    title: str
    rationale: str
    framework: Optional[str] = None
    source: Literal["policy_rule", "enterprise_knowledge"]


class RoadmapPhase(BaseModel):
    name: str
    duration: str
    goals: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ImplementationRoadmap(BaseModel):
    phases: list[RoadmapPhase] = Field(default_factory=list)
    total_timeline: str


class EvidenceConfidenceSummary(BaseModel):
    overall_confidence: int
    confidence_rationale: str
    dimension_confidence: dict[str, int] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    evidence_strength_summary: str
    best_practice_count: int
    similar_solution_count: int
    reusable_asset_count: int


class RecommendationEnrichment(BaseModel):
    business_understanding: BusinessUnderstanding
    reusable_assets: list[ReusableCatalogAsset] = Field(default_factory=list)
    similar_solutions: list[SimilarSolution] = Field(default_factory=list)
    best_practices: list[BestPracticeReference] = Field(default_factory=list)
    security_summary: SecuritySummary
    governance_recommendations: list[GovernanceRecommendation] = Field(default_factory=list)
    implementation_roadmap: ImplementationRoadmap
    evidence_confidence_summary: EvidenceConfidenceSummary


# --------------------------------------------------------------------------
# Report-level executive metrics — deterministic, core (not gated behind
# optional `enrichment`), so the header/Business Value sections always have
# something to render regardless of enrichment availability.
# --------------------------------------------------------------------------


class ImplementationReadiness(BaseModel):
    score: int
    label: str


class BusinessValueSummary(BaseModel):
    """Every field here is a grounded estimate — traced to a config table
    or an existing scoring value, never free-invented by an LLM. Ranges are
    directional, not precise forecasts; the UI labels them "(estimated)"."""

    cost_savings_estimate: str
    productivity_estimate: str
    accuracy_confidence_label: str
    timeline_estimate: str
    roi_estimate: str


class Report(BaseModel):
    mode: SubmissionMode
    signal_vector: SignalVector
    report_title: str
    one_line_summary: str
    executive_cards: ExecutiveCards
    feasibility: FeasibilityScore
    implementation_readiness: ImplementationReadiness
    architecture_recommendation: ArchitectureRecommendation
    enterprise_reuse: list[EnterpriseReuseItem]
    model_recommendation: ModelRecommendation
    workbench_recommendation: WorkbenchRecommendation
    effort_estimate: str
    timeline_estimate: str
    risks: list[Risk]
    assumptions: list[str]
    confidence_scores: ConfidenceScores
    next_best_actions: list[str]
    business_value: BusinessValueSummary
    enrichment: Optional[RecommendationEnrichment] = None
    decision_kernel: Optional["KernelReport"] = None


# --------------------------------------------------------------------------
# Decision Kernel projection — additive, optional so any caller/test that
# builds a Report without it (or against an older shape) is unaffected.
# Populated by app.kernel.orchestrator; see that module for how each field
# is derived. Kept as one nested object rather than flattened onto Report
# so the "new reasoning surface" is clearly delineated from the legacy
# fields above, which remain populated for the existing UI.
# --------------------------------------------------------------------------


class KernelReport(BaseModel):
    solution_class_id: str
    solution_class_name: str
    sufficiency: SufficiencyOutcome
    obligations: list[ObligationInstance]
    pattern_verdicts: list[PatternVerdictEntry]
    rejected_patterns: list[PatternVerdictEntry]
    precedent_findings: list[PrecedentFinding]
    sourcing_decisions: list[SourcingDecision]
    candidates: list[Candidate]
    elimination_record: list[EliminationEntry]
    recommended_candidate_id: str
    alternatives: list[Alternative]
    kernel_assumptions: list[Assumption]
    counterfactuals: list[str]
    narrative_extras: KernelNarrativeExtras
    decision_record: DecisionRecord
