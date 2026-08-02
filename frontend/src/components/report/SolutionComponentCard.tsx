import { Bot, Cloud, Layers, Server, type LucideIcon } from "lucide-react";
import type { EnterpriseReuseItem } from "../../types/report";
import { formatAssetCategory } from "../../lib/catalogLabels";

const CATEGORY_ICON: Record<string, LucideIcon> = {
  skill: Layers,
  mcp_server: Server,
  agent: Bot,
  api: Cloud,
};

export default function SolutionComponentCard({ items }: { items: EnterpriseReuseItem[] }) {
  return (
    <div className="rpt-component-grid">
      {items.map((item) => {
        const Icon = CATEGORY_ICON[item.asset.category] ?? Layers;
        return (
          <div className="rpt-component-card" key={item.asset.id}>
            <span className="icon-badge">
              <Icon width={18} height={18} />
            </span>
            <div className="body">
              <p className="name">{item.asset.name}</p>
              <p className="tech">{formatAssetCategory(item.asset.category)}</p>
              <p className="purpose">{item.asset.description}</p>
              <p className="reason">
                <span className="field-label">Why: </span>
                {item.rationale}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
