import { IconAlertTriangle, IconCheckCircle, IconInfo } from "./icons";
import { severityFor } from "../lib/severity";

const ICON = { good: IconCheckCircle, warning: IconInfo, critical: IconAlertTriangle };

export default function ConfidenceBadge({ value, label }: { value: number; label?: string }) {
  const severity = severityFor(value);
  const Icon = ICON[severity];
  return (
    <span className={`badge ${severity}`}>
      <Icon width={14} height={14} strokeWidth={2} />
      {label ?? `${Math.round(value)}% confidence`}
    </span>
  );
}
