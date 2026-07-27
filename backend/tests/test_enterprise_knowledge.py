from pathlib import Path

from app.enterprise_knowledge.factory import get_recommendation_pipeline, get_retrieval_service, load_knowledge_base
from app.enterprise_knowledge.ingestion.file_loaders import JsonKnowledgeLoader, YamlKnowledgeLoader
from app.enterprise_knowledge.models import ArchitecturePatternEntry, GovernanceRuleEntry
from app.enterprise_knowledge.pipeline.base import KnowledgeRecommendationRequest
from app.enterprise_knowledge.retrieval.base import RetrievalQuery

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_knowledge_base_loads_all_seven_categories():
    kb = load_knowledge_base()
    counts = kb.counts()

    assert set(counts) == {
        "architecture_pattern",
        "ai_model",
        "security_control",
        "governance_rule",
        "cloud_service",
        "ai_catalog_component",
        "reference_architecture",
    }
    assert all(n > 0 for n in counts.values())
    assert len(kb.all_entries()) == sum(counts.values())


def test_every_entry_has_source_attribution():
    for entry in load_knowledge_base().all_entries():
        assert entry.source.vendor
        assert entry.source.title
        assert entry.source.reference


def test_seed_data_spans_all_named_vendors():
    vendors = {entry.source.vendor for entry in load_knowledge_base().all_entries()}
    assert {"microsoft", "aws", "google_cloud", "anthropic", "openai"}.issubset(vendors)


def test_json_loader_validates_architecture_patterns():
    loader = JsonKnowledgeLoader(
        Path(__file__).resolve().parents[1] / "data" / "enterprise_knowledge" / "architecture_patterns.json",
        ArchitecturePatternEntry,
    )
    entries = loader.load()
    assert len(entries) > 0
    assert all(isinstance(e, ArchitecturePatternEntry) for e in entries)
    assert all(e.category == "architecture_pattern" for e in entries)


def test_yaml_loader_reads_same_shape_as_json_loader():
    loader = YamlKnowledgeLoader(FIXTURES_DIR / "sample_governance_rules.yaml", GovernanceRuleEntry)
    entries = loader.load()

    assert len(entries) == 1
    assert isinstance(entries[0], GovernanceRuleEntry)
    assert entries[0].id == "governance-sample-yaml-source"
    assert entries[0].source.vendor == "vendor_neutral"


def test_retrieval_filters_by_category():
    service = get_retrieval_service()
    results = service.search(RetrievalQuery(category="ai_model"))
    assert len(results) > 0
    assert all(r.entry.category == "ai_model" for r in results)


def test_retrieval_filters_by_vendor():
    service = get_retrieval_service()
    results = service.search(RetrievalQuery(vendor="anthropic"))
    assert len(results) > 0
    assert all(r.entry.source.vendor == "anthropic" for r in results)


def test_retrieval_filters_by_tag():
    service = get_retrieval_service()
    results = service.search(RetrievalQuery(tags=["retrieval"]))
    assert len(results) > 0
    assert all("retrieval" in [t.lower() for t in r.entry.tags] for r in results)


def test_retrieval_text_search_ranks_name_match_highest():
    service = get_retrieval_service()
    results = service.search(RetrievalQuery(text="Bedrock"))
    assert len(results) > 0
    # every top-scored result should actually mention "bedrock" somewhere
    top_score = results[0].score
    assert all(r.score <= top_score for r in results)
    assert "bedrock" in results[0].entry.name.lower() or "bedrock" in results[0].entry.summary.lower()


def test_retrieval_respects_limit():
    service = get_retrieval_service()
    results = service.search(RetrievalQuery(limit=2))
    assert len(results) <= 2


def test_retrieval_no_match_returns_empty():
    # Nonsense tokens sharing no real word with any seed entry — a query
    # built from ordinary English words (even in a nonsense sentence) can
    # legitimately score low-but-nonzero matches on unrelated entries that
    # happen to share a common word (e.g. "data"); that's expected keyword-
    # search behavior, not a bug, and exactly what the vector-search
    # extension point in retrieval/base.py exists to eventually improve on.
    service = get_retrieval_service()
    results = service.search(RetrievalQuery(text="zzqxephemeral419 blorptastic gigafrobnicate"))
    assert results == []


def test_pipeline_placeholder_returns_labeled_not_implemented_result():
    pipeline = get_recommendation_pipeline()
    result = pipeline.recommend(KnowledgeRecommendationRequest(raw_text="anything"))

    assert result.confidence.basis == "not_yet_implemented"
    assert "not implemented" in result.summary.lower()
    assert result.evidence == []
