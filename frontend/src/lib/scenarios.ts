// Pre-built demonstration scenario content. Fully synthetic/fictional —
// no real payer data, PHI, or proprietary workflows. See
// docs/demo-scenario-claims-payment-integrity.md for the design spec this
// was transcribed from.

import type { Scenario } from "../types/scenario";

export const CLAIMS_PAYMENT_INTEGRITY_SCENARIO: Scenario = {
  id: "claims-payment-integrity",
  title: "Claims Payment Integrity Advisor",
  tagline: "Prioritize the claims worth investigating, not just the ones you have time for.",

  businessBackground:
    "A large national health payer processes millions of medical, behavioral, and ancillary claims every month. " +
    "A dedicated Payment Integrity team of claims investigators reviews a subset of paid and pending claims for " +
    "duplicate billing, upcoding/unbundling, and other overpayment risk — but review coverage is capped by manual " +
    "investigator capacity, not by claim volume.",

  currentProcess: [
    "Claims flow from the core claims adjudication platform into a nightly extract for the Payment Integrity team.",
    "Investigators manually query multiple systems — claims history, provider network file, prior investigation notes — to check a sampled claim.",
    "Investigators cross-reference procedure/diagnosis code combinations against known billing-anomaly patterns from memory and spreadsheets.",
    "Suspected claims are escalated to a senior investigator for manual case-file assembly.",
    "Confirmed overpayments route to the recovery team; findings are logged in a shared tracker, not systematically fed back into future targeting.",
    "Investigation coverage is sampling-based and capped by team size, not comprehensive.",
  ],

  painPoints: [
    "Only ~4% of paid claims receive any payment-integrity review each month.",
    "Average investigation takes 6.5 business days from flag to disposition.",
    "Investigators spend an estimated 40% of their time gathering data across systems rather than analyzing it.",
    "False-positive rate on manually-flagged claims runs near 35%.",
    "Dollars recovered per investigator-hour has plateaued for several quarters.",
    "No systematic way to prioritize the highest-risk claims first — review order is largely FIFO.",
  ],

  businessObjectives: [
    "Increase payment-integrity review coverage from ~4% to 100% of paid claims via automated risk scoring.",
    "Reduce average investigation turnaround from 6.5 days to under 2 days for prioritized cases.",
    "Reduce false-positive rate on escalated cases from ~35% to under 15%.",
    "Increase dollars protected per investigator-hour by at least 30% within two quarters of rollout.",
    "Maintain a full explainability/audit trail for every flagged claim, to support appeals and regulatory review.",
  ],

  stakeholders: [
    { role: "VP, Payment Integrity", concern: "Owns the investigator team and recovery targets" },
    { role: "Director, Special Investigations Unit", concern: "Oversees fraud/abuse escalations" },
    { role: "Chief Compliance Officer", concern: "Regulatory and audit accountability" },
    { role: "CIO / Chief Digital Officer", concern: "Technology investment sponsor" },
    { role: "VP, Claims Operations", concern: "Owns the core claims platform and data feeds" },
    { role: "Actuarial / Finance Lead", concern: "Validates dollars-protected methodology and ROI" },
    { role: "Provider Network Relations Lead", concern: "Manages provider-facing impact of flagged claims and appeals" },
  ],

  technologyLandscape: [
    "Core claims adjudication platform (Facets-class)",
    "Enterprise data warehouse (Snowflake-class)",
    "Provider network and credentialing system",
    "Investigation tracking (spreadsheet-based today, no dedicated system)",
    "Enterprise SSO / identity and access management",
    "EDI clearinghouse for claims intake (Availity-class)",
    "BI / reporting layer for monthly payment-integrity metrics (Power BI-class)",
  ],

  datasets: [
    {
      name: "Sample Claims",
      description: "A representative slice of paid, pending, and denied claims with a preliminary risk score.",
      columns: ["Claim ID", "Member ID", "Provider ID", "Procedure Code", "Diagnosis Code", "Billed", "Paid", "Status", "Risk Score"],
      rows: [
        ["CLM-100234", "MBR-58291", "PRV-1042", "99213", "E11.9", "$185", "$142", "Paid", 82],
        ["CLM-100235", "MBR-58292", "PRV-2077", "99214", "M54.5", "$220", "$198", "Paid", 45],
        ["CLM-100236", "MBR-58293", "PRV-1042", "99213", "E11.9", "$185", "$185", "Paid", 91],
        ["CLM-100237", "MBR-58294", "PRV-3310", "20610", "M17.11", "$410", "$340", "Paid", 28],
        ["CLM-100238", "MBR-58295", "PRV-2077", "99215", "F41.1", "$265", "$265", "Pending", 63],
        ["CLM-100239", "MBR-58296", "PRV-4521", "97110", "M25.561", "$95", "$76", "Paid", 12],
        ["CLM-100240", "MBR-58297", "PRV-1042", "99214", "E11.9", "$220", "$220", "Paid", 88],
        ["CLM-100241", "MBR-58298", "PRV-3310", "20610", "M17.12", "$410", "$410", "Paid", 34],
        ["CLM-100242", "MBR-58299", "PRV-5190", "99213", "J06.9", "$150", "$120", "Denied", 5],
      ],
    },
    {
      name: "Sample Providers",
      description: "Provider organizations referenced by the sample claims above, with recent volume and flag history.",
      columns: ["Provider ID", "Provider Org", "Specialty", "Network Status", "30-Day Claims", "Prior Flags"],
      rows: [
        ["PRV-1042", "Provider Org 1042", "Internal Medicine", "In-Network", 340, 3],
        ["PRV-2077", "Provider Org 2077", "Behavioral Health", "In-Network", 210, 1],
        ["PRV-3310", "Provider Org 3310", "Orthopedics", "In-Network", 165, 5],
        ["PRV-4521", "Provider Org 4521", "Physical Therapy", "In-Network", 480, 0],
        ["PRV-5190", "Provider Org 5190", "Urgent Care", "Out-of-Network", 95, 2],
        ["PRV-6003", "Provider Org 6003", "Internal Medicine", "In-Network", 275, 0],
        ["PRV-7188", "Provider Org 7188", "Cardiology", "In-Network", 140, 4],
        ["PRV-8244", "Provider Org 8244", "Behavioral Health", "In-Network", 190, 1],
      ],
    },
    {
      name: "Sample Investigation Outcomes",
      description: "Recent case dispositions, used to calibrate false-positive rate and dollars recovered.",
      columns: ["Case ID", "Claim ID", "Flag Reason", "Disposition", "Recovered", "Days to Disposition"],
      rows: [
        ["CASE-4401", "CLM-100234", "Upcoding pattern", "Confirmed overpayment", "$43", 2],
        ["CASE-4402", "CLM-100237", "Unbundling", "Confirmed overpayment", "$70", 3],
        ["CASE-4403", "CLM-100240", "Duplicate billing", "False positive", "$0", 1],
        ["CASE-4404", "CLM-100241", "Upcoding pattern", "Under review", "$0", 5],
        ["CASE-4405", "CLM-100238", "Frequency anomaly", "Confirmed overpayment", "$28", 4],
        ["CASE-4406", "CLM-100242", "Denied claim reopened", "False positive", "$0", 1],
        ["CASE-4407", "CLM-100235", "Coding mismatch", "Confirmed overpayment", "$19", 2],
        ["CASE-4408", "CLM-100239", "Frequency anomaly", "False positive", "$0", 2],
      ],
    },
  ],

  kpiBaseline: [
    { label: "Claims reviewed for payment integrity (monthly)", current: "4%", target: "100%" },
    { label: "Average investigation turnaround", current: "6.5 days", target: "< 2 days" },
    { label: "False-positive rate on escalated cases", current: "35%", target: "< 15%" },
    { label: "Dollars protected per investigator-hour", current: "$410", target: "$550+" },
    { label: "Investigator time spent on data-gathering", current: "~40%", target: "< 15%" },
  ],

  capabilityAssessment: [
    {
      capability: "Claims Data Integration & Accessibility",
      maturity: "Medium",
      notes: "Data exists in the warehouse but requires manual multi-system querying.",
    },
    {
      capability: "AI/ML Operations Maturity",
      maturity: "Low",
      notes: "No production ML models in the payment-integrity function today.",
    },
    {
      capability: "Investigation Case Management",
      maturity: "Low",
      notes: "Spreadsheet-based tracking, no structured case system.",
    },
    {
      capability: "Data Governance & Explainability",
      maturity: "Medium",
      notes: "Strong audit culture, but no explainability tooling for automated flags yet.",
    },
    {
      capability: "Change Management / Investigator Enablement",
      maturity: "Medium",
      notes: "Team is receptive to tooling, with limited AI-assisted-workflow experience.",
    },
  ],

  approaches: [
    {
      name: "Batch Risk-Scoring & Prioritization Pipeline",
      description:
        "A nightly batch job scores every paid and pending claim for duplicate-billing, upcoding, and coding-anomaly risk, " +
        "surfacing a prioritized investigation queue instead of a small random sample.",
      pros: [
        "Fastest to value — directly solves the 4%-coverage gap at enterprise scale",
        "Lower implementation complexity: a well-understood batch classification pattern",
        "Scales cleanly to full claim volume without added investigator headcount",
      ],
      cons: [
        "Less rich per-claim explanation than an agentic copilot unless paired with a narrative-generation step",
        "Doesn't reduce investigator research time on the cases it flags",
      ],
      scores: { businessFit: 9, implementationComplexity: 8, security: 8, compliance: 8, scalability: 9, cost: 8, timeToValue: 9 },
    },
    {
      name: "Agentic Investigation Copilot (Human-in-the-loop)",
      description:
        "An agent gathers claim, provider, and history context for a case, drafts a risk narrative and recommended action, " +
        "and an investigator approves or escalates.",
      pros: [
        "Highest investigator trust and adoption — explains its reasoning",
        "Directly reduces the 40% of time spent on data-gathering",
      ],
      cons: [
        "More complex to build and orchestrate than a scoring pipeline",
        "Slower time-to-value than a batch approach",
      ],
      scores: { businessFit: 8, implementationComplexity: 5, security: 8, compliance: 8, scalability: 7, cost: 6, timeToValue: 6 },
    },
    {
      name: "Rules Engine Augmented with LLM Case Summarization",
      description:
        "The existing rules-based flagging logic stays in place; an LLM drafts a case summary for each flagged claim to speed up investigator review.",
      pros: [
        "Builds on the team's existing rules-engine investment",
        "Lower change-management lift than a new scoring model",
      ],
      cons: [
        "Inherits the existing rules engine's blind spots — won't catch novel anomaly patterns",
        "Doesn't meaningfully close the coverage gap",
      ],
      scores: { businessFit: 6, implementationComplexity: 7, security: 7, compliance: 7, scalability: 6, cost: 7, timeToValue: 7 },
    },
  ],
  recommendedApproach: "Batch Risk-Scoring & Prioritization Pipeline",
  recommendationRationale:
    "The batch scoring pipeline is recommended as the foundational phase: it has the fastest time-to-value, directly " +
    "closes the coverage gap at enterprise scale, and carries the lowest implementation complexity of the three options. " +
    "The Agentic Investigation Copilot is a natural phase-2 extension once the scoring pipeline is in production and " +
    "generating a reliable prioritized queue for it to work from.",

  investmentEstimate:
    "$650K-$950K (Year 1: risk-scoring pipeline, data integration, investigator workflow tooling, and change management) " +
    "— a follow-on agentic-copilot phase is a separate future investment.",

  request: {
    mode: "idea",
    description:
      "A batch AI pipeline that analyzes historical and incoming claims for a national health payer's Payment Integrity " +
      "team. It integrates with the claims data warehouse to retrieve claims records and classify every paid and " +
      "pending claim — across hundreds of thousands of claims each month — for duplicate-billing, upcoding, and " +
      "coding-anomaly risk, explaining the contributing risk factors, and producing a prioritized investigation queue " +
      "so investigators work highest-risk claims first instead of a small random sample.",
    hints: {
      industry: "Healthcare",
      data_sensitivity: "phi",
      expected_scale: "enterprise",
      automation_level: "assist",
    },
  },
};

export const SCENARIOS: Scenario[] = [CLAIMS_PAYMENT_INTEGRITY_SCENARIO];

export function getScenario(id: string): Scenario | undefined {
  return SCENARIOS.find((s) => s.id === id);
}
