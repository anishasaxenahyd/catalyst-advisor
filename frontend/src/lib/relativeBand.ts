// Mirrors backend/data/config/decision_rules.json's relative_cost_bands /
// relative_latency_bands exactly ({"low": [1,2], "medium": [3], "high": [4,5]}).
// Used only to band an alternative model's raw latency_tier client-side,
// since the backend only computes relative_latency for the primary model.

import type { RelativeLevel } from "../types/report";

export function relativeBand(tier: number): RelativeLevel {
  if (tier <= 2) return "low";
  if (tier === 3) return "medium";
  return "high";
}
