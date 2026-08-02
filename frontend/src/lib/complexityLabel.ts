// Trivial presentational banding of the 1-5 complexity_tier already exposed
// by the backend — no backend round-trip needed for a linear 4-bucket split.

export function complexityLabel(tier: number): string {
  if (tier <= 2) return "Low";
  if (tier === 3) return "Medium";
  if (tier === 4) return "High";
  return "Very High";
}
