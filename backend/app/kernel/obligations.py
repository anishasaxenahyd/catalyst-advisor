"""Stage 5: Obligation Resolution — Policy & Constraint Plane, Class A only.

Fully deterministic rule evaluation over `data/policy/obligations.json`.
No LLM: this is the plane whose failure mode is a compliance breach, not a
weaker recommendation, so it gets deterministic rule evaluation, not
retrieval or interpretation (Part 1, Plane 3).

Deliberately runs *before* solution class and pattern admissibility — an
obligation like "PHI present" doesn't just constrain a chosen architecture,
it disqualifies patterns and mandates capabilities before any architecture
is drawn (Part 3, Stage 5's "why this sits here" note).
"""

from app.kernel.loaders import get_obligation_rules
from app.kernel.schemas import ObligationCondition, ObligationInstance
from app.models.schemas import SignalVector


def _condition_holds(condition: ObligationCondition, signal: SignalVector, signature_ids: set[str]) -> bool:
    if condition.field == "always":
        return bool(condition.value)
    if condition.field == "signatures":
        return condition.value in signature_ids if condition.op == "contains" else False
    value = getattr(signal, condition.field, None)
    if condition.op == "equals":
        return value == condition.value
    if condition.op == "in":
        return value in condition.value
    if condition.op == "contains":
        return isinstance(value, list) and condition.value in value
    return False


def resolve_obligations(signal: SignalVector, signature_ids: set[str]) -> list[ObligationInstance]:
    resolved: list[ObligationInstance] = []
    for rule in get_obligation_rules():
        checks = [_condition_holds(c, signal, signature_ids) for c in rule.conditions]
        fired = any(checks) if rule.match == "any" else all(checks)
        if not fired:
            continue
        resolved.append(
            ObligationInstance(
                id=rule.id,
                title=rule.title,
                source=rule.source,
                mandates_capabilities=rule.mandates_capabilities,
                rationale=rule.description,
            )
        )
    return resolved
