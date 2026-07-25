// Enterprise Solution Blueprint — a structural, business-language rendering
// of "what would I actually build" for the recommended solution.
//
// A fixed scaffold (Users, Identity Provider, API Gateway, AI Gateway,
// Audit, Monitoring, Response) represents architectural facts true of any
// real enterprise deployment — every one needs an entry point, an identity
// check, and an audit trail, whether or not the recommendation engine
// "chose" them. Everything else — which agents, skills, connectors,
// databases, and enterprise systems appear — is assembled entirely from
// this specific Report: `enterprise_reuse`, `model_recommendation`,
// `signal_vector`. Two different recommendations produce two different
// graphs; only the scaffold repeats.

import type { EnterpriseAsset, Report } from "../types/report";

export type NodeKind =
  | "user"
  | "auth"
  | "api_gateway"
  | "ai_gateway"
  | "agent"
  | "skill"
  | "model"
  | "prompt"
  | "vector_store"
  | "mcp_server"
  | "api"
  | "database"
  | "system"
  | "human"
  | "audit"
  | "monitoring"
  | "output";

export interface NodeDetail {
  purpose: string;
  componentType: string;
  authentication?: string;
  authorization?: string;
  consumes: string[];
  produces: string[];
  dependencies: string[];
  relatedCatalogComponent?: string;
}

export interface BlueprintNode {
  id: string;
  kind: NodeKind;
  label: string;
  column: number;
  row: number;
  lane: "main" | "oversight";
  securityRelevant: boolean;
  aiRelevant: boolean;
  detail: NodeDetail;
}

export type EdgeTag = "primary" | "security" | "audit";

export interface BlueprintEdge {
  id: string;
  from: string;
  to: string;
  label?: string;
  tags: EdgeTag[];
  sensitive: boolean;
}

export interface Blueprint {
  nodes: BlueprintNode[];
  edges: BlueprintEdge[];
}

const DB_KEYWORDS = ["database", "warehouse", "store", "snowflake", "sql", "records"];

function looksLikeDatabase(asset: EnterpriseAsset): boolean {
  const text = `${asset.name} ${asset.description}`.toLowerCase();
  return DB_KEYWORDS.some((kw) => text.includes(kw));
}

function titleCase(value: string): string {
  return value.replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1));
}

function catalogRef(name: string): string {
  return `AI Catalog → ${name}`;
}

export function buildBlueprint(report: Report): Blueprint {
  const rowCounters: Record<number, number> = {};
  const nextRow = (column: number): number => {
    rowCounters[column] = (rowCounters[column] ?? -1) + 1;
    return rowCounters[column];
  };

  const { signal_vector, enterprise_reuse, model_recommendation, architecture_recommendation } = report;
  const assets = enterprise_reuse.map((item) => item.asset);
  const agents = assets.filter((a) => a.category === "agent");
  const skills = assets.filter((a) => a.category === "skill");
  const rawConnectors = assets.filter((a) => a.category === "mcp_server" || a.category === "api");
  const databases = rawConnectors.filter(looksLikeDatabase);
  const connectors = rawConnectors.filter((a) => !looksLikeDatabase(a));
  const systems = signal_vector.integration_points.slice(0, 4);
  const humanInLoop = signal_vector.automation_level !== "autonomous";
  const isRetrievalPattern =
    architecture_recommendation.pattern.suitable_for_tags.includes("retrieval") ||
    architecture_recommendation.pattern.id.includes("rag");
  const sensitiveData = signal_vector.data_sensitivity !== "none";

  const nodes: BlueprintNode[] = [];
  const edges: BlueprintEdge[] = [];

  const addNode = (
    id: string,
    kind: NodeKind,
    label: string,
    column: number,
    detail: NodeDetail,
    opts: { lane?: "main" | "oversight"; security?: boolean; ai?: boolean } = {}
  ) => {
    nodes.push({
      id,
      kind,
      label,
      column,
      row: nextRow(column),
      lane: opts.lane ?? "main",
      securityRelevant: opts.security ?? false,
      aiRelevant: opts.ai ?? false,
      detail,
    });
  };

  const addEdge = (from: string, to: string, tags: EdgeTag[], label?: string, sensitive = false) => {
    edges.push({ id: `${from}->${to}`, from, to, label, tags, sensitive });
  };

  // --- Column 0: Users ---
  addNode("user", "user", "Users", 0, {
    purpose: "The people or upstream systems that initiate this workflow.",
    componentType: "End users",
    consumes: [],
    produces: [signal_vector.use_case_type],
    dependencies: [],
  });

  // --- Column 1: Identity + API Gateway ---
  addNode("auth", "auth", "Identity Provider (SSO)", 1, {
    purpose: "Confirms who is making the request before anything else happens.",
    componentType: "Authentication",
    authentication: "Enterprise SSO (e.g. Azure AD, Okta, Entra ID)",
    consumes: ["Login / SSO token"],
    produces: ["Verified identity"],
    dependencies: [],
    relatedCatalogComponent: "Standard enterprise infrastructure — not an AI Catalog component.",
  }, { security: true });

  addNode("api_gateway", "api_gateway", "API Gateway", 1, {
    purpose: "Single entry point for every request; enforces authorization and routing before traffic reaches the AI layer.",
    componentType: "Gateway",
    authorization: "Confirms the caller is entitled to this workflow.",
    consumes: ["Incoming request", "Verified identity"],
    produces: ["Authorized request"],
    dependencies: ["Identity Provider (SSO)"],
    relatedCatalogComponent: "Standard enterprise infrastructure — not an AI Catalog component.",
  }, { security: true });

  addEdge("user", "api_gateway", ["primary"], "sends request");
  addEdge("api_gateway", "auth", ["security"], "verifies identity");
  addEdge("auth", "api_gateway", ["security"], "issues token");

  // --- Column 2: AI Gateway ---
  addNode("ai_gateway", "ai_gateway", "AI Gateway", 2, {
    purpose: "Governs access to agents and models specifically — model routing, usage limits, and data-sensitivity policy checks for AI traffic.",
    componentType: "AI Governance",
    authorization: "Applies AI-usage policy before the request reaches an agent or model.",
    consumes: ["Authorized request"],
    produces: ["Governed AI request"],
    dependencies: ["API Gateway"],
    relatedCatalogComponent: "Standard enterprise infrastructure — not an AI Catalog component.",
  }, { security: true, ai: true });
  addEdge("api_gateway", "ai_gateway", ["primary", "security"], "forwards");

  // --- Column 3: Orchestration (agents, chained) ---
  let upstream = "ai_gateway";
  agents.forEach((agent, i) => {
    const id = `agent${i}`;
    addNode(id, "agent", agent.name, 3, {
      purpose: agent.description,
      componentType: "AI Agent",
      authorization: "Operates within the permissions granted by the AI Gateway.",
      consumes: [i === 0 ? "Governed AI request" : `Output of ${agents[i - 1].name}`],
      produces: ["Task decomposition", "Tool / connector calls"],
      dependencies: [i === 0 ? "AI Gateway" : agents[i - 1].name],
      relatedCatalogComponent: catalogRef(agent.name),
    }, { ai: true });
    addEdge(upstream, id, ["primary"], i === 0 ? "routes to" : "hands off to");
    upstream = id;
  });

  // --- Column 4: AI core — model, prompt templates, vector store ---
  addNode("prompt", "prompt", "Prompt Templates", 4, {
    purpose: `The structured, versioned instructions that shape how the model reasons about "${architecture_recommendation.pattern.name}".`,
    componentType: "Prompt Engineering",
    consumes: [`Business rules for ${architecture_recommendation.pattern.name}`],
    produces: ["Structured prompt"],
    dependencies: [],
    relatedCatalogComponent: "Maintained alongside the agent/model configuration — not a separate AI Catalog entry.",
  }, { ai: true });

  addNode("model", "model", model_recommendation.primary.name, 4, {
    purpose: model_recommendation.primary.description,
    componentType: "Language Model (LLM)",
    consumes: ["Structured prompt", "Task from orchestration"],
    produces: ["Draft response", "Reasoning output"],
    dependencies: isRetrievalPattern ? ["Prompt Templates", "Vector Store"] : ["Prompt Templates"],
    relatedCatalogComponent: catalogRef(model_recommendation.primary.name),
  }, { ai: true });

  addEdge("prompt", "model", ["primary"], "shapes prompt for");
  addEdge(upstream, "model", ["primary"], "reasons via");

  if (isRetrievalPattern) {
    addNode("vector_store", "vector_store", "Vector Store (Knowledge Index)", 4, {
      purpose: "Holds embedded enterprise documents so the model retrieves relevant context instead of relying on memory alone.",
      componentType: "Knowledge Store",
      consumes: ["Indexed enterprise documents"],
      produces: ["Relevant passages"],
      dependencies: databases.length > 0 ? [databases[0].name] : [],
      relatedCatalogComponent: "Standard RAG infrastructure — not an AI Catalog component.",
    }, { ai: true });
    addEdge(upstream, "vector_store", ["primary"], "retrieves context from");
    addEdge("vector_store", "model", ["primary"], "supplies context to");
  }

  // --- Column 5: Capabilities (skills) ---
  skills.forEach((skill, i) => {
    const id = `skill${i}`;
    addNode(id, "skill", skill.name, 5, {
      purpose: skill.description,
      componentType: "Skill (Reusable Capability)",
      consumes: ["Task from orchestration"],
      produces: ["Structured result"],
      dependencies: [],
      relatedCatalogComponent: catalogRef(skill.name),
    }, { ai: true });
    addEdge(upstream, id, ["primary"], "invokes");
  });

  // --- Column 6: Integration layer (connectors + databases) ---
  const connectorNodes: { id: string; name: string }[] = [];
  connectors.forEach((asset, i) => {
    const id = `conn${i}`;
    const kind: NodeKind = asset.category === "mcp_server" ? "mcp_server" : "api";
    addNode(id, kind, asset.name, 6, {
      purpose: asset.description,
      componentType: asset.category === "mcp_server" ? "MCP Server (Enterprise Connector)" : "Enterprise API",
      authentication: "Authenticates to the target system with a managed service credential (not a user credential).",
      consumes: ["Query from orchestration"],
      produces: ["Enterprise data"],
      dependencies: [],
      relatedCatalogComponent: catalogRef(asset.name),
    }, { security: true, ai: true });
    addEdge(upstream, id, ["primary"], asset.category === "mcp_server" ? "queries" : "calls");
    connectorNodes.push({ id, name: asset.name });
  });
  databases.forEach((asset, i) => {
    const id = `db${i}`;
    addNode(id, "database", asset.name, 6, {
      purpose: asset.description,
      componentType: "Database",
      authentication: "Authenticates with a managed service credential (not a user credential).",
      consumes: ["Query from orchestration"],
      produces: ["Records"],
      dependencies: [],
      relatedCatalogComponent: catalogRef(asset.name),
    }, { security: true, ai: true });
    addEdge(upstream, id, ["primary"], "reads/writes");
    connectorNodes.push({ id, name: asset.name });
  });

  // --- Column 7: Enterprise systems (named connector match preferred) ---
  systems.forEach((sys, i) => {
    const id = `sys${i}`;
    const sysLower = sys.toLowerCase();
    const named = connectorNodes.filter((c) => c.name.toLowerCase().includes(sysLower));
    const sources = named.length > 0 ? named : connectorNodes;

    addNode(id, "system", titleCase(sys), 7, {
      purpose: "The system of record this solution reads from or writes to.",
      componentType: "Enterprise System",
      consumes: ["Requests from the integration layer"],
      produces: ["Business data"],
      dependencies: [],
      relatedCatalogComponent: "External system — not part of the AI Catalog.",
    }, { security: sensitiveData });

    if (sources.length > 0) {
      sources.forEach((s) => addEdge(s.id, id, ["primary", "security"], "reads/writes", sensitiveData));
    } else {
      addEdge(upstream, id, ["primary"], "connects to");
    }
  });

  // --- Human approval + outcome ---
  const finalColumn = 8;
  if (humanInLoop) {
    addNode("human", "human", "Human Review & Approval", finalColumn, {
      purpose: "A person reviews the AI's output before it's finalized or acted on — required because this workflow is not fully autonomous.",
      componentType: "Human-in-the-loop Control",
      authorization: "Only authorized reviewers may approve, per the Workbench's access policy.",
      consumes: ["Draft output"],
      produces: ["Approved action / response"],
      dependencies: [],
    }, { security: true });
    addEdge("model", "human", ["primary", "security"], "drafts for", sensitiveData);
    addNode("output", "output", "Response / Action", finalColumn + 1, {
      purpose: "The final result reaches the user or system that requested it.",
      componentType: "Outcome",
      consumes: ["Approved result"],
      produces: [],
      dependencies: [],
    });
    addEdge("human", "output", ["primary", "security"], "approves");
  } else {
    addNode("output", "output", "Automated Action", finalColumn, {
      purpose: "The result is delivered or acted on automatically — no human checkpoint in this workflow.",
      componentType: "Outcome",
      consumes: ["Model result"],
      produces: [],
      dependencies: [],
    });
    addEdge("model", "output", ["primary"], "executes");
  }

  // --- Oversight lane: Audit + Monitoring ---
  addNode("audit", "audit", "Audit Log", 2, {
    purpose: "Immutable record of who did what, when — required for compliance review and incident investigation.",
    componentType: "Audit & Compliance",
    consumes: ["Access events", "Actions taken"],
    produces: ["Audit trail"],
    dependencies: [],
  }, { lane: "oversight", security: true });
  addEdge("api_gateway", "audit", ["audit"], "logs access");
  addEdge("ai_gateway", "audit", ["audit"], "logs AI usage");
  if (humanInLoop) addEdge("human", "audit", ["audit"], "logs decision");

  addNode("monitoring", "monitoring", "Observability", 6, {
    purpose: "Tracks latency, error rates, and usage so the team can tell the solution is healthy in production.",
    componentType: "Monitoring",
    consumes: ["Runtime metrics"],
    produces: ["Dashboards & alerts"],
    dependencies: [],
  }, { lane: "oversight" });
  addEdge(upstream, "monitoring", ["audit"], "reports metrics");

  return { nodes, edges };
}

// --------------------------------------------------------------------------
// Layout — a plain column/row grid, not a general graph-layout algorithm.
// The blueprint is always a small, well-structured DAG with explicit
// conceptual layers (see `column` above), so a hand-computed grid gives a
// clean result without pulling in a layout library. The "oversight" lane
// (Audit, Monitoring) is pinned below every "main" lane node so it always
// reads as a separate band rather than wherever its own column happens to end.
// --------------------------------------------------------------------------

export interface LayoutBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export const NODE_WIDTH = 168;
export const NODE_HEIGHT = 56;
const COLUMN_WIDTH = 210;
const ROW_HEIGHT = 80;
const LANE_GAP = 56;
const MARGIN = 24;

export function computeLayout(nodes: BlueprintNode[]): {
  boxes: Map<string, LayoutBox>;
  width: number;
  height: number;
} {
  const mainRows = nodes.filter((n) => n.lane === "main").map((n) => n.row);
  const maxMainRow = mainRows.length > 0 ? Math.max(...mainRows) : 0;
  const oversightY = MARGIN + (maxMainRow + 1) * ROW_HEIGHT + LANE_GAP;

  const boxes = new Map<string, LayoutBox>();
  let maxX = 0;
  let maxY = 0;

  for (const n of nodes) {
    const x = MARGIN + n.column * COLUMN_WIDTH;
    const y = n.lane === "oversight" ? oversightY + n.row * ROW_HEIGHT : MARGIN + n.row * ROW_HEIGHT;
    boxes.set(n.id, { x, y, width: NODE_WIDTH, height: NODE_HEIGHT });
    maxX = Math.max(maxX, x + NODE_WIDTH);
    maxY = Math.max(maxY, y + NODE_HEIGHT);
  }

  return { boxes, width: maxX + MARGIN, height: maxY + MARGIN };
}
