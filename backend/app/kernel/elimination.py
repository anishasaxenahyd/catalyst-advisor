"""Stage 13: Elimination.

Fully deterministic — no LLM call anywhere in this module, on purpose. This
is the stage most susceptible to plausible-sounding rationalisation if a
model were allowed near it (Part 3, Stage 13), and it is the stage that
makes the Advisor read like an architect rather than a generator: every
elimination is shown to the user with a rule ID and evidence, never hidden.
"""

from app.kernel.schemas import Candidate, EliminationEntry

_ESCALATED_RULE = "CPX-BUDGET-01"
_CAPABILITY_GAP_RULE = "CAP-GAP-01"


def eliminate(candidates: list[Candidate]) -> tuple[list[Candidate], list[EliminationEntry]]:
    survivors: list[Candidate] = []
    eliminations: list[EliminationEntry] = []

    for candidate in candidates:
        if not candidate.covers_all_mandatory_capabilities:
            eliminations.append(
                EliminationEntry(
                    candidate_id=candidate.id,
                    candidate_label=candidate.label,
                    gate="mandatory capability unsourced",
                    rule_id=_CAPABILITY_GAP_RULE,
                    evidence=f"Uncovered mandatory capability requirement(s): {', '.join(candidate.uncovered_capabilities)}.",
                )
            )
            continue

        if candidate.id == "CAND-ESCALATED":
            eliminations.append(
                EliminationEntry(
                    candidate_id=candidate.id,
                    candidate_label=candidate.label,
                    gate="complexity budget",
                    rule_id=_ESCALATED_RULE,
                    evidence=f"{candidate.description} No requirement signature justifies the added pattern; burden of proof sits on complexity.",
                )
            )
            continue

        survivors.append(candidate)

    return survivors, eliminations
