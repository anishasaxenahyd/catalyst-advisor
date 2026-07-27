"""Loads the Solution Registry's seed data. Same shape as
`app.ai_catalog.factory` — reuses the same JSON loader, own independent
cache. Kept separate from the AI Catalog and the Enterprise Knowledge
Platform: this is a record of past implementations, not reusable assets
or vendor-sourced guidance.
"""

from functools import lru_cache
from pathlib import Path

from app.enterprise_knowledge.ingestion.file_loaders import JsonKnowledgeLoader
from app.solution_registry.models import SolutionRecord

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "solution_registry"


@lru_cache(maxsize=1)
def load_solution_registry() -> list[SolutionRecord]:
    return JsonKnowledgeLoader(DATA_DIR / "solutions.json", SolutionRecord).load()
