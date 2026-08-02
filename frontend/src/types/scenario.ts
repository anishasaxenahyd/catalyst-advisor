// Data model for pre-built demonstration scenarios (see
// docs/demo-scenario-claims-payment-integrity.md for the design spec).
// Scenario content is frontend-only static data — the "Run the AI Solution
// Advisor" button feeds `request` into the real, unmodified submit() flow.

import type { RecommendationRequest } from "./report";

export interface ScenarioStakeholder {
  role: string;
  concern: string;
}

export interface ScenarioDataset {
  name: string;
  description: string;
  columns: string[];
  rows: (string | number)[][];
}

export interface ScenarioKpi {
  label: string;
  current: string;
  target: string;
}

export interface ScenarioCapability {
  capability: string;
  maturity: "Low" | "Medium" | "High";
  notes: string;
}

export interface ScoredApproachDimensions {
  businessFit: number;
  implementationComplexity: number;
  security: number;
  compliance: number;
  scalability: number;
  cost: number;
  timeToValue: number;
}

export interface ScoredApproach {
  name: string;
  description: string;
  pros: string[];
  cons: string[];
  scores: ScoredApproachDimensions;
}

export interface Scenario {
  id: string;
  title: string;
  tagline: string;
  businessBackground: string;
  currentProcess: string[];
  painPoints: string[];
  businessObjectives: string[];
  stakeholders: ScenarioStakeholder[];
  technologyLandscape: string[];
  datasets: ScenarioDataset[];
  kpiBaseline: ScenarioKpi[];
  capabilityAssessment: ScenarioCapability[];
  approaches: ScoredApproach[];
  recommendedApproach: string;
  recommendationRationale: string;
  investmentEstimate: string;
  request: RecommendationRequest;
}
