"""A real, working retrieval implementation — keyword matching plus
category/vendor/tag filtering over an in-memory list. This is the
"initially" counterpart to `VectorSearchCapable` in `base.py`: good enough
to search 40 seed entries usefully today, and swappable for an embedding
index later without any caller needing to change (same `RetrievalService`
interface, same `RetrievalQuery` in, `RetrievalResult` out).
"""

from app.enterprise_knowledge.models import KnowledgeEntry
from app.enterprise_knowledge.retrieval.base import RetrievalQuery, RetrievalResult, RetrievalService

_STOPWORDS = {
    "the", "a", "an", "in", "on", "of", "to", "for", "and", "or", "is", "are",
    "this", "that", "with", "from", "by", "as", "it", "be", "was", "were",
    "will", "can", "not", "no", "our", "your", "we", "you",
}


def _tokenize(text: str) -> set[str]:
    return {w.strip(".,()-\"'") for w in text.lower().split()}


class InMemoryKeywordRetrievalService(RetrievalService):
    def __init__(self, entries: list[KnowledgeEntry]):
        self._entries = entries

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        candidates = self._entries
        if query.category:
            candidates = [e for e in candidates if e.category == query.category]
        if query.vendor:
            candidates = [e for e in candidates if e.source.vendor == query.vendor]
        if query.tags:
            wanted = {t.lower() for t in query.tags}
            candidates = [e for e in candidates if wanted & {t.lower() for t in e.tags}]

        text = (query.text or "").strip().lower()
        results: list[RetrievalResult] = []
        for entry in candidates:
            score = self._score(entry, text)
            if text and score <= 0:
                continue
            results.append(RetrievalResult(entry=entry, score=score))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.limit]

    @staticmethod
    def _score(entry: KnowledgeEntry, text: str) -> float:
        if not text:
            return 1.0  # filter-only query — every surviving candidate is equally relevant
        name = entry.name.lower()
        summary = entry.summary.lower()
        tags = " ".join(t.lower() for t in entry.tags)

        score = 0.0
        if text in name:
            score += 3.0
        if text in tags:
            score += 2.0
        if text in summary:
            score += 1.0

        # Word-level partial credit uses whole-word set membership, not
        # substring containment — "in" as a query word must not match
        # merely because it's a substring of, say, "Human-in-the-Loop".
        # Short/common words are excluded so a natural-language query
        # ("show me a pattern for...") doesn't pick up noise matches from
        # stopwords alone.
        query_words = {w for w in _tokenize(text) if len(w) >= 4 and w not in _STOPWORDS}
        if query_words:
            name_words = _tokenize(name)
            summary_words = _tokenize(summary)
            for word in query_words:
                if word in name_words:
                    score += 0.5
                if word in summary_words:
                    score += 0.25
        return score
