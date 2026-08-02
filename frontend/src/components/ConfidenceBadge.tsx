import { AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { severityFor } from "../lib/severity";
import { confidenceLabel } from "../lib/confidenceLabel";

const SEVERITY_ICON = { good: CheckCircle2, warning: Info, critical: AlertTriangle };

// "severity" (default) is the original 3-tier good/warning/critical scheme
// used elsewhere. "confidence" is the report's 4-tier Very High/High/Good/
// Needs More Information scheme (lib/confidenceLabel.ts) — kept as an
// opt-in prop so nothing outside the report changes behavior.
export default function ConfidenceBadge({
  value,
  label,
  scheme = "severity",
}: {
  value: number;
  label?: string;
  scheme?: "severity" | "confidence";
}) {
  if (scheme === "confidence") {
    const bandLabel = confidenceLabel(value);
    const style = bandLabel === "Needs More Information" ? "warning" : "good";
    const Icon = bandLabel === "Needs More Information" ? Info : CheckCircle2;
    return (
      <span className={`rpt-badge ${style}`}>
        <Icon width={14} height={14} strokeWidth={2} />
        {label ?? `${Math.round(value)}% — ${bandLabel}`}
      </span>
    );
  }

  const severity = severityFor(value);
  const Icon = SEVERITY_ICON[severity];
  return (
    <span className={`rpt-badge ${severity}`}>
      <Icon width={14} height={14} strokeWidth={2} />
      {label ?? `${Math.round(value)}% confidence`}
    </span>
  );
}
