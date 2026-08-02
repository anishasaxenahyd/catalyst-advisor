import { Clock, DollarSign, Target, TrendingUp, Zap, type LucideIcon } from "lucide-react";
import type { BusinessValueSummary } from "../../types/report";

const KPIS: { key: keyof BusinessValueSummary; label: string; icon: LucideIcon }[] = [
  { key: "cost_savings_estimate", label: "Cost Savings", icon: DollarSign },
  { key: "productivity_estimate", label: "Productivity", icon: Zap },
  { key: "accuracy_confidence_label", label: "Accuracy", icon: Target },
  { key: "timeline_estimate", label: "Timeline", icon: Clock },
  { key: "roi_estimate", label: "ROI", icon: TrendingUp },
];

export default function BusinessValueKpis({ value }: { value: BusinessValueSummary }) {
  return (
    <div className="rpt-kpi-grid">
      {KPIS.map(({ key, label, icon: Icon }) => (
        <div className="rpt-kpi-card" key={key}>
          <p className="label">
            <Icon width={13} height={13} style={{ marginRight: "0.35em", verticalAlign: "-2px" }} />
            {label}
          </p>
          <p className="value">{value[key]}</p>
        </div>
      ))}
    </div>
  );
}
