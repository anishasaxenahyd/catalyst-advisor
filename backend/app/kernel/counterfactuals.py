"""Counterfactual explanation (Part 10.4) — "what would change this
recommendation?" Computed by inspecting the decided verdicts and
obligations directly, not asked of the LLM: the answer is a structural fact
about the Decision Kernel's own output, not a judgement call, so it stays
deterministic like the rest of the load-bearing stages.
"""

from app.kernel.loaders import get_pattern_by_id
from app.kernel.schemas import ObligationInstance, PatternVerdictEntry


def compute_counterfactuals(
    verdicts: list[PatternVerdictEntry], obligations: list[ObligationInstance]
) -> list[str]:
    counterfactuals: list[str] = []
    by_id = get_pattern_by_id()

    unnecessary = [v for v in verdicts if v.verdict == "UNNECESSARY" and v.pattern_type == "solution"]
    for entry in unnecessary[:2]:
        pattern = by_id.get(entry.pattern_id)
        if pattern and pattern.escalation_trigger:
            counterfactuals.append(f"{pattern.escalation_trigger.rstrip('.')} — currently absent, which is why '{pattern.name}' is not part of the recommendation.")

    contra = [v for v in verdicts if v.verdict == "CONTRA_INDICATED"]
    for entry in contra[:1]:
        counterfactuals.append(
            f"If {', '.join(entry.matched_contra_indications)} were not present, '{entry.pattern_name}' would become admissible for reconsideration."
        )

    phi_obligation = next((o for o in obligations if o.id == "OBL-PHI-BOUNDARY"), None)
    if phi_obligation:
        counterfactuals.append(
            "If PHI were confirmed absent, the PHI-approved processing boundary and PHI-safe logging obligations would "
            "no longer apply, widening the set of viable catalog and vendor options."
        )

    conditional = [v for v in verdicts if v.verdict == "CONDITIONAL"]
    for entry in conditional[:1]:
        counterfactuals.append(
            f"If the deferred capability behind '{entry.pattern_name}' were needed immediately rather than in a later "
            f"increment, see the Target State alternative below."
        )

    return counterfactuals[:4]
