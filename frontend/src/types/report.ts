// Mirrors backend/app/models/schemas.py. Kept hand-in-sync for Phase 0;
// generating this from the FastAPI OpenAPI schema is a fine later upgrade.

export type DataSensitivity = "none" | "pii" | "phi";
export type DataModality = "text" | "image" | "structured" | "mixed";
export type LatencyRequirement = "batch" | "near_realtime" | "realtime";
export type ExpectedScale = "pilot" | "department" | "enterprise";
export type AutomationLevel = "assist" | "copilot" | "autonomous";
export type SubmissionMode = "idea" | "design_review";
export type RelativeLevel = "low" | "medium" | "high";

export interface StructuredHints {
  industry?: string | null;
  data_sensitivity?: DataSensitivity | null;
  expected_scale?: ExpectedScale | null;
  automation_level?: AutomationLevel | null;
}

export interface RecommendationRequest {
  mode: SubmissionMode;
  description: string;
  diagram_text?: string | null;
  diagram_filename?: string | null;
  hints: StructuredHints;
}

// Prompt optimizer (pre-submission, advisory only — never touches scoring)
export interface QAExchange {
  field: string;
  question: string;
  answer: string;
}

export interface PromptOptimizationRequest {
  mode: SubmissionMode;
  description: string;
  diagram_text?: string | null;
  hints: StructuredHints;
  prior_answers: QAExchange[];
}

export interface ClarifyingQuestion {
  field: string;
  question: string;
}

export interface PromptOptimizationResult {
  optimized_text: string;
  original_token_estimate: number;
  optimized_token_estimate: number;
  gaps: string[];
  clarifying_questions: ClarifyingQuestion[];
  notes: string;
}

export type FieldProvenance = "user" | "llm" | "default";

export interface ValidationWarning {
  field: string;
  original_value?: string | null;
  corrected_value?: string | null;
  reason: string;
}

export interface SignalVector {
  use_case_type: string;
  industry: string;
  data_sensitivity: DataSensitivity;
  data_modality: DataModality;
  latency_requirement: LatencyRequirement;
  expected_scale: ExpectedScale;
  automation_level: AutomationLevel;
  integration_points: string[];
  tags: string[];
  field_provenance: Record<string, FieldProvenance>;
  validation_warnings: ValidationWarning[];
}

export interface AIModel {
  id: string;
  name: string;
  family: string;
  modality: string[];
  context_window: number;
  cost_tier: number;
  latency_tier: number;
  compliance: string[];
  suitable_for_tags: string[];
  scale_ceiling: ExpectedScale;
  strengths: string[];
  weaknesses: string[];
  description: string;
  is_primary_candidate: boolean;
}

export interface ArchitecturePattern {
  id: string;
  name: string;
  description: string;
  complexity_tier: number;
  suitable_for_tags: string[];
  scale_ceiling: ExpectedScale;
  mermaid_template: string;
}

export interface EnterpriseAsset {
  id: string;
  category: "skill" | "mcp_server" | "agent" | "api";
  name: string;
  description: string;
  tags: string[];
  reuse_score: number;
  compliance: string[];
}

export interface SecurityProfile {
  id: string;
  name: string;
  description: string;
  allowed_data_sensitivity: DataSensitivity[];
  compliance_flags: string[];
  restrictiveness_rank: number;
}

export interface WorkspaceTier {
  id: string;
  name: string;
  description: string;
  compatible_security_profiles: string[];
}

export interface ComputeProfile {
  id: string;
  name: string;
  description: string;
  suitable_scale: ExpectedScale[];
  suitable_cost_tiers: number[];
  cost_tier: number;
}

export interface DeploymentTarget {
  id: string;
  name: string;
  description: string;
  supports_compliance_flags: string[];
}

export interface AlternativeConsidered {
  id: string;
  name: string;
  score: number;
  why_lower: string;
}

export interface DecisionTrace {
  selected: string;
  why_selected: string;
  alternatives_considered: AlternativeConsidered[];
  assumptions: string[];
  confidence: number;
  evidence: string[];
  missing_information: string[];
  validation_warnings: string[];
  confidence_rationale: string;
}

export interface ArchitectureRecommendation {
  pattern: ArchitecturePattern;
  rationale: string;
  decision_trace: DecisionTrace;
}

export interface ModelAlternative {
  model: AIModel;
  rationale: string;
  trade_off: string;
  relative_cost: RelativeLevel;
}

export interface ModelRecommendation {
  primary: AIModel;
  primary_rationale: string;
  alternatives: ModelAlternative[];
  relative_cost: RelativeLevel;
  relative_latency: RelativeLevel;
  suitability_rationale: string;
  decision_trace: DecisionTrace;
}

export interface EnterpriseReuseItem {
  asset: EnterpriseAsset;
  rationale: string;
}

export interface WorkbenchRecommendation {
  workspace_tier: WorkspaceTier;
  compute_profile: ComputeProfile;
  security_profile: SecurityProfile;
  deployment_targets: DeploymentTarget[];
  reasons: Record<string, string>;
  decision_trace: DecisionTrace;
}

export interface FeasibilityScore {
  technical: number;
  business: number;
}

export interface ConfidenceScores {
  overall: number;
  architecture: number;
  model: number;
  workbench: number;
}

// Enterprise context enrichment (AI Catalog, Solution Registry, Enterprise
// Knowledge Platform) — additive, optional on Report.
export interface ReusableCatalogAsset {
  id: string;
  name: string;
  asset_type: string;
  description: string;
  rationale: string;
}

export interface SimilarSolution {
  id: string;
  title: string;
  industry: string;
  architecture_pattern_name: string;
  business_outcome: string;
  lessons_learned: string[];
  security_considerations: string[];
  rationale: string;
}

export interface BestPracticeReference {
  id: string;
  title: string;
  vendor: string;
  category: string;
  summary: string;
  reference: string;
}

export interface BusinessUnderstanding {
  stated_need: string;
  problem_narrative: string;
  industry: string;
  use_case_type: string;
  data_sensitivity: DataSensitivity;
  data_modality: DataModality;
  latency_requirement: LatencyRequirement;
  expected_scale: ExpectedScale;
  automation_level: AutomationLevel;
  integration_points: string[];
  key_signals: string[];
}

export interface SecuritySummary {
  security_profile_name: string;
  restrictiveness_rank: number;
  compliance_flags: string[];
  considerations: string[];
  relevant_controls: BestPracticeReference[];
}

export interface GovernanceRecommendation {
  title: string;
  rationale: string;
  framework?: string | null;
  source: "policy_rule" | "enterprise_knowledge";
}

export interface RoadmapPhase {
  name: string;
  duration: string;
  goals: string[];
  deliverables: string[];
  risks: string[];
}

export interface ImplementationRoadmap {
  phases: RoadmapPhase[];
  total_timeline: string;
}

export interface EvidenceConfidenceSummary {
  overall_confidence: number;
  confidence_rationale: string;
  dimension_confidence: Record<string, number>;
  missing_information: string[];
  validation_warnings: string[];
  evidence_strength_summary: string;
  best_practice_count: number;
  similar_solution_count: number;
  reusable_asset_count: number;
}

export interface RecommendationEnrichment {
  business_understanding: BusinessUnderstanding;
  reusable_assets: ReusableCatalogAsset[];
  similar_solutions: SimilarSolution[];
  best_practices: BestPracticeReference[];
  security_summary: SecuritySummary;
  governance_recommendations: GovernanceRecommendation[];
  implementation_roadmap: ImplementationRoadmap;
  evidence_confidence_summary: EvidenceConfidenceSummary;
}

// Report-level executive metrics — deterministic, always present regardless
// of whether `enrichment` is populated.
export interface RiskItem {
  risk: string;
  impact: RelativeLevel;
  likelihood: RelativeLevel;
  mitigation: string;
}

export interface Risk extends RiskItem {
  status: string;
}

export interface ExecutiveCards {
  problem: string;
  opportunity: string;
  recommended_pattern: string;
  expected_outcome: string;
}

export interface ImplementationReadiness {
  score: number;
  label: string;
}

export interface BusinessValueSummary {
  cost_savings_estimate: string;
  productivity_estimate: string;
  accuracy_confidence_label: string;
  timeline_estimate: string;
  roi_estimate: string;
}

export interface Report {
  mode: SubmissionMode;
  signal_vector: SignalVector;
  report_title: string;
  one_line_summary: string;
  executive_cards: ExecutiveCards;
  feasibility: FeasibilityScore;
  implementation_readiness: ImplementationReadiness;
  architecture_recommendation: ArchitectureRecommendation;
  enterprise_reuse: EnterpriseReuseItem[];
  model_recommendation: ModelRecommendation;
  workbench_recommendation: WorkbenchRecommendation;
  effort_estimate: string;
  timeline_estimate: string;
  risks: Risk[];
  assumptions: string[];
  confidence_scores: ConfidenceScores;
  next_best_actions: string[];
  business_value: BusinessValueSummary;
  enrichment?: RecommendationEnrichment | null;
  decision_kernel?: KernelReport | null;
}

// ---------------------------------------------------------------------
// Decision Kernel — the staged reasoning trail (see backend app/kernel/).
// Additive and optional: an older/mock Report is still fully renderable
// without this section.
// ---------------------------------------------------------------------

export type SufficiencyStatus = "PROCEED" | "PROCEED_WITH_QUESTIONS" | "HALT_CLARIFY";

export interface Clarification {
  field_or_signature: string;
  question: string;
  decision_critical: boolean;
}

export interface SufficiencyOutcome {
  status: SufficiencyStatus;
  blocking_questions: Clarification[];
  advisory_questions: Clarification[];
  rationale: string;
}

export interface ObligationInstance {
  id: string;
  title: string;
  source: string;
  mandates_capabilities: string[];
  rationale: string;
}

export type PatternVerdict = "REQUIRED" | "APPLICABLE" | "CONDITIONAL" | "UNNECESSARY" | "CONTRA_INDICATED";

export interface PatternVerdictEntry {
  pattern_id: string;
  pattern_name: string;
  pattern_type: "solution" | "assurance";
  verdict: PatternVerdict;
  reason: string;
  matched_indications: string[];
  matched_contra_indications: string[];
}

export interface PrecedentFinding {
  solution_id: string;
  title: string;
  evidence_class: string;
  similarity_basis: string[];
  transferable: boolean;
  conditions: string[];
  divergences: string[];
  lesson_summary: string;
  usage: "transferable_decision_evidence" | "feasibility_evidence" | "hazard_evidence";
}

export type SourcingOutcome = "reuse" | "compose" | "extend" | "buy" | "build" | "defer";

export interface SourcingDecision {
  capability_id: string;
  capability_name: string;
  decision: SourcingOutcome;
  justification: string;
  rejected_alternatives: string[];
  asset_ref?: string | null;
}

export interface Candidate {
  id: string;
  label: string;
  description: string;
  pattern_ids: string[];
  complexity_score: number;
}

export interface EliminationEntry {
  candidate_id: string;
  candidate_label: string;
  gate: string;
  rule_id: string;
  evidence: string;
}

export interface Alternative {
  candidate_id: string;
  label: string;
  governing_priority: string;
  what_is_given_up: string;
  switching_cost: string;
  revisit_trigger: string;
}

export interface AlternativeNarrative {
  candidate_id: string;
  narrative: string;
}

export interface KernelNarrativeExtras {
  rejected_options_narrative: string;
  sourcing_narrative: string;
  alternatives_narrative: AlternativeNarrative[];
  counterfactuals: string[];
}

export interface KernelReport {
  solution_class_id: string;
  solution_class_name: string;
  sufficiency: SufficiencyOutcome;
  obligations: ObligationInstance[];
  pattern_verdicts: PatternVerdictEntry[];
  rejected_patterns: PatternVerdictEntry[];
  precedent_findings: PrecedentFinding[];
  sourcing_decisions: SourcingDecision[];
  candidates: Candidate[];
  elimination_record: EliminationEntry[];
  recommended_candidate_id: string;
  alternatives: Alternative[];
  kernel_assumptions: { id: string; statement: string; field: string }[];
  counterfactuals: string[];
  narrative_extras: KernelNarrativeExtras;
}
