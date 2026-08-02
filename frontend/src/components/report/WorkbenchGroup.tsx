import { Cloud, Cpu, Database, Eye, Shield } from "lucide-react";
import type { AIModel, GovernanceRecommendation, WorkbenchRecommendation } from "../../types/report";

export default function WorkbenchGroup({
  workbench,
  primaryModel,
  governance,
}: {
  workbench: WorkbenchRecommendation;
  primaryModel: AIModel;
  governance?: GovernanceRecommendation[];
}) {
  const monitoringDetail =
    governance && governance.length > 0
      ? governance.map((g) => g.title).join("; ")
      : "Standard audit logging and runtime observability enabled per the selected security profile.";

  const groups = [
    {
      key: "ai-models",
      icon: Cpu,
      label: "AI Models",
      value: `${primaryModel.name} on ${workbench.compute_profile.name}`,
      detail: workbench.reasons.compute ?? workbench.compute_profile.description,
    },
    {
      key: "knowledge-sources",
      icon: Database,
      label: "Knowledge Sources",
      value: workbench.workspace_tier.name,
      detail: workbench.reasons.workspace ?? workbench.workspace_tier.description,
    },
    {
      key: "security",
      icon: Shield,
      label: "Security",
      value: workbench.security_profile.name,
      detail: [workbench.reasons.security, workbench.security_profile.compliance_flags.join(", ")]
        .filter(Boolean)
        .join(" — "),
    },
    {
      key: "deployment",
      icon: Cloud,
      label: "Deployment",
      value: workbench.deployment_targets.map((d) => d.name).join(", ") || "—",
      detail: workbench.reasons.deployment ?? "",
    },
    {
      key: "monitoring",
      icon: Eye,
      label: "Monitoring",
      value: "Audit & Observability",
      detail: monitoringDetail,
    },
  ];

  return (
    <div className="rpt-workbench-grid">
      {groups.map((group) => (
        <div className="rpt-workbench-card" key={group.key}>
          <p className="label">
            <group.icon width={14} height={14} />
            {group.label}
          </p>
          <p className="value">{group.value}</p>
          {group.detail && <p className="detail">{group.detail}</p>}
        </div>
      ))}
    </div>
  );
}
