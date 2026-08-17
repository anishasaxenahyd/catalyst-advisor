"""Stage 6: Solution Class Determination.

Deterministic classification against the closed solution-class vocabulary
(`data/taxonomy/solution_classes.json`) by indicative-signature overlap.
The design doc treats this stage as hybrid (LLM proposes, rules validate);
this prototype keeps it fully rule-based to hold the LLM surface to the two
calls in `providers/llm/base.py` — an LLM-authored justification for *why*
this class fits can be layered on top at the narration stage without
changing which class wins, since the class itself must stay reproducible.
"""

from app.kernel.loaders import get_solution_classes
from app.kernel.schemas import SolutionClassDef


def determine_solution_class(signature_ids: set[str]) -> tuple[SolutionClassDef, list[tuple[SolutionClassDef, int]]]:
    ranked = sorted(
        ((cls, len(set(cls.indicative_signatures) & signature_ids)) for cls in get_solution_classes()),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return ranked[0][0], ranked
