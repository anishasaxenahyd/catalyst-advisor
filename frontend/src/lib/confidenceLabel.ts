// Mirrors backend/app/engine/confidence_bands.py exactly — same thresholds,
// same labels, so "Very High"/"High"/"Good"/"Needs More Information" never
// mean different things depending on which side computed them.

export function confidenceLabel(score: number): string {
  if (score >= 95) return "Very High";
  if (score >= 90) return "High";
  if (score >= 80) return "Good";
  return "Needs More Information";
}

const MEANING: Record<string, string> = {
  "Very High": "Strong evidence behind this recommendation — safe to proceed as-is.",
  High: "Solid evidence behind this recommendation, with minor gaps worth a quick check.",
  Good: "Reasonable evidence, but a few assumptions should be confirmed before committing.",
  "Needs More Information": "Key details were missing or defaulted — validate with stakeholders before proceeding.",
};

export function confidenceMeaning(score: number): string {
  return MEANING[confidenceLabel(score)];
}
