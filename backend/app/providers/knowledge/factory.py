"""Builds the active KnowledgeProvider for the running process.

Phase 0 always wires the JSON-backed composite. A future phase that wants a
REST or MCP-backed catalog swaps the construction here — nothing that calls
`get_knowledge_provider()` needs to change.
"""

from functools import lru_cache
from pathlib import Path

from app.providers.knowledge.base import KnowledgeProvider
from app.providers.knowledge.json_providers import (
    CompositeKnowledgeProvider,
    JsonCatalogProvider,
    JsonModelProvider,
    JsonWorkbenchProvider,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@lru_cache(maxsize=1)
def get_knowledge_provider() -> KnowledgeProvider:
    catalog_dir = DATA_DIR / "catalog"
    workbench_dir = DATA_DIR / "workbench"
    return CompositeKnowledgeProvider(
        catalog=JsonCatalogProvider(catalog_dir),
        models=JsonModelProvider(catalog_dir),
        workbench=JsonWorkbenchProvider(workbench_dir),
    )
