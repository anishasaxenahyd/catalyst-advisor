"""Ingestion interface — how a knowledge source becomes a list of typed
entries. Originally written for `data/enterprise_knowledge/`; the bound is
`pydantic.BaseModel` rather than `KnowledgeEntryBase` specifically so the
same loaders also serve the AI Catalog and Solution Registry (any Pydantic
model, not just knowledge-platform entries) without duplicating this
class — a future ingestion source (a live vendor feed, a scheduled crawl,
a partner API) implements this same interface and slots in without
changing anything downstream.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class KnowledgeSourceLoader(ABC, Generic[T]):
    """Loads and validates entries of one type from one source."""

    @abstractmethod
    def load(self) -> list[T]: ...
