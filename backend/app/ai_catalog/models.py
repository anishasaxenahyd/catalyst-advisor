"""AI Catalog — a seeded inventory of reusable enterprise AI building
blocks (agents, MCP servers, APIs, models, prompt templates, skills,
connectors). Deliberately separate from both `app.models.schemas`
(Catalyst's fictional catalog that drives the deterministic engine — left
untouched) and `app.enterprise_knowledge` (real-vendor public knowledge,
not reusable internal assets). This one models an enterprise's *own*
inventory: realistic sample data, not sourced from public documentation,
so it deliberately does not carry `KnowledgeSourceRef` attribution — a
catalog asset isn't a claim that needs evidence, it's inventory.

Mirrors the shape of `app.models.schemas.EnterpriseAsset` (same style:
one model, a category/type discriminator, tags) rather than inventing a
new pattern, per "follow the existing project architecture and coding
style".
"""

from typing import Literal

from pydantic import BaseModel, Field

AssetType = Literal[
    "agent",
    "mcp_server",
    "api",
    "ai_model",
    "prompt_template",
    "skill",
    "connector",
]

Maturity = Literal["experimental", "stable", "deprecated"]


class CatalogAsset(BaseModel):
    id: str
    asset_type: AssetType
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    maturity: Maturity = "stable"
    reuse_count: int = Field(
        default=0, description="Illustrative count of how many Solution Registry implementations reused this asset."
    )
