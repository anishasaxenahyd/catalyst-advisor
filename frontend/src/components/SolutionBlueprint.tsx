import { useEffect, useMemo, useRef, useState, type ComponentType, type SVGProps } from "react";
import type { Report } from "../types/report";
import {
  buildBlueprint,
  computeLayout,
  computeZoneRects,
  type BlueprintEdge,
  type BlueprintNode,
  type NodeKind,
} from "../lib/blueprint";
import {
  User,
  Lock,
  Route,
  Sparkles,
  Layers,
  Cpu,
  FileText,
  Database,
  Server,
  Cloud,
  CheckCircle2,
  Eye,
  ChevronRight,
} from "lucide-react";

const KIND_ICON: Record<NodeKind, ComponentType<SVGProps<SVGSVGElement>>> = {
  user: User,
  auth: Lock,
  api_gateway: Route,
  ai_gateway: Route,
  agent: Sparkles,
  skill: Layers,
  model: Cpu,
  prompt: FileText,
  vector_store: Database,
  mcp_server: Server,
  api: Cloud,
  database: Database,
  system: Cloud,
  human: User,
  audit: Eye,
  monitoring: Eye,
  output: CheckCircle2,
};

// Five legend categories the redesign asks for — every NodeKind maps to
// exactly one, so the legend never has more entries than a reader can scan.
type NodeCategory = "app" | "ai" | "data" | "security" | "external";

const KIND_CATEGORY: Record<NodeKind, NodeCategory> = {
  user: "app",
  api_gateway: "app",
  output: "app",
  ai_gateway: "ai",
  agent: "ai",
  skill: "ai",
  model: "ai",
  prompt: "ai",
  vector_store: "ai",
  database: "data",
  mcp_server: "data",
  api: "data",
  auth: "security",
  audit: "security",
  human: "security",
  monitoring: "security",
  system: "external",
};

const CATEGORY_LABEL: Record<NodeCategory, string> = {
  app: "App",
  ai: "AI",
  data: "Data",
  security: "Security",
  external: "External Systems",
};

type ViewId = "solution" | "security" | "ai" | "dataflow";

const VIEWS: { id: ViewId; label: string; help: string }[] = [
  { id: "solution", label: "Solution Architecture", help: "Every component, connection, and enterprise system in this recommendation." },
  { id: "security", label: "Security View", help: "Where authentication, authorization, sensitive data, and audit logging happen." },
  { id: "ai", label: "AI Components", help: "Just the AI Catalog components — agents, skills, connectors, and the model." },
  { id: "dataflow", label: "Data Flow", help: "The primary request path, from user to response." },
];

function edgePath(from: { x: number; y: number; width: number; height: number }, to: { x: number; y: number; width: number; height: number }): string {
  const x1 = from.x + from.width;
  const y1 = from.y + from.height / 2;
  const x2 = to.x;
  const y2 = to.y + to.height / 2;

  // Same-column edges (e.g. a bidirectional pair like Identity <-> API
  // Gateway) have x2 < x1, which makes the default midpoint bezier loop
  // back through the nodes themselves and cross a same-column reverse
  // edge. Bow those out to the right instead of through the nodes, and
  // give the upward/downward direction a different bow depth so the two
  // arcs run parallel instead of crossing each other.
  if (from.x === to.x) {
    const bowX = x1 + (from.y > to.y ? 30 : 48);
    return `M ${x1} ${y1} C ${bowX} ${y1}, ${bowX} ${y2}, ${x2} ${y2}`;
  }

  const midX = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
}

export default function SolutionBlueprint({ report }: { report: Report }) {
  const blueprint = useMemo(() => buildBlueprint(report), [report]);
  const layout = useMemo(() => computeLayout(blueprint.nodes), [blueprint]);
  const zoneRects = useMemo(() => computeZoneRects(blueprint.nodes, layout), [blueprint, layout]);
  const nodeById = useMemo(() => new Map(blueprint.nodes.map((n) => [n.id, n])), [blueprint]);
  const primaryNodeIds = useMemo(() => {
    const ids = new Set<string>();
    blueprint.edges.forEach((e) => {
      if (e.tags.includes("primary")) {
        ids.add(e.from);
        ids.add(e.to);
      }
    });
    return ids;
  }, [blueprint]);

  const [view, setView] = useState<ViewId>("solution");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = selectedId ? nodeById.get(selectedId) ?? null : null;

  // Scale the whole canvas down to fit the available width instead of
  // scrolling horizontally — CSS transform:scale preserves correct click
  // hit-testing, so nodes stay clickable at any scale.
  const wrapRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width;
      if (width) setContainerWidth(width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const scale = containerWidth > 0 ? Math.min(1, containerWidth / layout.width) : 1;

  const isNodeRelevant = (node: BlueprintNode): boolean => {
    if (view === "security") return node.securityRelevant;
    if (view === "ai") return node.aiRelevant;
    if (view === "dataflow") return primaryNodeIds.has(node.id);
    return true;
  };

  const isEdgeRelevant = (edge: BlueprintEdge): boolean => {
    if (view === "dataflow") return edge.tags.includes("primary");
    if (view === "security") return edge.tags.includes("security") || edge.tags.includes("audit");
    if (view === "ai") {
      const from = nodeById.get(edge.from);
      const to = nodeById.get(edge.to);
      return Boolean(from?.aiRelevant && to?.aiRelevant);
    }
    return true;
  };

  const activeView = VIEWS.find((v) => v.id === view)!;

  return (
    <div className="blueprint-shell">
      <div className="blueprint-tabs" role="tablist" aria-label="Architecture views">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            type="button"
            role="tab"
            aria-selected={view === v.id}
            className={`blueprint-tab ${view === v.id ? "active" : ""}`}
            onClick={() => setView(v.id)}
          >
            {v.label}
          </button>
        ))}
      </div>
      <p className="blueprint-view-help">{activeView.help}</p>

      <div className="blueprint-body">
        <div className="blueprint-canvas-wrap" ref={wrapRef} style={{ height: layout.height * scale }}>
          <div
            className="blueprint-canvas"
            data-view={view}
            style={{ width: layout.width, height: layout.height, transform: `scale(${scale})` }}
          >
            <div className="blueprint-zones" aria-hidden="true">
              {zoneRects.map((zone) => (
                <div
                  key={zone.id}
                  className="blueprint-zone"
                  style={{ left: zone.x, width: zone.width, height: layout.mainLaneHeight }}
                >
                  <span className="zone-label">{zone.label}</span>
                </div>
              ))}
              <div
                className="blueprint-oversight-band"
                style={{ top: layout.mainLaneHeight, width: layout.width, height: layout.height - layout.mainLaneHeight }}
              >
                <span className="zone-label">Governance &amp; Oversight</span>
              </div>
            </div>

            <svg className="blueprint-edges" width={layout.width} height={layout.height} aria-hidden="true">
              <defs>
                <marker id="bp-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M0 0 L10 5 L0 10 Z" fill="currentColor" />
                </marker>
              </defs>
              {blueprint.edges.map((edge) => {
                const from = layout.boxes.get(edge.from);
                const to = layout.boxes.get(edge.to);
                if (!from || !to) return null;
                return (
                  <path
                    key={edge.id}
                    d={edgePath(from, to)}
                    className="blueprint-edge"
                    markerEnd="url(#bp-arrow)"
                    data-primary={edge.tags.includes("primary")}
                    data-security={edge.tags.includes("security")}
                    data-audit={edge.tags.includes("audit") && !edge.tags.includes("security")}
                    data-sensitive={edge.sensitive}
                    data-dim={!isEdgeRelevant(edge)}
                  />
                );
              })}
            </svg>

            {blueprint.nodes.map((node) => {
              const box = layout.boxes.get(node.id);
              if (!box) return null;
              const Icon = KIND_ICON[node.kind];
              const category = KIND_CATEGORY[node.kind];
              return (
                <button
                  key={node.id}
                  type="button"
                  className={`blueprint-node cat-${category} lane-${node.lane} ${selectedId === node.id ? "selected" : ""}`}
                  style={{ left: box.x, top: box.y, width: box.width, height: box.height }}
                  data-dim={!isNodeRelevant(node)}
                  onClick={() => setSelectedId(node.id)}
                  aria-pressed={selectedId === node.id}
                >
                  <Icon width={16} height={16} />
                  <span>{node.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {selected && (
          <>
            <div className="blueprint-backdrop" onClick={() => setSelectedId(null)} />
            <aside className="blueprint-detail" aria-label={`${selected.label} details`}>
              <button type="button" className="blueprint-detail-close" onClick={() => setSelectedId(null)} aria-label="Close details">
                <ChevronRight width={16} height={16} />
              </button>
              <p className="blueprint-detail-type">{selected.detail.componentType}</p>
              <h3>{selected.label}</h3>
              <p className="blueprint-detail-purpose">{selected.detail.purpose}</p>
              <dl className="blueprint-detail-list">
                {selected.detail.authentication && (
                  <>
                    <dt>Authentication</dt>
                    <dd>{selected.detail.authentication}</dd>
                  </>
                )}
                {selected.detail.authorization && (
                  <>
                    <dt>Authorization</dt>
                    <dd>{selected.detail.authorization}</dd>
                  </>
                )}
                {selected.detail.consumes.length > 0 && (
                  <>
                    <dt>Consumes</dt>
                    <dd>{selected.detail.consumes.join(", ")}</dd>
                  </>
                )}
                {selected.detail.produces.length > 0 && (
                  <>
                    <dt>Produces</dt>
                    <dd>{selected.detail.produces.join(", ")}</dd>
                  </>
                )}
                {selected.detail.dependencies.length > 0 && (
                  <>
                    <dt>Dependencies</dt>
                    <dd>{selected.detail.dependencies.join(", ")}</dd>
                  </>
                )}
                {selected.detail.relatedCatalogComponent && (
                  <>
                    <dt>Related AI Catalog component</dt>
                    <dd>{selected.detail.relatedCatalogComponent}</dd>
                  </>
                )}
              </dl>
            </aside>
          </>
        )}
      </div>

      <p className="blueprint-hint">Click any component for details. Switch views above for security, AI-catalog, or data-flow emphasis.</p>

      <div className="blueprint-legend">
        {(Object.keys(CATEGORY_LABEL) as NodeCategory[]).map((category) => (
          <span className="legend-item" key={category}>
            <span className={`swatch cat-${category}`} /> {CATEGORY_LABEL[category]}
          </span>
        ))}
        <span className="legend-item">
          <span className="line-sample" /> Primary flow
        </span>
        <span className="legend-item">
          <span className="line-sample dashed" /> Audit trail
        </span>
        <span className="legend-item">
          <span className="line-sample sensitive" /> Sensitive data
        </span>
      </div>
    </div>
  );
}
