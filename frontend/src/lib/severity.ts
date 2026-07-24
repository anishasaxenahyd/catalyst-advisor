// Shared severity banding for anything scored 0-100 (confidence, dimension
// scores). Status colors are fixed and never reused for anything else —
// see index.css --good/--warning/--critical.

export type Severity = "good" | "warning" | "critical";

export function severityFor(value: number): Severity {
  if (value >= 70) return "good";
  if (value >= 40) return "warning";
  return "critical";
}

export const SEVERITY_COLOR_VAR: Record<Severity, string> = {
  good: "var(--good)",
  warning: "var(--warning)",
  critical: "var(--critical)",
};

export function formatDimensionLabel(dimension: string): string {
  return dimension
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
