"""Stage 12: Candidate Architecture Construction.

Templated composition, not free-form LLM generation, per the design doc's
own MVP guidance (Part 15.15 Phase 2): construct from the already-decided
pattern verdicts rather than asking a model to invent a topology. A
structural validator would reject an incoherent candidate before it's
shown to anyone (Part 6.2) — for this prototype the constructor itself
only ever proposes coherent, already-validated compositions (REQUIRED
patterns plus their declared `composes_with` assurance layer), so there is
nothing left for a separate validator to catch yet; that becomes necessary
once candidate construction stops being templated.

Produces up to three candidates:
  * CAND-BASE — minimum sufficient: every REQUIRED pattern, nothing else.
    Always survives elimination by construction.
  * CAND-ESCALATED — CAND-BASE plus one pattern one rung up an escalation
    ladder whose trigger is *not* present in the Requirement Set. Exists
    specifically to be eliminated at Stage 13 by the complexity budget —
    this is how "this pattern is unnecessary" becomes a first-class,
    demonstrable rejection rather than just a Stage 8 verdict.
  * CAND-DEFERRED-FORWARD — CAND-BASE plus whatever Stage 8 marked
    CONDITIONAL (deferred capability brought forward). Only constructed
    when a CONDITIONAL verdict exists; becomes an Alternative at Stage 14,
    never eliminated.
"""

from app.kernel.loaders import get_pattern_by_id
from app.kernel.schemas import Candidate, PatternVerdictEntry


def _complexity(pattern_ids: list[str]) -> int:
    by_id = get_pattern_by_id()
    return sum(by_id[pid].complexity_tier for pid in pattern_ids if pid in by_id and by_id[pid].pattern_type == "solution")


def construct_candidates(verdicts: list[PatternVerdictEntry]) -> list[Candidate]:
    by_id = get_pattern_by_id()
    required_ids = [v.pattern_id for v in verdicts if v.verdict == "REQUIRED"]
    conditional_ids = [v.pattern_id for v in verdicts if v.verdict == "CONDITIONAL"]
    unnecessary_solution_ids = {v.pattern_id for v in verdicts if v.verdict == "UNNECESSARY" and v.pattern_type == "solution"}

    candidates: list[Candidate] = []

    base = Candidate(
        id="CAND-BASE",
        label="Minimum sufficient — recommended baseline",
        description="Every pattern with a REQUIRED verdict; nothing included that the Requirement Set doesn't justify.",
        pattern_ids=required_ids,
        complexity_score=_complexity(required_ids),
    )
    candidates.append(base)

    escalation_pattern_id = None
    for pid in required_ids:
        pattern = by_id.get(pid)
        if not pattern:
            continue
        for escalated_id in pattern.composition.get("escalates_to", []):
            if escalated_id in unnecessary_solution_ids:
                escalation_pattern_id = escalated_id
                break
        if escalation_pattern_id:
            break

    if escalation_pattern_id:
        escalated_ids = [*required_ids, escalation_pattern_id]
        candidates.append(
            Candidate(
                id="CAND-ESCALATED",
                label=f"Escalated — adds {by_id[escalation_pattern_id].name}",
                description=f"CAND-BASE plus '{by_id[escalation_pattern_id].name}', one rung up the escalation ladder. "
                f"Its trigger signature is not present in the Requirement Set — constructed to demonstrate the "
                f"complexity-budget elimination gate.",
                pattern_ids=escalated_ids,
                complexity_score=_complexity(escalated_ids),
            )
        )

    if conditional_ids:
        deferred_ids = [*required_ids, *conditional_ids]
        names = ", ".join(by_id[pid].name for pid in conditional_ids if pid in by_id)
        candidates.append(
            Candidate(
                id="CAND-DEFERRED-FORWARD",
                label=f"Target state — {names} brought forward",
                description=f"CAND-BASE plus the capability currently marked deferred ({names}), built into the "
                f"first release instead of a later increment.",
                pattern_ids=deferred_ids,
                complexity_score=_complexity(deferred_ids),
            )
        )

    return candidates
