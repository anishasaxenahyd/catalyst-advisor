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

export interface Report {
  mode: SubmissionMode;
  signal_vector: SignalVector;
  executive_summary: string;
  feasibility: FeasibilityScore;
  architecture_recommendation: ArchitectureRecommendation;
  enterprise_reuse: EnterpriseReuseItem[];
  model_recommendation: ModelRecommendation;
  workbench_recommendation: WorkbenchRecommendation;
  effort_estimate: string;
  timeline_estimate: string;
  risks: string[];
  assumptions: string[];
  confidence_scores: ConfidenceScores;
  next_best_actions: string[];
  enrichment?: RecommendationEnrichment | null;
}
