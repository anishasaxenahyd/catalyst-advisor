"""Stage 15: Evidence Validation & Assembly.

Fully deterministic grounding validator, no LLM. Every ID referenced
anywhere in the `KernelResult` must resolve against the registry it claims
to come from — an unresolvable reference is a hard failure, not a warning
(Part 3, Stage 15). This is the mechanism (structure, not prompting) that
makes it impossible for the LLM-authored narration stage to have invented a
pattern, asset, obligation, or precedent: by the time narration runs, every
ID it's allowed to mention has already been validated to exist.
"""

from app.kernel.loaders import get_obligation_by_id, get_pattern_by_id
from app.kernel.schemas import KernelResult
from app.solution_registry.factory import load_solution_registry


class KernelValidationError(Exception):
    pass


def validate(result: KernelResult, known_asset_ids: set[str]) -> None:
    errors: list[str] = []
    patterns = get_pattern_by_id()
    obligations = get_obligation_by_id()
    solution_ids = {s.id for s in load_solution_registry()}

    for entry in result.pattern_verdicts:
        if entry.pattern_id not in patterns:
            errors.append(f"Pattern verdict references unknown pattern '{entry.pattern_id}'.")

    for candidate in result.candidates:
        for pid in candidate.pattern_ids:
            if pid not in patterns:
                errors.append(f"Candidate '{candidate.id}' references unknown pattern '{pid}'.")

    for obligation in result.obligations:
        if obligation.id not in obligations:
            errors.append(f"Obligation instance references unknown obligation rule '{obligation.id}'.")

    for resolution in result.asset_resolutions:
        if resolution.asset_id and resolution.asset_id not in known_asset_ids:
            errors.append(f"Asset resolution for '{resolution.capability_id}' references unknown asset '{resolution.asset_id}'.")

    for finding in result.precedent_findings:
        if finding.solution_id not in solution_ids:
            errors.append(f"Precedent finding references unknown solution '{finding.solution_id}'.")

    if errors:
        raise KernelValidationError("; ".join(errors))
