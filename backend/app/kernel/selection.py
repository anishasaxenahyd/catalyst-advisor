"""Stage 14: Differentiation & Selection.

Default priority (declared explicitly so it can be challenged, per Part 3
Stage 14): satisfy all obligations, then minimise complexity, then
maximise reuse, then minimise time-to-first-production-value. Survivors of
elimination already satisfy all obligations by construction, so the
tie-breaker here is the complexity budget — the lowest-complexity survivor
wins outright; no scores are combined or weighted.
"""

from app.kernel.schemas import Alternative, Candidate

DEFAULT_PRIORITY = "satisfy all obligations, then minimise complexity, then maximise reuse, then minimise time-to-first-production-value"


def select(survivors: list[Candidate]) -> tuple[Candidate, list[Alternative]]:
    ranked = sorted(survivors, key=lambda c: c.complexity_score)
    recommended = ranked[0]
    alternatives: list[Alternative] = []

    for candidate in ranked[1:]:
        if candidate.id == "CAND-DEFERRED-FORWARD":
            alternatives.append(
                Alternative(
                    candidate_id=candidate.id,
                    label=candidate.label,
                    governing_priority="Choose this if the deferred capability is needed within the next couple of quarters, "
                    "not just eventually.",
                    what_is_given_up="A longer initial timeline and a broader obligation/compliance review scope pulled forward.",
                    switching_cost="Low if the recommended baseline's interface is designed with this seam in mind now; "
                    "high if the seam is bolted on after launch.",
                    revisit_trigger="A committed business date for the deferred capability, or evidence the baseline's "
                    "manual workaround isn't scaling.",
                )
            )
        else:
            alternatives.append(
                Alternative(
                    candidate_id=candidate.id,
                    label=candidate.label,
                    governing_priority="A surviving, obligation-compliant option with a different complexity/reuse trade-off.",
                    what_is_given_up="Lower complexity of the recommended baseline.",
                    switching_cost="Depends on the specific pattern delta — see the sourcing decisions for the affected capabilities.",
                    revisit_trigger="The baseline proves insufficient against a mandatory requirement in practice.",
                )
            )

    return recommended, alternatives
