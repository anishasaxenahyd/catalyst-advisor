"""Stage 8: Pattern Admissibility Analysis — and the second wave of Stage 7
(Capability Requirement Derivation) that only exists once patterns have a
verdict.

Evaluates every pattern in the library against the Requirement Set — never
a retrieved subset (Part 6.1: "the library is small enough that you
evaluate all of it — no retrieval, no recall risk"). Contra-indications are
checked before indications, since disqualification is cheaper and safer
than qualification (Part 6.1, question order).

This is the module that replaces `app.engine.matcher` + the weighted
`technical_fit` dimension in `app.engine.scoring` — contract evaluation
over a closed signature vocabulary, not tag-overlap scoring.
"""

from app.kernel.humanize import capability_label, join_labels, signature_label, signature_labels
from app.kernel.loaders import get_capability_ids, get_pattern_by_id, get_patterns
from app.kernel.schemas import CapabilityRequirement, PatternRecord, PatternVerdict, PatternVerdictEntry


def _solution_pattern_verdict(pattern: PatternRecord, signature_ids: set[str]) -> tuple[PatternVerdict, str, list[str], list[str]]:
    matched_contra = sorted(set(pattern.contra_indications) & signature_ids)
    if matched_contra:
        return (
            "CONTRA_INDICATED",
            f"Doesn't fit because: {join_labels(signature_labels(matched_contra))}.",
            [],
            matched_contra,
        )

    matched_indications = sorted(set(pattern.indications) & signature_ids)

    if "ACTION_REQUIRED_DEFERRED" in signature_ids and "ACTION_REQUIRED" in pattern.indications:
        return (
            "CONDITIONAL",
            "The requester wants this later, not now — not needed in the first release, but worth "
            "designing the interface so it can be added without a rework.",
            matched_indications,
            [],
        )

    if matched_indications:
        return (
            "REQUIRED",
            f"Needed because: {join_labels(signature_labels(matched_indications))}.",
            matched_indications,
            [],
        )

    trigger_note = f" Would apply if: {pattern.escalation_trigger}" if pattern.escalation_trigger else ""
    return (
        "UNNECESSARY",
        f"Nothing in this request calls for it.{trigger_note}",
        [],
        [],
    )


def _assurance_pattern_verdict(pattern: PatternRecord, mandatory_capability_ids: set[str]) -> tuple[PatternVerdict, str]:
    matched = sorted(set(pattern.fulfills_capabilities) & mandatory_capability_ids)
    if matched:
        return "REQUIRED", f"Required by policy: {join_labels([capability_label(c) for c in matched])}."
    return "UNNECESSARY", "No policy currently requires this for the request as described."


def _apply_subsumption(verdicts: list[PatternVerdictEntry]) -> None:
    """A pattern REQUIRED and subsumed by another REQUIRED pattern demotes
    to APPLICABLE — listing both is a modelling error (Part 6.2)."""
    by_id = {v.pattern_id: v for v in verdicts}
    for entry in verdicts:
        if entry.verdict != "REQUIRED":
            continue
        pattern = get_pattern_by_id().get(entry.pattern_id)
        if not pattern:
            continue
        for subsumed_id in pattern.composition.get("subsumes", []):
            subsumed = by_id.get(subsumed_id)
            if subsumed and subsumed.verdict == "REQUIRED":
                subsumed.verdict = "APPLICABLE"
                subsumed.reason = f"Subsumed by '{entry.pattern_name}', which already provides this pattern's capability at a higher tier."


def evaluate_patterns(
    signature_ids: set[str], mandatory_capability_ids: set[str]
) -> tuple[list[PatternVerdictEntry], list[CapabilityRequirement]]:
    known_caps = get_capability_ids()
    verdicts: list[PatternVerdictEntry] = []

    for pattern in get_patterns():
        if pattern.pattern_type == "assurance":
            verdict, reason = _assurance_pattern_verdict(pattern, mandatory_capability_ids)
            matched_ind: list[str] = []
            matched_contra: list[str] = []
        else:
            verdict, reason, matched_ind, matched_contra = _solution_pattern_verdict(pattern, signature_ids)

        verdicts.append(
            PatternVerdictEntry(
                pattern_id=pattern.id,
                pattern_name=pattern.name,
                pattern_type=pattern.pattern_type,
                verdict=verdict,
                reason=reason,
                matched_indications=matched_ind,
                matched_contra_indications=matched_contra,
            )
        )

    _apply_subsumption(verdicts)

    capability_requirements: dict[str, CapabilityRequirement] = {}
    for entry in verdicts:
        if entry.verdict not in ("REQUIRED", "CONDITIONAL"):
            continue
        pattern = get_pattern_by_id()[entry.pattern_id]
        status = "mandatory" if entry.verdict == "REQUIRED" else "deferred"
        for cap_id in pattern.required_capabilities:
            if cap_id not in known_caps:
                continue
            if cap_id in capability_requirements:
                capability_requirements[cap_id].derived_from.append(entry.pattern_id)
                continue
            capability_requirements[cap_id] = CapabilityRequirement(
                id=cap_id, name=capability_label(cap_id), status=status, derived_from=[entry.pattern_id]
            )

    return verdicts, list(capability_requirements.values())
