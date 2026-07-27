"""Retrieval interface. `RetrievalService` is the one contract the rest of
the app depends on today, backed by a real (if simple) keyword/filter
implementation — see `in_memory.py`.

`VectorSearchCapable` and `GraphTraversalCapable` are extension points, not
requirements: a future retrieval implementation can additionally implement
one or both (structurally — no inheritance needed, just define the
methods) to add embedding-based similarity search or relationship
traversal (e.g. "which Security Controls apply to this Architecture
Pattern") without changing this interface or anything that calls
`search()`. Nothing in this phase implements either.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from app.enterprise_knowledge.models import KnowledgeCategory, KnowledgeEntry, SourceVendor


class RetrievalQuery(BaseModel):
    text: str | None = None
    category: KnowledgeCategory | None = None
    vendor: SourceVendor | None = None
    tags: list[str] = Field(default_factory=list)
    limit: int = 20


class RetrievalResult(BaseModel):
    entry: KnowledgeEntry
    score: float = Field(description="Relevance score. Keyword-match based today; embedding similarity is a drop-in replacement behind the same field.")


class RetrievalService(ABC):
    @abstractmethod
    def search(self, query: RetrievalQuery) -> list[RetrievalResult]: ...


@runtime_checkable
class VectorSearchCapable(Protocol):
    """Future extension point — not implemented in this phase. A retrieval
    service that also implements this can be embedded-similarity-searched
    directly, e.g. by a future `RecommendationPipeline`."""

    def vector_search(self, query_text: str, top_k: int) -> list[RetrievalResult]: ...


@runtime_checkable
class GraphTraversalCapable(Protocol):
    """Future extension point — not implemented in this phase. A retrieval
    service that also implements this can answer relationship queries,
    e.g. traverse(start_id="pattern-rag", relation="requires_control")."""

    def traverse(self, start_id: str, relation: str, depth: int) -> list[RetrievalResult]: ...
