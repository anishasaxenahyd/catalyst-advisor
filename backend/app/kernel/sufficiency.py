"""Stage 4: Sufficiency Gate.

Deterministic — never delegated to the LLM ("do you have enough information?"
asked of a model will nearly always say yes). A defaulted field only blocks
if guessing it would plausibly change the recommendation; the criticality
table below is a small, explicit, hand-authored judgement call (the same
kind of call the design doc's own worked example makes for "does the
assistant read personal enrolment data"), not a computed score.

The kernel never hard-stops the pipeline on HALT_CLARIFY — there is no
session/persistence layer yet to pause and resume against (see the
Interaction Plane guidance in the architecture doc). Instead it produces a
provisional recommendation and surfaces the blocking question prominently,
exactly as the design doc's own Stage 4 example does ("proceeding on the
general-plan-documents reading... with personal-data access marked as a
defined evolution step").
"""

from app.kernel.schemas import Clarification, SufficiencyOutcome
from app.models.schemas import SignalVector

# field -> (is decision-critical when defaulted, blocking question)
_CRITICALITY: dict[str, tuple[bool, str]] = {
    "data_sensitivity": (
        True,
        "Does this involve PII or PHI data? This determines the entire obligation set (compliance boundary, "
        "logging, per-user authorisation) and cannot be safely assumed.",
    ),
    "automation_level": (
        True,
        "Should this assist a human, draft for review, or act autonomously on systems of record? This changes "
        "which patterns are admissible and whether an approval workflow is required.",
    ),
    "latency_requirement": (
        True,
        "Does this need to respond in real time, or can it run in scheduled batches? This determines the "
        "interaction pattern family.",
    ),
    "expected_scale": (False, "Is this a pilot, a department-wide rollout, or an enterprise-wide rollout?"),
    "data_modality": (False, "What's the primary data type — text, images, or structured/tabular data?"),
    "industry": (False, "What industry or business domain is this for?"),
}


def evaluate_sufficiency(signal: SignalVector) -> SufficiencyOutcome:
    blocking: list[Clarification] = []
    advisory: list[Clarification] = []

    for field, (is_critical, question) in _CRITICALITY.items():
        if signal.field_provenance.get(field) != "default":
            continue
        clarification = Clarification(field_or_signature=field, question=question, decision_critical=is_critical)
        (blocking if is_critical else advisory).append(clarification)

    if any(c.field_or_signature == "data_sensitivity" for c in blocking):
        status = "HALT_CLARIFY"
        rationale = (
            "Data sensitivity is unknown and governs the entire obligation set. Proceeding on the "
            "least-sensitive assumption (data_sensitivity=none) below, provisionally — confirm before build."
        )
    elif blocking:
        status = "PROCEED_WITH_QUESTIONS"
        rationale = f"{len(blocking)} decision-critical field(s) were defaulted; recommendation below is provisional on them."
    else:
        status = "PROCEED"
        rationale = "No decision-critical fields were left to default."

    return SufficiencyOutcome(status=status, blocking_questions=blocking, advisory_questions=advisory, rationale=rationale)
