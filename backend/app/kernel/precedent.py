"""Stage 9: Precedent Retrieval & Analysis.

Runs *after* pattern admissibility (Part 5.5, mechanism 2): precedent may
confirm, warn, or inform, but it cannot introduce a pattern Stage 8 already
ruled contra-indicated, and it must state where the current problem
diverges (mechanism 3) — a precedent that cannot articulate a difference
hasn't been analysed, it's been copied.

Similarity is multi-dimensional and weighted toward obligations, checked in
that order (Part 5.3): obligation-profile overlap first, then requirement-
signature overlap, then solution-pattern match. Evidence class gates what a
finding may be used for (Part 5.4): only `proven_in_production` supports a
transferable decision; `pilot`/`prototype_poc` are feasibility evidence
only; `abandoned`/`superseded` are retained deliberately as hazard evidence.
"""

from app.kernel.schemas import PrecedentFinding
from app.models.schemas import SignalVector
from app.solution_registry.factory import load_solution_registry
from app.solution_registry.models import SolutionRecord

_MAX_FINDINGS = 3


def _usage_for_evidence_class(evidence_class: str) -> str:
    if evidence_class == "proven_in_production":
        return "transferable_decision_evidence"
    if evidence_class in ("abandoned", "superseded"):
        return "hazard_evidence"
    return "feasibility_evidence"


def _similarity(record: SolutionRecord, obligation_ids: set[str], signature_ids: set[str], pattern_ids: set[str]) -> int:
    obligation_overlap = len(set(record.obligation_profile) & obligation_ids)
    signature_overlap = len(set(record.requirement_signatures) & signature_ids)
    pattern_match = 1 if record.architecture_pattern_id in pattern_ids else 0
    return obligation_overlap * 3 + signature_overlap * 2 + pattern_match


def find_precedents(
    obligation_ids: set[str], signature_ids: set[str], admissible_pattern_ids: set[str], signal: SignalVector
) -> list[PrecedentFinding]:
    scored = [
        (record, _similarity(record, obligation_ids, signature_ids, admissible_pattern_ids))
        for record in load_solution_registry()
    ]
    scored = [pair for pair in scored if pair[1] > 0]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    findings: list[PrecedentFinding] = []
    for record, score in scored[:_MAX_FINDINGS]:
        divergent_obligations = sorted(obligation_ids - set(record.obligation_profile))
        missing_here = sorted(set(record.obligation_profile) - obligation_ids)
        divergences = []
        if divergent_obligations:
            divergences.append(f"Current problem carries obligation(s) this precedent did not: {', '.join(divergent_obligations)}.")
        if missing_here:
            divergences.append(f"This precedent carried obligation(s) not present here: {', '.join(missing_here)}.")
        if record.industry.lower() != signal.industry.lower():
            divergences.append(f"Different industry context ({record.industry} vs {signal.industry}).")

        usage = _usage_for_evidence_class(record.evidence_class)
        transferable = usage == "transferable_decision_evidence" and not divergent_obligations

        similarity_basis = []
        if set(record.obligation_profile) & obligation_ids:
            similarity_basis.append("obligation profile")
        if set(record.requirement_signatures) & signature_ids:
            similarity_basis.append("requirement signatures")
        if record.architecture_pattern_id in admissible_pattern_ids:
            similarity_basis.append("solution pattern")

        findings.append(
            PrecedentFinding(
                solution_id=record.id,
                title=record.title,
                evidence_class=record.evidence_class,
                similarity_basis=similarity_basis,
                transferable=transferable,
                conditions=record.conditions,
                divergences=divergences or ["No material divergence identified against the current requirement/obligation set."],
                lesson_summary=record.lessons_learned[0] if record.lessons_learned else "",
                usage=usage,
            )
        )
    return findings
