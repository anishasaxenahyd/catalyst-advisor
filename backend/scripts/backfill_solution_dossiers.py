"""One-off data migration: backfill obligation_profile / requirement_signatures /
evidence_class / conditions onto every existing Solution Registry record, using
simple industry/tag/pattern heuristics — this is seed data for a prototype, not
a real classification service. Also appends two new precedent records
(an abandoned attempt and a pilot) so the precedent store has hazard and
feasibility-only evidence classes to demonstrate, not just production successes.

Run once: .venv/Scripts/python.exe scripts/backfill_solution_dossiers.py
Safe to re-run — it recomputes the four new fields from scratch each time.
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "solution_registry" / "solutions.json"

_PHI_INDUSTRIES = {"Healthcare", "Pharmaceuticals & Life Sciences"}
_PII_INDUSTRIES = {
    "Healthcare", "Pharmaceuticals & Life Sciences", "Banking & Financial Services", "Insurance",
    "Government & Public Sector", "Higher Education", "Human Resources", "Retail & E-commerce",
    "Travel & Hospitality", "Automotive", "Telecommunications", "Professional Services",
}
_ACTION_PATTERNS = {"pattern-agentic-hitl", "pattern-autonomous-multi-agent"}
_RETRIEVAL_PATTERNS = {"pattern-rag-enterprise-docs", "pattern-realtime-copilot"}

_TAG_TO_SIGNATURES = {
    "document-heavy": ["ENTERPRISE_PRIVATE_DATA"],
    "retrieval": ["ENTERPRISE_PRIVATE_DATA", "ATTRIBUTION_REQUIRED"],
    "structured": ["STRUCTURED_DATA_SOURCE"],
    "assist": ["INTERACTION_CONVERSATIONAL"],
    "copilot": ["INTERACTION_CONVERSATIONAL", "LOW_LATENCY_REQUIRED"],
    "realtime": ["LOW_LATENCY_REQUIRED"],
    "low-latency": ["LOW_LATENCY_REQUIRED"],
    "agentic": ["TASK_DECOMPOSITION_REQUIRED", "ACTION_REQUIRED"],
    "workflow": ["ACTION_REQUIRED"],
    "autonomous": ["PARALLEL_INDEPENDENT_SUBTASKS"],
    "high-scale": ["HIGH_SCALE_VOLUME"],
    "batch": ["INTERACTION_BATCH"],
    "classification": ["STRUCTURED_DATA_SOURCE"],
    "image": ["IMAGE_MODALITY"],
    "multimodal": ["IMAGE_MODALITY"],
    "compliance": ["SENSITIVE_DATA_PII"],
}


def derive_obligations(record: dict) -> list[str]:
    industry = record["industry"]
    pattern = record["architecture_pattern_id"]
    obligations = ["OBL-GUARDRAILS-ALWAYS", "OBL-EVAL-HARNESS-ALWAYS", "OBL-OBSERVABILITY-ALWAYS", "OBL-MODEL-APPROVED-LIST"]

    if industry in _PHI_INDUSTRIES:
        obligations += ["OBL-PHI-BOUNDARY", "OBL-PHI-SAFE-LOGGING"]
    elif industry in _PII_INDUSTRIES:
        obligations.append("OBL-PII-COMPLIANCE")

    sensitive_industry = industry in _PHI_INDUSTRIES or industry in _PII_INDUSTRIES
    if pattern in _ACTION_PATTERNS or sensitive_industry:
        obligations.append("OBL-AUDIT-SUBJECT-TRACE")
    if pattern in _ACTION_PATTERNS:
        obligations.append("OBL-ACTION-APPROVAL")
    if pattern in _RETRIEVAL_PATTERNS and sensitive_industry:
        obligations.append("OBL-PER-USER-AUTHZ")

    # de-dup, preserve order
    seen: set[str] = set()
    ordered = []
    for o in obligations:
        if o not in seen:
            seen.add(o)
            ordered.append(o)
    return ordered


def derive_signatures(record: dict) -> list[str]:
    signatures: set[str] = set()
    for tag in record.get("tags", []):
        signatures.update(_TAG_TO_SIGNATURES.get(tag, []))
    if record["industry"] in _PHI_INDUSTRIES:
        signatures.add("SENSITIVE_DATA_PHI")
    elif record["industry"] in _PII_INDUSTRIES:
        signatures.add("SENSITIVE_DATA_PII")
    return sorted(signatures)


def derive_conditions(record: dict) -> list[str]:
    return [
        f"Applies when data sensitivity matches this precedent's obligation profile "
        f"({', '.join(record['obligation_profile']) or 'none'}) and the solution class matches "
        f"'{record['architecture_pattern_name']}'.",
    ]


def backfill(record: dict) -> dict:
    record["obligation_profile"] = derive_obligations(record)
    record["requirement_signatures"] = derive_signatures(record)
    record.setdefault("evidence_class", "proven_in_production")
    record["conditions"] = derive_conditions(record)
    return record


_NEW_PRECEDENTS = [
    {
        "id": "solution-claims-graphrag-abandoned",
        "title": "Claims & Coverage Relationship Explorer (Abandoned)",
        "industry": "Insurance",
        "business_problem": "An attempt to answer cross-claim, cross-policy relationship questions (\"which other claims touch this same policyholder and property\") that single-pass retrieval couldn't resolve.",
        "architecture_pattern_id": "pattern-graphrag",
        "architecture_pattern_name": "GraphRAG",
        "ai_models": ["Azure OpenAI GPT-4o"],
        "cloud_provider": "Azure",
        "reused_catalog_assets": ["asset-api-document-repository", "asset-mcp-claims-lookup"],
        "security_considerations": [
            "Entity graph spanned multiple source systems, widening the effective data-access boundary beyond what was originally scoped for review"
        ],
        "business_outcome": "Discontinued after five months — entity resolution across claims/policy/property source systems was unreliable, and graph maintenance cost exceeded the retrieval benefit it delivered.",
        "lessons_learned": [
            "Entity resolution across systems that don't share a common key was the real blocker, not the retrieval or generation quality",
            "The relationship-traversal questions that motivated the project turned out to be answerable by a much simpler join query against the claims warehouse"
        ],
        "tags": ["document-heavy", "retrieval", "structured", "integration-heavy"],
        "evidence_class": "abandoned",
    },
    {
        "id": "solution-hr-benefits-rag-pilot",
        "title": "Employee Benefits Q&A Pilot",
        "industry": "Human Resources",
        "business_problem": "A time-boxed pilot to let employees self-serve general benefits-plan questions instead of filing an HR ticket.",
        "architecture_pattern_id": "pattern-rag-enterprise-docs",
        "architecture_pattern_name": "RAG over Enterprise Docs",
        "ai_models": ["Azure OpenAI GPT-4o mini"],
        "cloud_provider": "Azure",
        "reused_catalog_assets": ["asset-api-document-repository"],
        "security_considerations": [
            "Scoped to general plan documents only — no access to any individual employee's personal enrollment record",
            "No production monitoring or eval harness stood up yet; pilot cohort was 40 employees over six weeks"
        ],
        "business_outcome": "Positive qualitative feedback from the pilot cohort; document-level citation only, no span-level extraction. Not yet operated at scale — no support commitment, no eval suite.",
        "lessons_learned": [
            "Employees repeatedly asked for the specific clause an answer came from, not just the document — a clear signal that document-level citation would not be sufficient for a production launch",
            "Retrofitting span-level citation later is expected to be significant unplanned work; design it in from the start next time"
        ],
        "tags": ["document-heavy", "retrieval", "assist", "structured"],
        "evidence_class": "pilot",
    },
]


def main() -> None:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    records = [backfill(r) for r in records]
    for new_record in _NEW_PRECEDENTS:
        records.append(backfill(new_record))
    DATA_PATH.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Backfilled {len(records)} solution dossiers -> {DATA_PATH}")


if __name__ == "__main__":
    main()
