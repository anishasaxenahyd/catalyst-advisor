import type { ScenarioKpi } from "../../types/scenario";
import { IconArrowRight } from "../icons";

export default function KpiComparisonGrid({ kpis }: { kpis: ScenarioKpi[] }) {
  return (
    <div className="kpi-grid">
      {kpis.map((kpi) => (
        <div className="kpi-tile" key={kpi.label}>
          <div className="label">{kpi.label}</div>
          <div className="values">
            <span className="current">{kpi.current}</span>
            <IconArrowRight width={14} height={14} className="arrow" />
            <span className="target">{kpi.target}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
