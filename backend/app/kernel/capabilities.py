"""Stage 7: Capability Requirement Derivation (obligation-derived half).

Obligations mandate capabilities before any pattern has been chosen — this
is deliberately upstream of pattern admissibility (Stage 8), which adds a
second wave of capability requirements from whichever patterns get a
REQUIRED/APPLICABLE verdict. Both waves land in the same closed vocabulary
(`data/taxonomy/capabilities.json`), which is the only thing Knowledge and
Catalog have in common (Part 7.1) — this function only ever emits IDs from
that vocabulary, silently dropping anything else, so a typo in an
obligation's `mandates_capabilities` fails closed rather than inventing a
capability nothing can resolve.
"""

from app.kernel.loaders import get_capability_ids
from app.kernel.schemas import CapabilityRequirement, ObligationInstance


def derive_from_obligations(obligations: list[ObligationInstance]) -> list[CapabilityRequirement]:
    known = get_capability_ids()
    requirements: dict[str, CapabilityRequirement] = {}
    for obligation in obligations:
        for cap_id in obligation.mandates_capabilities:
            if cap_id not in known:
                continue
            if cap_id in requirements:
                requirements[cap_id].derived_from.append(obligation.id)
                continue
            requirements[cap_id] = CapabilityRequirement(
                id=cap_id, name=cap_id, status="mandatory", derived_from=[obligation.id]
            )
    return list(requirements.values())
