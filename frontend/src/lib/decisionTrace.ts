// The backend's DecisionTrace.evidence is a flat string[] with two shapes
// depending on which recommendation produced it (see backend/app/engine/
// trace.py vs workbench_selector.py) — this is the existing API contract,
// unchanged by Phase 3, just parsed here for display.
//
//   "technical_fit=100.0/100"        — a dimension score (pattern/model traces)
//   "signal.data_sensitivity=phi"    — a plain fact (workbench trace)

export interface ParsedScoreEvidence {
  dimension: string;
  value: number;
}

const SCORE_PATTERN = /^([a-z_]+)=(-?[\d.]+)\/100$/;

export function parseEvidence(evidence: string[]): { scores: ParsedScoreEvidence[]; facts: string[] } {
  const scores: ParsedScoreEvidence[] = [];
  const facts: string[] = [];
  for (const item of evidence) {
    const match = item.match(SCORE_PATTERN);
    if (match) {
      scores.push({ dimension: match[1], value: parseFloat(match[2]) });
    } else {
      facts.push(item);
    }
  }
  return { scores, facts };
}
