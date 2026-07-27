"""Loads the AI Catalog's seed data. Same shape as
`app.enterprise_knowledge.factory` — reuses the same JSON loader rather
than duplicating loading logic — but its own, independent cache: this
catalog has nothing to do with the Enterprise Knowledge Platform's
vendor-sourced entries or Catalyst's engine-facing catalog.
"""

from functools import lru_cache
from pathlib import Path

from app.ai_catalog.models import CatalogAsset
from app.enterprise_knowledge.ingestion.file_loaders import JsonKnowledgeLoader

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "ai_catalog"

_FILES = [
    "agents.json",
    "mcp_servers.json",
    "apis.json",
    "ai_models.json",
    "prompt_templates.json",
    "skills.json",
    "connectors.json",
]


@lru_cache(maxsize=1)
def load_ai_catalog() -> list[CatalogAsset]:
    assets: list[CatalogAsset] = []
    for filename in _FILES:
        assets.extend(JsonKnowledgeLoader(DATA_DIR / filename, CatalogAsset).load())
    return assets
