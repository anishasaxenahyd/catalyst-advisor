"""Turns closed-vocabulary IDs (SCREAMING_SNAKE_CASE signatures, CAP-KEBAB-CASE
capabilities) into short human-readable phrases for anything that reaches a
report or UI. The IDs themselves stay canonical everywhere else in the
kernel — evaluation, matching, and the evidence chain all still key off
`ENTERPRISE_PRIVATE_DATA` / `CAP-RETRIEVAL-PERMISSION-AWARE` unchanged. This
module is the one place that translates them for display, so a reader never
sees a raw identifier in prose.
"""

from app.kernel.loaders import get_capability_by_id, get_signature_by_id


def _title_case_id(raw_id: str, strip_prefix: str = "") -> str:
    text = raw_id
    if strip_prefix and text.startswith(strip_prefix):
        text = text[len(strip_prefix):]
    words = text.replace("_", " ").replace("-", " ").strip().split()
    return " ".join(words).capitalize()


def signature_label(signature_id: str) -> str:
    definition = get_signature_by_id().get(signature_id)
    if definition and definition.label:
        return definition.label
    return _title_case_id(signature_id)


def signature_labels(signature_ids: list[str]) -> list[str]:
    return [signature_label(s) for s in signature_ids]


def capability_label(capability_id: str) -> str:
    definition = get_capability_by_id().get(capability_id)
    if definition and definition.name:
        return definition.name
    return _title_case_id(capability_id, strip_prefix="CAP-")


def join_labels(labels: list[str]) -> str:
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + " and " + labels[-1]
