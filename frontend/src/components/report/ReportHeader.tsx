import { Printer, RefreshCw, Sparkles } from "lucide-react";
import type { Report } from "../../types/report";
import { complexityLabel } from "../../lib/complexityLabel";

export default function ReportHeader({
  report,
  onPrint,
  onReset,
}: {
  report: Report;
  onPrint: () => void;
  onReset: () => void;
}) {
  const date = new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });

  return (
    <div className="rpt-header">
      <div className="rpt-header-main">
        <p className="rpt-eyebrow">
          <Sparkles width={14} height={14} />
          Executive Report
        </p>
        <h1>{report.report_title}</h1>
        <p className="rpt-one-line-summary">{report.one_line_summary}</p>
        <div className="rpt-meta-row">
          <span className="rpt-meta-pill">
            Date: <span className="value">{date}</span>
          </span>
          <span className="rpt-meta-pill">
            Complexity:{" "}
            <span className="value">
              {complexityLabel(report.architecture_recommendation.pattern.complexity_tier)}
            </span>
          </span>
          <span className="rpt-meta-pill">
            Implementation Readiness: <span className="value">{report.implementation_readiness.label}</span>
          </span>
        </div>
      </div>
      <div className="rpt-actions">
        <button type="button" className="rpt-btn" onClick={onPrint}>
          <Printer width={16} height={16} />
          Export / Print
        </button>
        <button type="button" className="rpt-btn" onClick={onReset}>
          <RefreshCw width={16} height={16} />
          Start over
        </button>
      </div>
    </div>
  );
}
