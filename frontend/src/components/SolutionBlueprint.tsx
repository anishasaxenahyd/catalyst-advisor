import { useMemo, useState, type ComponentType, type SVGProps } from "react";
import type { Report } from "../types/report";
import {
  buildBlueprint,
  computeLayout,
  type BlueprintEdge,
  type BlueprintNode,
  type NodeKind,
} from "../lib/blueprint";
import {
  IconUser,
  IconLock,
  IconRoute,
  IconSparkles,
  IconLayers,
  IconCpu,
  IconFileText,
  IconDatabase,
  IconServer,
  IconCloud,
  IconCheckCircle,
  IconEye,
  IconChevron,
} from "./icons";

const KIND_ICON: Record<NodeKind, ComponentType<SVGProps<SVGSVGElement>>> = {
  user: IconUser,
  auth: IconLock,
  api_gateway: IconRoute,
  ai_gateway: IconRoute,
  agent: IconSparkles,
  skill: IconLayers,
  model: IconCpu,
  prompt: IconFileText,
  vector_store: IconDatabase,
  mcp_server: IconServer,
  api: IconCloud,
  database: IconDatabase,
  system: IconCloud,
  human: IconUser,
  audit: IconEye,
  monitoring: IconEye,
  output: IconCheckCircle,
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
  const midX = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
}

export default function SolutionBlueprint({ report }: { report: Report }) {
  const blueprint = useMemo(() => buildBlueprint(report), [report]);
  const layout = useMemo(() => computeLayout(blueprint.nodes), [blueprint]);
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
        <div className="blueprint-canvas-scroll">
          <div className="blueprint-canvas" data-view={view} style={{ width: layout.width, height: layout.height }}>
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
              return (
                <button
                  key={node.id}
                  type="button"
                  className={`blueprint-node kind-${node.kind} lane-${node.lane} ${selectedId === node.id ? "selected" : ""}`}
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
                <IconChevron width={16} height={16} />
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
    </div>
  );
}
