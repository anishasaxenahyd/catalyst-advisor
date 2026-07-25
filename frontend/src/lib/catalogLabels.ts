// Display labels for EnterpriseAsset.category — shared by the catalog
// cards and the solution architecture diagram so both agree on wording.

const CATEGORY_LABELS: Record<string, string> = {
  skill: "Skill",
  mcp_server: "MCP Server",
  agent: "Agent",
  api: "API",
};

export function formatAssetCategory(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}
